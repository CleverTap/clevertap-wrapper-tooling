#!/usr/bin/env python3
"""
expo_diff.py — the deterministic "fact finder" for the CleverTap Expo plugin sync.

Unlike diff_native_api.py (which diffs native *method surface*), the Expo plugin
surfaces ZERO SDK methods. It is a config plugin that pins dependency versions and
generates native setup. So this tool answers a different question:

    "Given a target clevertap-react-native version (and a target Expo SDK version),
     what version numbers and build-config does the plugin need to change?"

It does, in one invocation:
    1. CHAIN  — read what the target clevertap-react-native release requires:
                its android/build.gradle pins the CleverTap Android SDK version,
                its .podspec pins the CleverTap iOS SDK version.
    2. ANDROID CATALOG DIFF — parse gradle/libs.versions.toml (with tomllib, a real
                parser) at the plugin's CURRENT core version vs the resolved TARGET
                core version; diff every [versions] entry.
    3. ANDROID DEP DIFF — diff the clevertap-core (and pt/hms) build.gradle
                dependencies{} blocks, separating compileOnly (host must provide →
                plugin change) from implementation (transitive → no plugin change).
    4. iOS DIFF — diff the CleverTap-iOS-SDK podspec deployment target + deps.
    5. DISCOVERY — parse the plugin's OWN files (constants.ts, android/build.gradle,
                the classpath .ts, IOSConstants.ts) to learn what it actually pins,
                then name-match against the catalog. This replaces a hand-maintained
                mapping table. Emits mapped / catalog_only / plugin_only.
    6. CHANGELOGS — pull verbatim changelog blocks (RN, Android core/pt/hms,
                intermediates). Expo's changelog is HTML → emitted as
                "webfetch_needed" for the brain (which has WebFetch) to read.

Reliability (this output is treated as ground truth by the sync brain):
    - tomllib for catalogs (not fuzzy text matching).
    - FAILS LOUD: a 404, parse failure, or ambiguous match goes into warnings[]
      and forces a non-zero exit. It NEVER invents a version number.
    - Dumps every raw file it fetched under <cache>/raw/ so a human (and the brain)
      can verify what it actually read.
    - Robust tag resolution: lists tags via the GitHub API and substring-matches so
      combined tags like `corev7.6.0_ptv2.2.0` resolve correctly.

Stdlib-only. Requires Python >= 3.11 (tomllib).

Usage:
    expo_diff.py \
      --rn-version 4.1.0 \
      --expo-sdk-version 56 \
      --plugin-path /path/to/clevertap-expo-plugin \
      [--rn-current 4.0.0] \
      [--out-dir ~/.cache/clevertap-expo-diff] \
      [--cache-dir ~/.cache/clevertap-sdk-versions] \
      [--github-token <token>] [--no-cache]

Output: <out-dir>/<rn>-expo<expo>/expo-diff.json  (+ raw fetched files under <cache>/raw/)
"""

import argparse
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────── Configuration ─────────────────────────────

REPOS = {
    "rn":          ("CleverTap/clevertap-react-native", "{ver}"),       # bare tag, master branch
    "android_core":("CleverTap/clevertap-android-sdk",  "corev{ver}"),
    "android_pt":  ("CleverTap/clevertap-android-sdk",  "ptv{ver}"),
    "android_hms": ("CleverTap/clevertap-android-sdk",  "hmsv{ver}"),
    "ios_core":    ("CleverTap/clevertap-ios-sdk",      "{ver}"),
}

# How clevertap-react-native declares the native SDK versions it requires.
RN_ANDROID_GRADLE = "android/build.gradle"
RN_ANDROID_PIN_RE = re.compile(r"clevertap-android-sdk:([0-9][0-9.]*)")
RN_PODSPEC        = "clevertap-react-native.podspec"
RN_IOS_PIN_RE     = re.compile(r"CleverTap-iOS-SDK['\"]\s*,\s*['\"]([0-9][0-9.]*)['\"]")
RN_CHANGELOG      = "CHANGELOG.md"

# CleverTap Android SDK build files (relative to repo root, fetched at a tag).
ANDROID_CATALOG       = "gradle/libs.versions.toml"
ANDROID_CORE_GRADLE   = "clevertap-core/build.gradle"
ANDROID_PT_GRADLE     = "clevertap-pushtemplates/build.gradle"
ANDROID_HMS_GRADLE    = "clevertap-hms/build.gradle"
ANDROID_CORE_CHANGELOG = "docs/CTCORECHANGELOG.md"
ANDROID_PT_CHANGELOG   = "docs/CTPUSHTEMPLATESCHANGELOG.md"
ANDROID_HMS_CHANGELOG  = "docs/CTHUAWEIPUSHCHANGELOG.md"

# Catalog keys that map to the plugin's push-templates / hms pins (so we can resolve
# the aligned pt/hms target versions deterministically from the catalog at the core tag).
CATALOG_KEY_CORE = "clevertap_android_sdk"
CATALOG_KEY_PT   = "clevertap_push_templates_sdk"
CATALOG_KEY_HMS  = "clevertap_hms_sdk"

# CleverTap iOS SDK podspec (at a tag).
IOS_PODSPEC = "CleverTap-iOS-SDK.podspec"
IOS_CHANGELOG = "CHANGELOG.md"  # clevertap-ios-sdk repo root; same '### [Version X.Y.Z]' format as Android

# Expo changelog sources (HTML at expo.dev + markdown on GitHub). NOT parsed here —
# handed to the brain's WebFetch.
EXPO_CHANGELOG_WEB = "https://expo.dev/changelog/sdk-{ver}"
EXPO_CHANGELOG_GH  = "https://raw.githubusercontent.com/expo/expo/main/CHANGELOG.md"

# Plugin files we parse to discover its current pins (relative to --plugin-path).
PLUGIN_CONSTANTS     = "src/android_config/utility/constants.ts"
PLUGIN_DEPS_TEMPLATE = "src/android_config/utility/androidAppDepsTemplate.ts"
PLUGIN_ANDROID_GRADLE = "android/build.gradle"
PLUGIN_CLASSPATH_TS  = "src/android_config/gradle/withCleverTapAndroidAppRootBuildGradle.ts"
PLUGIN_IOS_CONSTANTS = "src/iOS_config/IOSConstants.ts"
PLUGIN_README        = "README.md"
PLUGIN_PACKAGE_JSON  = "package.json"

DEFAULT_OUT_DIR   = Path.home() / ".cache" / "clevertap-expo-diff"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "clevertap-sdk-versions"

RAW_URL = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"
TAGS_API = "https://api.github.com/repos/{repo}/tags?per_page=100"


# ─────────────────────────── State / fail-loud ─────────────────────────

class Finder:
    """Holds shared state: warnings, the raw-dump dir, and the GitHub token."""

    def __init__(self, cache_dir: Path, github_token: Optional[str], no_cache: bool):
        self.cache_dir = cache_dir
        self.raw_dir = cache_dir / "raw"
        self.token = github_token
        self.no_cache = no_cache
        self.warnings: List[str] = []
        self._tags_cache: Dict[str, List[str]] = {}
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"[expo-diff] ⚠️  {msg}", file=sys.stderr)

    # ── network ──
    def _request(self, url: str) -> bytes:
        req = urllib.request.Request(url)
        if self.token and ("api.github.com" in url or "raw.githubusercontent.com" in url):
            req.add_header("Authorization", f"token {self.token}")
        req.add_header("User-Agent", "clevertap-expo-diff")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()

    def fetch_raw(self, repo: str, ref: str, path: str) -> Optional[str]:
        """Fetch a single file at a ref. Returns text or None (and warns) on 404.

        Caches the fetched bytes under <cache>/raw/<repo>/<ref>/<path> for inspection.
        """
        safe = self.raw_dir / repo.replace("/", "_") / ref.replace("/", "_") / path
        if safe.exists() and not self.no_cache:
            return safe.read_text(encoding="utf-8", errors="replace")
        url = RAW_URL.format(repo=repo, ref=ref, path=path)
        try:
            data = self._request(url)
        except urllib.error.HTTPError as e:
            self.warn(f"could not fetch {path} from {repo}@{ref} (HTTP {e.code}) — {url}")
            return None
        except (urllib.error.URLError, TimeoutError) as e:
            self.warn(f"network error fetching {url}: {e}")
            return None
        safe.parent.mkdir(parents=True, exist_ok=True)
        safe.write_bytes(data)
        return data.decode("utf-8", errors="replace")

    def list_tags(self, repo: str) -> List[str]:
        if repo in self._tags_cache:
            return self._tags_cache[repo]
        tags: List[str] = []
        try:
            data = self._request(TAGS_API.format(repo=repo))
            tags = [t["name"] for t in json.loads(data)]
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, KeyError) as e:
            self.warn(f"could not list tags for {repo}: {e}")
        self._tags_cache[repo] = tags
        return tags

    def resolve_tag(self, kind: str, version: str) -> Optional[str]:
        """Resolve the real git tag for a (kind, version).

        Handles combined tags like `corev7.6.0_ptv2.2.0`: the formatted candidate
        (`corev7.6.0`) may not exist verbatim, so we substring-match against the
        live tag list. Returns None (and warns) if nothing matches.
        """
        repo, fmt = REPOS[kind]
        candidate = fmt.format(ver=version)
        tags = self.list_tags(repo)
        if not tags:
            # No tag list (API failure). Optimistically try the formatted candidate;
            # fetch_raw will warn if it 404s.
            return candidate
        if candidate in tags:
            return candidate
        # bare-version tag (iOS / RN) exact match already handled above; for prefixed
        # tags, substring-match the `corev{ver}` / `ptv{ver}` / `hmsv{ver}` token.
        matches = [t for t in tags if candidate in t]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            # Prefer the shortest (least combined) — but flag the ambiguity.
            best = min(matches, key=len)
            self.warn(f"multiple tags match {candidate} in {repo}: {matches}; using {best}")
            return best
        self.warn(f"no tag matches {candidate} in {repo} (looked at {len(tags)} tags)")
        return None


# ─────────────────────────── Version helpers ───────────────────────────

def parse_version(s: str) -> Tuple[int, ...]:
    parts = re.findall(r"\d+", s or "")
    return tuple(int(p) for p in parts) if parts else (0,)


# ─────────────────────────── Plugin discovery ──────────────────────────

def _read_plugin_file(plugin: Path, rel: str, finder: Finder) -> Optional[str]:
    p = plugin / rel
    if not p.exists():
        finder.warn(f"plugin file not found: {rel}")
        return None
    return p.read_text(encoding="utf-8", errors="replace")


def discover_plugin_pins(plugin: Path, finder: Finder) -> Dict[str, Any]:
    """Parse the plugin's own files to learn every version it pins."""
    out: Dict[str, Any] = {
        "android_versions": {},   # versionKey -> version (from CLEVERTAP_DEPENDENCIES_DEFAULT_VERSIONS)
        "coordinate_map": {},     # versionKey -> [maven coordinates] (from the deps template)
        "compile_only": {},       # coordinate -> version (from android/build.gradle)
        "classpaths": {},         # name -> {coord, version}
        "ios_deployment_target": None,
        "rn_current": None,
        "plugin_version": None,
        "expo_devdep": None,
    }

    # 1. constants.ts — scope to the relevant object blocks only.
    text = _read_plugin_file(plugin, PLUGIN_CONSTANTS, finder)
    keys_map: Dict[str, str] = {}   # KEYS const name -> gradle property string (== version key)
    if text:
        block = _extract_ts_object_block(text, "CLEVERTAP_DEPENDENCIES_DEFAULT_VERSIONS")
        if block is None:
            finder.warn("could not locate CLEVERTAP_DEPENDENCIES_DEFAULT_VERSIONS block in constants.ts")
        else:
            # version values look like  someKey: '8.0.0'  (string values only)
            for key, val in re.findall(r"(\w+)\s*:\s*'([^']+)'", block):
                # skip nested group identifiers (their values are objects, not strings) — the
                # regex only matches string values, so group names like `clevertapCore` are skipped.
                out["android_versions"][key] = val
            if not out["android_versions"]:
                finder.warn("parsed 0 version pins from constants.ts — format may have changed")
        # KEYS map: CONST_NAME -> property string (the property string equals the version key).
        keys_block = _extract_ts_object_block(text, "CLEVERTAP_GRADLE_PROPERTIES_KEYS")
        if keys_block:
            for const, prop in re.findall(r"(\w+)\s*:\s*'([^']+)'", keys_block):
                keys_map[const] = prop

    # 1b. deps template — map each version key to the Maven coordinate(s) it's declared with,
    # so we can match the plugin's pins to the catalog by COORDINATE (unambiguous), not by fuzzy
    # key name (which wrongly equates play-services-ads-identifier with play-services-ads).
    tmpl = _read_plugin_file(plugin, PLUGIN_DEPS_TEMPLATE, finder)
    if tmpl:
        # matches:  "group:artifact:${getVersionProperty(KEYS.SOME_CONST)}"
        for coord, const in re.findall(
            r'"([\w.\-]+:[\w.\-]+):\$\{getVersionProperty\(KEYS\.(\w+)\)\}"', tmpl
        ):
            vkey = keys_map.get(const)
            if vkey:
                out["coordinate_map"].setdefault(vkey, [])
                if coord not in out["coordinate_map"][vkey]:
                    out["coordinate_map"][vkey].append(coord)
        if not out["coordinate_map"]:
            finder.warn("parsed 0 coordinates from androidAppDepsTemplate.ts — matching will degrade to flagged")

    # 2. android/build.gradle — compileOnly coordinates.
    text = _read_plugin_file(plugin, PLUGIN_ANDROID_GRADLE, finder)
    if text:
        for coord, ver in re.findall(r'compileOnly\(?\s*["\']([^"\':]+:[^"\':]+):([^"\']+)["\']', text):
            out["compile_only"][coord] = ver

    # 3. classpath .ts — GOOGLE_SERVICES_CLASSPATH / HMS_CLASSPATH literals.
    text = _read_plugin_file(plugin, PLUGIN_CLASSPATH_TS, finder)
    if text:
        for name, coord, ver in re.findall(
            r'(\w*CLASSPATH)\s*=\s*"([^":]+:[^":]+):([^"]+)"', text
        ):
            out["classpaths"][name] = {"coord": coord, "version": ver}

    # 4. IOSConstants.ts — DEPLOYMENT_TARGET.
    text = _read_plugin_file(plugin, PLUGIN_IOS_CONSTANTS, finder)
    if text:
        m = re.search(r'DEPLOYMENT_TARGET\s*=\s*["\']([\d.]+)["\']', text)
        if m:
            out["ios_deployment_target"] = m.group(1)

    # 5. package.json — plugin version + expo devDep.
    text = _read_plugin_file(plugin, PLUGIN_PACKAGE_JSON, finder)
    if text:
        try:
            pkg = json.loads(text)
            out["plugin_version"] = pkg.get("version")
            out["expo_devdep"] = (pkg.get("devDependencies") or {}).get("expo")
        except ValueError:
            finder.warn("could not parse plugin package.json")

    # 6. README compatibility matrix — last row's clevertap-react-native column (rn_current).
    text = _read_plugin_file(plugin, PLUGIN_README, finder)
    if text:
        out["rn_current"] = _last_matrix_rn_version(text)
        if not out["rn_current"]:
            finder.warn("could not read clevertap-react-native version from README compatibility matrix")

    return out


def _extract_ts_object_block(text: str, identifier: str) -> Optional[str]:
    """Return the `{...}` body assigned to `identifier`, brace-balanced."""
    m = re.search(re.escape(identifier) + r"\s*(?::\s*\w+)?\s*=\s*\{", text)
    if not m:
        return None
    start = m.end() - 1  # at the opening brace
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _last_matrix_rn_version(readme: str) -> Optional[str]:
    """The compat matrix has rows `| plugin | expo | react-native | clevertap-rn |`.
    Return the clevertap-react-native (4th) column of the last data row."""
    rn = None
    for line in readme.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.match(r"^\d+\.\d+\.\d+$", cells[0]):
            rn = cells[3]
    return rn


# ─────────────────────────── Chain resolution ──────────────────────────

def resolve_chain(finder: Finder, rn_version: str) -> Dict[str, Optional[str]]:
    """Read what clevertap-react-native@rn_version requires for native SDKs."""
    repo = REPOS["rn"][0]
    tag = finder.resolve_tag("rn", rn_version)
    result: Dict[str, Optional[str]] = {
        "rn_tag": tag,
        "required_android_core": None,
        "required_ios_core": None,
    }
    if not tag:
        return result
    gradle = finder.fetch_raw(repo, tag, RN_ANDROID_GRADLE)
    if gradle:
        m = RN_ANDROID_PIN_RE.search(gradle)
        if m:
            result["required_android_core"] = m.group(1)
        else:
            finder.warn(f"could not find clevertap-android-sdk pin in RN {RN_ANDROID_GRADLE}@{tag}")
    podspec = finder.fetch_raw(repo, tag, RN_PODSPEC)
    if podspec:
        m = RN_IOS_PIN_RE.search(podspec)
        if m:
            result["required_ios_core"] = m.group(1)
        else:
            finder.warn(f"could not find CleverTap-iOS-SDK pin in RN {RN_PODSPEC}@{tag}")
    return result


# ─────────────────────────── Android catalog + deps ────────────────────

def fetch_catalog(finder: Finder, core_version: str) -> Optional[dict]:
    """Fetch + tomllib-parse libs.versions.toml at the given core tag."""
    repo = REPOS["android_core"][0]
    tag = finder.resolve_tag("android_core", core_version)
    if not tag:
        return None
    text = finder.fetch_raw(repo, tag, ANDROID_CATALOG)
    if text is None:
        return None
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        finder.warn(f"failed to parse libs.versions.toml@{tag}: {e}")
        return None


def diff_catalog_versions(old: Optional[dict], new: Optional[dict]) -> dict:
    o = (old or {}).get("versions", {}) or {}
    n = (new or {}).get("versions", {}) or {}
    added = {k: n[k] for k in sorted(set(n) - set(o))}
    removed = {k: o[k] for k in sorted(set(o) - set(n))}
    changed = {k: {"old": o[k], "new": n[k]} for k in sorted(set(o) & set(n)) if o[k] != n[k]}
    return {"added": added, "removed": removed, "changed": changed}


_GRADLE_DEP_RE = re.compile(
    r"^\s*(api|implementation|compileOnly)\s*\(?\s*"
    r"['\"]([^'\"]+:[^'\"]+)(?::([^'\"]+))?['\"]",
    re.MULTILINE,
)


def fetch_dep_block(finder: Finder, kind: str, version: str, gradle_path: str) -> Optional[Dict[str, Dict[str, str]]]:
    """Fetch a module build.gradle at a tag; return {scope: {coord: version}}."""
    repo = REPOS[kind][0]
    tag = finder.resolve_tag(kind, version)
    if not tag:
        return None
    text = finder.fetch_raw(repo, tag, gradle_path)
    if text is None:
        return None
    out: Dict[str, Dict[str, str]] = {"api": {}, "implementation": {}, "compileOnly": {}}
    for scope, coord, ver in _GRADLE_DEP_RE.findall(text):
        out.setdefault(scope, {})[coord] = ver or ""
    return out


def diff_dep_block(old: Optional[dict], new: Optional[dict]) -> dict:
    old = old or {}
    new = new or {}
    result: Dict[str, Any] = {}
    for scope in ("api", "implementation", "compileOnly"):
        o = old.get(scope, {}) or {}
        n = new.get(scope, {}) or {}
        added = {k: n[k] for k in sorted(set(n) - set(o))}
        removed = {k: o[k] for k in sorted(set(o) - set(n))}
        changed = {k: {"old": o[k], "new": n[k]} for k in sorted(set(o) & set(n)) if o[k] != n[k]}
        if added or removed or changed:
            result[scope] = {"added": added, "removed": removed, "changed": changed}
    return result


# ─────────────────────────── iOS podspec diff ──────────────────────────

_POD_DEPLOY_RE = re.compile(r"s\.(?:ios\.deployment_target|platform\s*=\s*:ios\s*,)\s*['\"]([\d.]+)['\"]")
_POD_DEP_RE = re.compile(r"s\.dependency\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?")


def fetch_ios_podspec(finder: Finder, ios_version: Optional[str]) -> Optional[dict]:
    if not ios_version:
        return None
    repo = REPOS["ios_core"][0]
    tag = finder.resolve_tag("ios_core", ios_version)
    if not tag:
        return None
    text = finder.fetch_raw(repo, tag, IOS_PODSPEC)
    if text is None:
        return None
    deploy = None
    m = _POD_DEPLOY_RE.search(text)
    if m:
        deploy = m.group(1)
    deps = {name: (ver or "") for name, ver in _POD_DEP_RE.findall(text)}
    return {"deployment_target": deploy, "dependencies": deps}


def diff_ios(old: Optional[dict], new: Optional[dict]) -> dict:
    old = old or {}
    new = new or {}
    deploy = None
    if old.get("deployment_target") != new.get("deployment_target"):
        deploy = {"old": old.get("deployment_target"), "new": new.get("deployment_target")}
    o_deps = old.get("dependencies", {}) or {}
    n_deps = new.get("dependencies", {}) or {}
    deps = {
        "added": {k: n_deps[k] for k in sorted(set(n_deps) - set(o_deps))},
        "removed": {k: o_deps[k] for k in sorted(set(o_deps) - set(n_deps))},
        "changed": {k: {"old": o_deps[k], "new": n_deps[k]} for k in sorted(set(o_deps) & set(n_deps)) if o_deps[k] != n_deps[k]},
    }
    return {"deployment_target": deploy, "dependencies": deps}


# ─────────────────────────── Name-matching discovery ───────────────────

def _catalog_lib_coords(catalog: Optional[dict]) -> Dict[str, str]:
    """From the catalog [libraries] section, map each Maven coordinate
    (group:artifact) to its version.ref key."""
    out: Dict[str, str] = {}
    for _key, spec in ((catalog or {}).get("libraries", {}) or {}).items():
        if not isinstance(spec, dict):
            continue
        module = spec.get("module")
        ver = spec.get("version")
        ref = ver.get("ref") if isinstance(ver, dict) else None
        if module and ref:
            out[module] = ref
    return out


def build_discovery(pins: Dict[str, Any], new_catalog: Optional[dict],
                    chain: Dict[str, Optional[str]], finder: Finder) -> dict:
    """Match each plugin pin to a catalog version by ACTUAL MAVEN COORDINATE
    (unambiguous), not by fuzzy key name.

    - CleverTap-owned SDKs (core / push-templates / hms) are matched by artifact:
      core's target comes from the RN chain (authoritative); pt/hms from the
      catalog's known version keys.
    - Third-party deps are matched only when the plugin's exact coordinate appears
      in the catalog's [libraries] section → its version.ref → target. This is why
      `play-services-ads-identifier` correctly does NOT match the catalog's
      `play-services-ads` (different artifact) — no false auto-bump.
    - Anything without a coordinate match is flagged (plugin_only); the brain
      re-verifies, never an auto-sync.
    """
    catalog_versions = (new_catalog or {}).get("versions", {}) or {}
    lib_coords = _catalog_lib_coords(new_catalog)
    coordinate_map: Dict[str, List[str]] = pins.get("coordinate_map", {}) or {}
    mapped: List[dict] = []
    plugin_only: List[dict] = []
    matched_catalog_keys = set()

    for pkey, pcur in pins.get("android_versions", {}).items():
        coords = coordinate_map.get(pkey, [])
        artifacts = {c.split(":", 1)[1] for c in coords if ":" in c}

        def _add_mapped(catalog_key, target, source):
            mapped.append({
                "plugin_key": pkey, "catalog_key": catalog_key,
                "coordinates": coords,
                "plugin_current": pcur, "catalog_target": target,
                "changed": bool(target and target != pcur),
                "confidence": "high", "source": source,
            })
            if catalog_key:
                matched_catalog_keys.add(catalog_key)

        # CleverTap-owned SDKs — matched by artifact name.
        if "clevertap-android-sdk" in artifacts:
            _add_mapped(CATALOG_KEY_CORE, chain.get("required_android_core"),
                        "clevertap-react-native android/build.gradle (chain)")
            continue
        if "push-templates" in artifacts:
            _add_mapped(CATALOG_KEY_PT, catalog_versions.get(CATALOG_KEY_PT),
                        f"libs.versions.toml [versions].{CATALOG_KEY_PT}")
            continue
        if "clevertap-hms-sdk" in artifacts:
            _add_mapped(CATALOG_KEY_HMS, catalog_versions.get(CATALOG_KEY_HMS),
                        f"libs.versions.toml [versions].{CATALOG_KEY_HMS}")
            continue

        # Third-party: exact coordinate match against catalog [libraries].
        ref = next((lib_coords[c] for c in coords if c in lib_coords), None)
        if ref and ref in catalog_versions:
            _add_mapped(ref, catalog_versions[ref],
                        f"libs.versions.toml [libraries] coordinate match -> [versions].{ref}")
            continue

        # No reliable catalog source — flag, never auto-sync.
        plugin_only.append({
            "plugin_key": pkey, "plugin_current": pcur, "coordinates": coords,
            "reason": ("no exact catalog [libraries] coordinate match — plugin-managed "
                       "(e.g. a different Maven artifact than the catalog). Verify manually "
                       "against the SDK before changing; do NOT auto-sync."),
            "confidence": "low",
        })

    catalog_only = [
        {"catalog_key": k, "catalog_value": catalog_versions[k]}
        for k in sorted(set(catalog_versions) - matched_catalog_keys)
    ]
    return {"mapped": mapped, "catalog_only": catalog_only, "plugin_only": plugin_only}


# ─────────────────────────── Changelogs ────────────────────────────────

_ANDROID_HEADING = re.compile(r"^###\s+\[?Version\s+(\d+\.\d+\.\d+(?:[.\w]*)?)\b", re.MULTILINE | re.IGNORECASE)
# RN uses setext headings: `Version 4.1.0 *(April 30 2026)*` underlined with dashes.
_RN_HEADING = re.compile(r"^Version\s+(\d+\.\d+\.\d+(?:[.\w]*)?)\b.*$", re.MULTILINE)


def _android_changelog_block(text: str, old_v: str, new_v: str) -> dict:
    return _block_by_heading(text, _ANDROID_HEADING, r"^###\s+\[?Version\b", old_v, new_v)


def _rn_changelog_block(text: str, old_v: Optional[str], new_v: str) -> dict:
    return _block_by_heading(text, _RN_HEADING, r"^Version\s+\d", old_v, new_v)


def _block_by_heading(text: str, heading_re: re.Pattern, next_re: str,
                      old_v: Optional[str], new_v: str) -> dict:
    """Generic: extract the new_v entry verbatim + every intermediate entry
    strictly between old_v and new_v."""
    if not text:
        return {"target_version": new_v, "target_entry": None, "intermediate_entries": []}
    all_versions = [m.group(1) for m in heading_re.finditer(text)]

    def entry_for(v: str) -> Optional[str]:
        pat = re.compile(
            rf"^[#\[ ]*Version\s+{re.escape(v)}\b.*?(?={next_re}|\Z)",
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        m = pat.search(text)
        return m.group(0).strip() if m else None

    target = entry_for(new_v)
    intermediates = []
    if old_v:
        ot, nt = parse_version(old_v), parse_version(new_v)
        for v in all_versions:
            if ot < parse_version(v) < nt:
                e = entry_for(v)
                if e:
                    intermediates.append({"version": v, "entry": e})
    return {"target_version": new_v, "target_entry": target, "intermediate_entries": intermediates}


def collect_changelogs(finder: Finder, chain: Dict[str, Optional[str]],
                       rn_version: str, rn_current: Optional[str],
                       core_old: Optional[str], core_new: Optional[str],
                       pt_new: Optional[str], hms_new: Optional[str],
                       ios_old: Optional[str], ios_new: Optional[str],
                       expo_version: str, expo_current: Optional[str]) -> dict:
    out: dict = {}

    rn_repo = REPOS["rn"][0]
    rn_tag = chain.get("rn_tag")
    rn_text = finder.fetch_raw(rn_repo, rn_tag, RN_CHANGELOG) if rn_tag else None
    out["rn"] = _rn_changelog_block(rn_text or "", rn_current, rn_version)

    sdk_repo = REPOS["android_core"][0]
    core_tag = finder.resolve_tag("android_core", core_new) if core_new else None
    core_text = finder.fetch_raw(sdk_repo, core_tag, ANDROID_CORE_CHANGELOG) if core_tag else None
    out["android_core"] = _android_changelog_block(core_text or "", core_old or "", core_new or "")

    # iOS core: same '### [Version X.Y.Z]' format as Android. Walk intermediates
    # between the iOS SDK version the plugin's RN-current required and the target's.
    ios_repo = REPOS["ios_core"][0]
    ios_tag = finder.resolve_tag("ios_core", ios_new) if ios_new else None
    ios_text = finder.fetch_raw(ios_repo, ios_tag, IOS_CHANGELOG) if ios_tag else None
    out["ios_core"] = _android_changelog_block(ios_text or "", ios_old or "", ios_new or "")

    pt_text = finder.fetch_raw(sdk_repo, core_tag, ANDROID_PT_CHANGELOG) if core_tag else None
    out["push_templates"] = _android_changelog_block(pt_text or "", "", pt_new or "")

    hms_text = finder.fetch_raw(sdk_repo, core_tag, ANDROID_HMS_CHANGELOG) if core_tag else None
    out["hms"] = _android_changelog_block(hms_text or "", "", hms_new or "")

    # Expo: not parsed here — the brain has WebFetch.
    out["expo"] = {
        "target_version": expo_version,
        "source": "webfetch_needed",
        "urls": [
            EXPO_CHANGELOG_WEB.format(ver=expo_version),
            EXPO_CHANGELOG_GH,
        ],
        "note": "Expo changelog is HTML; the orchestrator reads these with WebFetch. "
                "Walk intermediate SDK versions if jumping more than one major.",
    }
    return out


# ─────────────────────────── Main ──────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Fact finder for the CleverTap Expo plugin sync.")
    p.add_argument("--rn-version", required=True, help="Target clevertap-react-native version, e.g. 4.1.0")
    p.add_argument("--expo-sdk-version", required=True, help="Target Expo SDK version, e.g. 56")
    p.add_argument("--plugin-path", type=Path, required=True, help="Checked-out clevertap-expo-plugin root")
    p.add_argument("--rn-current", default=None, help="Current clevertap-react-native version (else read from README)")
    p.add_argument("--expo-current", default=None, help="Current Expo SDK version (informational)")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    p.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"))
    p.add_argument("--no-cache", action="store_true")
    args = p.parse_args()

    if not args.plugin_path.exists():
        print(f"[expo-diff] plugin path does not exist: {args.plugin_path}", file=sys.stderr)
        return 2

    finder = Finder(args.cache_dir, args.github_token, args.no_cache)

    # 1. Discover the plugin's current pins.
    print("[expo-diff] discovering plugin pins…", file=sys.stderr)
    pins = discover_plugin_pins(args.plugin_path, finder)
    rn_current = args.rn_current or pins.get("rn_current")
    core_old = pins.get("android_versions", {}).get("clevertapCoreSdkVersion")

    # 2. Resolve the chain (what the target RN release requires).
    print(f"[expo-diff] resolving clevertap-react-native {args.rn_version} chain…", file=sys.stderr)
    chain = resolve_chain(finder, args.rn_version)
    core_new = chain.get("required_android_core")
    ios_new = chain.get("required_ios_core")

    # 3. Android catalog diff (plugin's current core vs resolved target core).
    print("[expo-diff] diffing Android version catalog…", file=sys.stderr)
    old_catalog = fetch_catalog(finder, core_old) if core_old else None
    new_catalog = fetch_catalog(finder, core_new) if core_new else None
    catalog_diff = diff_catalog_versions(old_catalog, new_catalog)

    # Resolve aligned pt/hms target versions from the target catalog (deterministic).
    nv = (new_catalog or {}).get("versions", {}) or {}
    pt_new = nv.get(CATALOG_KEY_PT)
    hms_new = nv.get(CATALOG_KEY_HMS)

    # 4. Android dependency-block diff (core; pt/hms best-effort).
    print("[expo-diff] diffing Android dependency blocks…", file=sys.stderr)
    dep_diff = {}
    if core_old and core_new:
        dep_diff["core"] = diff_dep_block(
            fetch_dep_block(finder, "android_core", core_old, ANDROID_CORE_GRADLE),
            fetch_dep_block(finder, "android_core", core_new, ANDROID_CORE_GRADLE),
        )

    # 5. iOS podspec diff.
    print("[expo-diff] diffing iOS podspec…", file=sys.stderr)
    ios_old_core = None
    if rn_current:
        rn_cur_tag = finder.resolve_tag("rn", rn_current)
        if rn_cur_tag:
            podspec = finder.fetch_raw(REPOS["rn"][0], rn_cur_tag, RN_PODSPEC)
            if podspec:
                m = RN_IOS_PIN_RE.search(podspec)
                if m:
                    ios_old_core = m.group(1)
    if not ios_old_core:
        finder.warn("could not resolve current iOS core version (rn_current unknown) — "
                    "iOS diff reports target only")
    ios_diff = diff_ios(fetch_ios_podspec(finder, ios_old_core), fetch_ios_podspec(finder, ios_new))

    # 6. Name-matching discovery (replaces the hardcoded mapping table).
    print("[expo-diff] matching plugin pins to catalog…", file=sys.stderr)
    discovery = build_discovery(pins, new_catalog, chain, finder)
    discovery["ios_deployment_target"] = {
        "plugin_current": pins.get("ios_deployment_target"),
        "ios_diff": ios_diff.get("deployment_target"),
    }
    discovery["classpaths"] = pins.get("classpaths", {})

    # 7. Changelogs.
    print("[expo-diff] collecting changelogs…", file=sys.stderr)
    changelogs = collect_changelogs(
        finder, chain, args.rn_version, rn_current,
        core_old, core_new, pt_new, hms_new,
        ios_old_core, ios_new,
        args.expo_sdk_version, args.expo_current,
    )

    payload = {
        "meta": {
            "rn_current": rn_current,
            "rn_target": args.rn_version,
            "expo_current": args.expo_current or pins.get("expo_devdep"),
            "expo_target": args.expo_sdk_version,
            "plugin_version": pins.get("plugin_version"),
            "resolved": {
                "android_core_old": core_old,
                "android_core_new": core_new,
                "ios_core_old": ios_old_core,
                "ios_core_new": ios_new,
                "push_templates_new": pt_new,
                "hms_new": hms_new,
            },
            "discovered_pin_count": len(pins.get("android_versions", {})),
            "warnings": finder.warnings,
        },
        "chain": chain,
        "android_catalog_diff": {"versions": catalog_diff},
        "android_dependency_diff": dep_diff,
        "ios_diff": ios_diff,
        "discovery": discovery,
        "changelogs": changelogs,
    }

    out_dir = args.out_dir / f"{args.rn_version}-expo{args.expo_sdk_version}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "expo-diff.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"[expo-diff] wrote {out_path}", file=sys.stderr)
    print(str(out_path))  # stdout: the path, for the caller

    # FAIL LOUD: if we could not resolve the core chain (the single most important
    # fact) or hit warnings, exit non-zero so the brain treats the output as suspect.
    if not core_new:
        print("[expo-diff] FATAL: could not resolve the required CleverTap Android SDK "
              "version from the RN release. Aborting.", file=sys.stderr)
        return 3
    if finder.warnings:
        print(f"[expo-diff] completed with {len(finder.warnings)} warning(s) — see meta.warnings. "
              f"The orchestrator must treat flagged/uncertain items as needs-review, not facts.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
