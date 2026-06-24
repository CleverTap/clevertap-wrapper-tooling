# Flashcards — retrieve before you flip

> One card per [glossary](../GLOSSARY.md) term and per key concept. **Cover the answer, say it out
> loud, then open the fold.** Grouped by topic, mirroring the glossary, so you can drill one area at
> a time. Plain enough to paste into Anki (front = the summary line, back = the body).

How to use: read the `<summary>` (the question), answer from memory, *then* expand. If you were
vague, that card comes back sooner. See the [retention method](./README.md).

---

## The domain (CleverTap SDKs)

<details><summary>What is a <b>native SDK</b>?</summary>

The "real" CleverTap library for one platform: `clevertap-android-sdk` (Kotlin/Java) and
`clevertap-ios-sdk` (Objective-C/Swift). Native apps use it directly.
</details>

<details><summary>What is a <b>wrapper SDK</b>?</summary>

A thin library that lets cross-platform apps (JavaScript for Cordova/React Native, Dart for Flutter)
call the native SDK underneath. CleverTap has `clevertap-cordova`, `clevertap-react-native`,
`clevertap-flutter`.
</details>

<details><summary>What is the <b>bridge</b>?</summary>

The cross-language glue inside a wrapper. When JavaScript calls `recordEvent`, the bridge carries
that call down to the native Android/iOS method that actually does it.
</details>

<details><summary>What is the <b>API surface</b>?</summary>

The set of public methods the SDK exposes for others to call (e.g. `recordEvent`, `onUserLogin`).
"Surfacing an API" = exposing a new native method through the wrapper.
</details>

<details><summary>What is a <b>module</b> in a native SDK?</summary>

A versioned, separately-tagged piece of a native SDK. Android has `core`, `pushtemplates`, `hms`;
iOS has `core`, `pushtemplates`.
</details>

<details><summary>What is a <b>native release / version pin</b>?</summary>

The exact native SDK version a wrapper depends on (e.g. the Cordova plugin pins
`clevertap-android-sdk:8.2.0`). "Bumping the pin" = pointing the wrapper at a newer native version.
</details>

<details><summary>What is <b>libVersion</b> and how is it computed?</summary>

A version encoded as a plain integer in bridge code: `major*10000 + minor*100 + patch`. Example:
`5.2.3` → `50203`. It tells the native SDK which wrapper version is calling it.
</details>

<details><summary>What is <b>SemVer</b>, and what do MAJOR / MINOR / PATCH mean?</summary>

Semantic versioning: `MAJOR.MINOR.PATCH`. MAJOR = breaking change, MINOR = new backward-compatible
features, PATCH = fixes only.
</details>

---

## The triage vocabulary (what the AI decides per change)

<details><summary><b>Surfaced</b> — what does it mean?</summary>

A native API change the AI *implemented* in the wrapper (added/updated the bridge).
</details>

<details><summary><b>Skipped</b> — what does it mean?</summary>

A change the AI deliberately did **not** expose (e.g. an internal-only helper).
</details>

<details><summary><b>Deferred</b> — what does it mean?</summary>

A change the AI couldn't safely auto-apply, so it left it for a human with a reason.
</details>

<details><summary><b>Flagged for review</b> — and how does it differ from deferred?</summary>

A specific deferral: the AI couldn't *confirm* something (e.g. a method named in the changelog it
couldn't find in source), so it raises a flag instead of guessing. In the output JSON its `type` is
`removal | deprecation | signature | behavior | unconfirmed`.
</details>

<details><summary>What is <b>source verification</b>, and why is it non-negotiable?</summary>

The rule that the AI must find the exact method/selector in the real native source *before* writing
a call to it. Guessing a symbol that doesn't exist = a broken build. "Verify or flag — never guess."
</details>

<details><summary>What is the <b>recall pass</b>?</summary>

A second sweep where the AI cross-checks the native **changelog** against the diff tool's output, to
catch the ~20% of changes the regex parser misses.
</details>

<details><summary>Precision vs. recall — what's the difference, and who provides each?</summary>

Precision = "of what I reported, how much is correct?" (the regex diff — only reports what it
parsed). Recall = "of all that truly changed, how much did I find?" (the changelog pass boosts this
to catch the regex's ~20% miss).
</details>

---

## Python (the diff tool is written in it)

<details><summary>What is <b>Python</b>, and how do you run a file?</summary>

A programming language; files end in `.py`. Run one with `python3 file.py`. No compile step.
</details>

<details><summary>What is the <b>standard library</b>, and why does it matter here?</summary>

The batteries included with Python itself. The diff tool uses **only** the stdlib, so there's
nothing to install — **no `pip install` needed**.
</details>

<details><summary>What is <b>pip</b>?</summary>

Python's package installer (an app store for libraries). Not needed for the diff tool.
</details>

<details><summary>What is a <b>regex</b>, and what does the diff tool use it for?</summary>

A mini-language for text patterns. The diff tool uses regex to *find method declarations in source*
without fully parsing the code. Powerful but imperfect — hence ~80% coverage.
</details>

<details><summary>What is an <b>AST</b>, and why does the tool NOT use one?</summary>

Abstract syntax tree — the "proper" full-grammar way to parse code. The tool deliberately uses regex
instead because it's simpler and good enough (the "regex-based, not AST" design note).
</details>

<details><summary>What is a <b>dataclass</b>?</summary>

A Python shorthand for a small data-holding object; `@dataclass` auto-writes the boilerplate.
`Symbol` and `Surface` in the diff tool are dataclasses.
</details>

<details><summary>What does <b>frozen=True</b> do on a dataclass?</summary>

Makes it immutable (can't change after creation). Immutable objects can be dict keys and set members
— which is how the tool dedupes/compares symbols.
</details>

<details><summary>What is a Python <b>set</b>, and what do <code>-</code> and <code>&</code> do?</summary>

A collection of unique items. `A - B` = in A but not B (difference); `A & B` = in both
(intersection); `A | B` = in either (union). The diff is literally `new - old` (added) and
`old - new` (removed).
</details>

<details><summary>What is a <b>dict</b>, and what's a <b>tuple key</b>?</summary>

A lookup table mapping keys to values. A tuple key like `("android","core")` lets the tool look
things up by *platform + module together*.
</details>

<details><summary>What is <b>tomllib</b> used for?</summary>

A stdlib module (Python ≥ 3.11) that reads `.toml` files. Used to read Android's
`gradle/libs.versions.toml` dependency-versions list.
</details>

<details><summary>What is <b>pathlib / Path</b>?</summary>

Stdlib way to build file paths with `/` like Lego (`Path.home() / ".cache"`) instead of gluing
strings. Cross-OS.
</details>

<details><summary>What is <b>subprocess</b>, and how does the tool "use git"?</summary>

Stdlib way to run another command-line program. `subprocess.check_output(["git", ...])` literally
runs `git` and captures its output — that's how the Python file uses git without reimplementing it.
</details>

<details><summary>What is <b>urllib</b> used for here?</summary>

Stdlib way to download from the internet — here, a `.tar.gz` of the SDK source from GitHub.
</details>

<details><summary>What is a <b>tarball</b> (<code>.tar.gz</code>)?</summary>

A compressed archive (like a `.zip`). GitHub serves a repo at a tag as one; the tool downloads and
unpacks it (stripping the single top-level folder GitHub wraps everything in).
</details>

---

## git & GitHub

<details><summary>What is <b>git</b>?</summary>

A version-control tool: it records every change as a snapshot so you can branch, compare, and revert.
</details>

<details><summary>What is a <b>repository</b>?</summary>

One project's folder tracked by git (e.g. `clevertap-cordova`).
</details>

<details><summary>What is a <b>branch</b>, and what does the sync create?</summary>

An independent line of changes. The sync creates a fresh branch like `task/release_<name>` so its
edits don't touch the base branch until reviewed.
</details>

<details><summary>What is the <b>develop / base branch</b>?</summary>

The main integration branch the sync starts *from* and opens its PR *against*.
</details>

<details><summary>What is a <b>commit</b>?</summary>

One saved snapshot of changes, with a message.
</details>

<details><summary>What is a <b>pull request (PR)</b>, and why does it matter here?</summary>

A proposal to merge one branch into another, with a diff and a place to review. The whole
automation's *output* is always a PR — never a silent change.
</details>

<details><summary>What is a <b>tag</b>, and how does the diff tool use it?</summary>

A name pinned to a specific commit, used for releases (e.g. `corev8.2.0`). The diff tool fetches
source *at a tag*.
</details>

<details><summary>What is <b>gh</b>?</summary>

GitHub's command-line tool. Scripts use `gh pr create`, `gh label create`, etc.
</details>

---

## GitHub Actions (the automation runner)

<details><summary>What is <b>GitHub Actions</b>?</summary>

GitHub's built-in automation; runs your scripts on GitHub's servers when something happens (a button
click, a push, a schedule).
</details>

<details><summary>What is a <b>workflow</b>, and where does it live?</summary>

A `.yml` file describing a sequence of automated steps, under `.github/workflows/`.
</details>

<details><summary>What is <b>YAML</b>?</summary>

A text format for configuration; indentation matters (like Python). Workflows are written in it.
</details>

<details><summary>What is <b>workflow_dispatch</b>?</summary>

A trigger meaning "run when a human clicks the button" (a manual dispatch), as opposed to running on
a push.
</details>

<details><summary>What is <b>workflow_call</b> / a reusable workflow?</summary>

A workflow other workflows can *call*, like a shared function. `sync.yml` is one; each wrapper repo's
tiny dispatch calls it.
</details>

<details><summary>What is a <b>composite action</b>? Name a few here.</summary>

A reusable bundle of steps (a function within Actions), under `.github/actions/`. Examples: `setup`,
`claude-sync`, `open-pr`, `build/*`.
</details>

<details><summary>What is a <b>runner</b>, and why <code>macos-14</code> here?</summary>

The virtual machine a workflow runs on. The sync uses `macos-14` because building the iOS example
requires a Mac (Xcode).
</details>

<details><summary>What is a step's <b>outcome</b>, and what values can it take?</summary>

The status Actions assigns automatically: `success`, `failure`, `cancelled`, or `skipped` (when its
`if:` was false). Read as `steps.<id>.outcome`.
</details>

<details><summary>What is an <b>if: / gating expression</b>?</summary>

A condition on a step deciding whether it runs. The trickiest logic in `sync.yml` lives here (e.g.
"open the PR only if a sync succeeded and nothing was cancelled").
</details>

<details><summary>What do <code>always()</code>, <code>failure()</code>, and <code>!cancelled()</code> mean?</summary>

`always()` = run no matter what (even on cancel). `failure()` = run only if a prior step failed.
`!cancelled()` = run on success *or* failure, but not if the run was cancelled. Without one, Actions
skips remaining steps after any failure.
</details>

<details><summary>Why use <code>!= 'failure'</code> instead of <code>== 'success'</code> in a gate?</summary>

A *skipped* step (its `if:` was false, e.g. no iOS version) has outcome `skipped`, not `success`.
`== 'success'` would wrongly block a single-platform run; `!= 'failure'` lets *skipped* through while
still blocking a genuine *failure*.
</details>

<details><summary>What is a <b>secret</b>, and how many does this system need?</summary>

An encrypted value (API keys, tokens) stored in repo settings that workflows read but humans can't
see. This system needs **four**: App ID, App private key, Anthropic key, Slack webhook URL.
</details>

<details><summary>What is a <b>GitHub App</b> here, and what's its name?</summary>

A bot identity (`clevertap-wrapper-sync`) granted permissions to mint short-lived tokens and act on
a repo (push a branch, open a PR) without using a person's account.
</details>

<details><summary>What is a <b>token</b>, and when is it minted?</summary>

A temporary password proving the bot may act. Minted at the start of a run (in Setup); expires when
the run ends.
</details>

<details><summary>What is an <b>artifact</b>?</summary>

A file a workflow saves for download afterward (e.g. the built APK, or Claude's output JSON/stream
logs). The sync uploads these `if: always()` for debugging.
</details>

---

## Claude-in-CI (the brain)

<details><summary>What does <b>headless</b> mean, and how is Claude invoked?</summary>

Running Claude with no human chatting — given one prompt, it runs to completion on its own. Invoked
as `claude -p "…"` (print mode).
</details>

<details><summary>What is a <b>prompt</b>, and where do the big ones live?</summary>

The written instructions handed to Claude — effectively a *program* in English. The big ones live in
`prompts/` (e.g. `sync-orchestrator-cordova.md`).
</details>

<details><summary>What is <b>.claude/skills/</b>, and how does it differ from the prompt?</summary>

Per-repo expert instructions Claude auto-discovers and follows — the *real conventions* for that
wrapper. The prompt is the **task**; the skills are the **know-how**.
</details>

<details><summary>What is the <b>allowlist</b> (<code>--allowed-tools</code>)?</summary>

The exact set of tools Claude may use in a run (e.g. read/edit files, run specific commands). A
security boundary — anything not listed is denied. For Cordova, `python3` is pinned to *only* the
diff tool.
</details>

<details><summary>What is <b>envsubst</b>, and why is it used on the prompt?</summary>

A tiny command that fills `${PLACEHOLDER}` blanks in a text file with real env values. It turns one
static prompt template into a run-specific prompt (injects `${PLATFORM}`, `${NEW_VERSION}`, etc.).
</details>

<details><summary>What is <b>stream-json</b>, and how is the final result extracted?</summary>

An output format where Claude emits one JSON event per line (JSON Lines). Scripts use
`jq 'select(.type=="result")' | tail -1` to pull the final `result` envelope for cost/token totals.
</details>

<details><summary>What is <b>jq</b>?</summary>

A command-line tool for slicing JSON. Used to pull the `result` event out of the stream.
</details>

<details><summary>What is the <b>soft cap</b>?</summary>

A cost threshold (e.g. $3) that, if exceeded, posts an informational PR comment. It does **not** stop
the run — just visibility.
</details>

<details><summary>What is <b>self-heal</b>?</summary>

An (optional/retired) retry loop: if a build fails, ask Claude to fix the code and try again, up to
N times.
</details>

<details><summary>Why does the claude-sync action drop <code>--bare</code>?</summary>

`--bare` would skip auto-discovery of the wrapper repo's `.claude/skills`. The orchestrator prompt
relies on those skills, so running non-bare loads them — a deliberate correctness choice.
</details>

<details><summary>Why <code>set +e</code> around the <code>claude</code> call?</summary>

So a non-zero exit doesn't instantly abort the script. The action captures the exit code (`rc=$?`),
still writes the result file, prints stderr + last 50 events, then fails deliberately with
`exit $rc`. `set -e` restores strict mode after.
</details>

---

## The 4-layer onion & key concepts

<details><summary>Name the four layers, one phrase each.</summary>

① **Trigger** (a button in a wrapper repo) → ② **Conductor** (`sync.yml` sequences & gates) →
③ **Brain** (Claude, headless, writes the code) → ④ **Ground truth** (`diff_native_api.py`, cold
facts). Click travels down; PR travels up.
</details>

<details><summary>Which layer actually writes the JS/Kotlin/Obj-C bridge code?</summary>

**Layer ③ — Claude.** The conductor (`sync.yml`) only sequences steps; the YAML wraps no APIs. This
is the idea beginners most often get backwards.
</details>

<details><summary>Why does a non-AI Python tool (Layer ④) exist if Claude is so capable?</summary>

Because an AI can hallucinate a method that doesn't exist. The diff tool reports only what's literally
in source, giving Claude a factual anchor it's told to trust and source-verify against.
</details>

<details><summary>What are the four stages of <code>diff_native_api.py</code>?</summary>

**Acquire → Extract → Diff → Render.** Get the source, pull out public methods (the surface), compare
old vs new, write `diff.json` + `diff.md`.
</details>

<details><summary>What are the three tiers of <code>acquire_sources</code>, fastest-first?</summary>

1) **Local clone** (if it has the git tag), 2) **cache** (downloaded on a past run), 3) **download**
the `.tar.gz` from GitHub. First that works wins.
</details>

<details><summary>In <code>_JAVA_PUBLIC_METHOD</code>, what do groups 1/2/3 capture?</summary>

Group 1 = **return type**, group 2 = **method name**, group 3 = **params**. Hence
`return_type, name, params = m.group(1), m.group(2), m.group(3)`.
</details>

<details><summary>What does the negative lookahead <code>(?!class\b|interface\b|…)</code> do?</summary>

Ensures the line is NOT a class/interface/enum/constant declaration, so `public class CleverTapAPI {`
isn't mistaken for a method. Keeps the regex to *methods only*.
</details>

<details><summary>Why does the Java extractor do a cheap <code>"public" not in line</code> check first?</summary>

Speed. Running regex on every line is wasteful; most lines obviously can't be a public method, so a
fast substring test rejects them before the expensive pattern.
</details>

<details><summary>What does <code>_is_restricted</code> filter out, and why?</summary>

Methods preceded by `@RestrictTo`/`@Hide`/`@Internal`/`@VisibleForTesting`. They're internal-only and
should never be surfaced to wrapper users.
</details>

<details><summary>How does <code>compute_diff</code> decide "changed"?</summary>

For a name in both versions, it builds the **set of signatures** in old and in new and compares with
`!=`. If the signature sets differ (param added, overload appeared, etc.), it lands in `changed`.
</details>

<details><summary>Why is everything in <code>compute_diff</code> wrapped in <code>sorted(...)</code>?</summary>

Sets are unordered. Sorting makes the output deterministic/reproducible — the same SDK pair always
produces byte-identical `diff.json`, keeping git diffs clean.
</details>

<details><summary>For a <code>8.1.0 → 8.3.0</code> sync, which changelog entries get read, and why?</summary>

The **target** (8.3.0) **plus every version strictly between** (8.2.0). Syncs skip versions; reading
intermediates surfaces changes that landed in a skipped release.
</details>

<details><summary>Why convert version strings to tuples of ints before comparing?</summary>

String comparison is wrong (`"8.10.0" < "8.9.0"` alphabetically). Tuples `(8,10,0)` vs `(8,9,0)`
compare numerically element-by-element, so ordering and "strictly between" work.
</details>

<details><summary>Why does <code>_CHANGELOG_METHOD_CALL</code> require a lowercase first letter?</summary>

To skip class names. Methods are lowerCamelCase (`recordEvent`), classes UpperCamelCase
(`CleverTapAPI`). Anchoring on `[a-z]` keeps the recall set to likely *methods*.
</details>

<details><summary>What are the THREE Android touches for a new method?</summary>

1) `CleverTapFunction.java` — add the enum constant. 2) `CleverTapPlugin.java` — add the case in the
`execute()` switch. 3) `CleverTapPlugin.java` — add the private implementation method.
</details>

<details><summary>What are the TWO iOS touches?</summary>

The `.h` declaration and the `.m` implementation.
</details>

<details><summary>Why is a missed Android touch a "silent no-op," and why is that worse than a compile error?</summary>

The app still **compiles** and the method exists, but it never reaches its implementation — runs and
does nothing, no crash or warning. A compile error is caught instantly; a silent no-op ships
unnoticed. Hence "always all three, then re-verify."</details>

<details><summary>What must be identical across JS, Android, and iOS for one method?</summary>

The **action string** — identical across the JS `cordova.exec`, the Android enum string, and the iOS
selector.
</details>

<details><summary>Why does the pre-sync build run BEFORE Claude does anything?</summary>

To fail fast and cheap. If the example app is already broken on `base_ref`, the run stops before
spending any AI cost — no point syncing into a pipeline that can't build.
</details>

<details><summary>Is a post-sync build failure fatal?</summary>

No. The PR still opens with a **`build-failed`** label and a warning banner; a human pulls the branch,
fixes the compile error, pushes, and merges. ("Option A.")
</details>

<details><summary>What is the system's output, every single time?</summary>

A **pull request** for a human to review and merge. The human approval is never automated away.
</details>

<details><summary>What does <code>skip_sync=true</code> still run, and what does it skip?</summary>

Still runs the **pre-sync build** (to test the pipeline); skips the AI Sync steps and post-sync build
— so **$0 AI cost**.
</details>

<details><summary>What is the "thin pointer" model?</summary>

Each wrapper repo carries only a tiny dispatch workflow that *calls* the hub's `sync.yml` (plus its
`.claude/skills`). All sync logic lives once in the hub — fix a bug once, every wrapper benefits.
</details>

<details><summary>Hub vs. wrapper repos — what lives where?</summary>

**Hub** (`clevertap-wrapper-tooling`): `sync.yml`, composite actions, `diff_native_api.py`, `prompts/`,
`scripts/`. **Wrapper** (`clevertap-cordova` etc.): the tiny `native-release-sync.yml` dispatch,
`.claude/skills/`, and the bridge code + example apps the automation edits.
</details>

---

**Next:** [exercises.md — do it, don't read it →](./exercises.md)
