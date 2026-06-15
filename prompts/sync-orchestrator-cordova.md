You are syncing the **CleverTap Cordova plugin** with a new native SDK release, running in AUTO-APPLY mode, invoked by the `clevertap-wrapper-sync` GitHub App during CI.

You have NO human in the loop. Do not ask questions. The Cordova repo ships a set of skills under `.claude/skills/` that hold the real conventions — wherever any skill says "wait for user acknowledgment", "Reply with Approved / Hold", "DISCUSS with user", or otherwise pauses for a human, treat that as: **make the best-judgment decision, proceed, and record it in your structured output.** Never stop and wait.

## Inputs for this run

- **Platform:** ${PLATFORM}  (android or ios)
- **Module:** ${MODULE}  (core / pushtemplates / hms)
- **New version:** ${NEW_VERSION}
- **Old version:** read from the wrapper repo's current pin (see step 1).
- **Diff tool path:** ${DIFF_TOOL_PATH}
- **Release date:** ${RELEASE_DATE} — human-readable date (e.g. "9 June 2026") used as the CHANGELOG entry date.

## Skills — invoke on demand, at the step that needs them (do NOT pre-read them all)

These skills hold the authoritative Cordova conventions and are available in this repo under `.claude/skills/`. **Invoke the relevant skill via the Skill tool at the step that needs it** (progressive — load only what you're about to use); do NOT read all of them upfront. Follow the invoked skill exactly rather than inferring from surrounding code. The step → skill mapping:

- `native-sdk-changelog-analysis` — at triage/recall (steps 3/3b): change categorization + decision tree + source-verification. (In CI: it already treats the diff tool as ground truth and skips WebFetch / human approval.)
- `api-wrapper-patterns` — at implementation (step 4): **MANDATORY** JS / Android (3-touch) / iOS bridge patterns, type mapping, code style.
- `example-app-patterns` — at the Example-demo step (4b): how to add a demo in **all 4 sample apps**.
- `version-detection` — at the version bump (step 6): the version-file locations + the `libVersion` integer conversion (which lives in TWO native files).
- `changelog-generation` — at the CHANGELOG step (step 7): exact `CHANGELOG.md` format, platform tags, native-SDK link anchors.
- `ionic-native-typings` — **NOT part of this sync.** The Ionic/`awesome-cordova-plugins` typings live in a separate repo and are updated by a separate workflow. Do NOT touch them here.

## What to do

1. **Read the wrapper repo's current native pin** for the requested platform/module. This is your `OLD_VERSION`. Both pins live in `plugin.xml`:
   - Android: grep `clevertap-android-sdk:` (or `clevertap-pushtemplates:` / `clevertap-hms:`) in `plugin.xml`.
   - iOS: grep `<pod name="CleverTap-iOS-SDK" spec="..."` (or the relevant pod) in `plugin.xml`.
   - If the pin is already at `${NEW_VERSION}`, exit immediately with an empty structured log — no work to do.

2. **Invoke the diff tool** to get the full diff between OLD_VERSION and NEW_VERSION:

   ```bash
   python3 ${DIFF_TOOL_PATH} \
       --platform ${PLATFORM} \
       --module ${MODULE} \
       --old-version <OLD_VERSION> \
       --new-version ${NEW_VERSION}
   ```

   Read the resulting `diff.json` from `~/.cache/clevertap-sdk-diff/${PLATFORM}-${MODULE}-<old>-to-${NEW_VERSION}/diff.json`. **This is your ground truth.** It has three parts:
   - `api_diff` — added / removed / changed public methods. This drives what you wrap.
   - `build_manifest` — minSdk / deployment target / permissions / dependency changes.
   - `changelog` — the native changelog entry, verbatim:
     ```json
     "changelog": {
       "target_version": "8.3.0",
       "target_entry": "### Version 8.3.0 ...",
       "intermediate_entries": [ {"version": "8.2.0", "entry": "..."} ]
     }
     ```

   **The changelog is a SECOND detection source — not just narrative.** The diff tool is regex-based (~80% coverage) and can miss real API changes: multi-line signatures, `@JvmOverloads`, Kotlin default-param methods, etc. `intermediate_entries` lists every version strictly between the old pin and the new version when releases were skipped — read those too. You reconcile the changelog against `api_diff` in **step 3b**. The changelog is also the source material for the human-readable `CHANGELOG.md` entry you write in step 7.

3. **Decide what to act on — from BOTH sources (union of `api_diff` and the changelog).**

   **3a. From `api_diff`:** walk the decision tree from the `native-sdk-changelog-analysis` skill for every added/removed/changed entry and every build-manifest delta. Categorize and decide: `NEW_IMPLEMENTATION`, `UPDATE`, `NO_ACTION`, or `SKIP`. Where the tree branches to "DISCUSS with user", make the best-judgment call yourself (auto-apply mode) and record the rationale — do not stop.

   **3b. Recall pass from the changelog (catch what the regex diff missed).** For every concrete public-API change the changelog names (in `target_entry` + `intermediate_entries`) that is NOT already covered by `api_diff`, you MUST **verify it against the new native source header before acting** — Android: `CleverTapAPI.java`; iOS: `CleverTap.h` (the same files the `native-sdk-changelog-analysis` skill uses; in the cached native source). Then:
   - **New API** — symbol exists in source and not already wrapped → implement it (step 4). If you can't fully confirm the signature, implement best-effort and mark the type `(inferred)`.
   - **Removed** — symbol is genuinely **absent** from the new source → remove/deprecate the wrapper method (this is a **MAJOR** bump).
   - **Deprecated** — symbol is **present but marked deprecated** (`@Deprecated` / `__attribute__((deprecated))`) → KEEP the wrapper method, add a deprecation note. Do NOT delete it.
   - **Signature changed** — source confirms a new signature → update the wrapper signature (**MAJOR** if a required parameter was added).
   - **Behavior-only change** — no symbol added/removed/changed → there is nothing to implement; add it to `flagged_for_review`.
   - **Cannot confirm in source** (symbol not found, or the changelog wording is ambiguous) → do NOT guess. Add it to `flagged_for_review` with what the changelog claimed.

   Items you acted on in 3b go in `surfaced` (or `skipped`) like any other. Items you could NOT safely auto-apply — behavior-only changes and anything you couldn't confirm — go in `flagged_for_review` so a human reviews them. The changelog is authoritative for *what exists*, the source confirms *how*.

4. **Apply each "surface" decision** by following the `api-wrapper-patterns` skill exactly, across all bridge layers. **Before writing each native call, source-verify the exact symbol** (see "Source verification" below) — never copy a method/selector name from examples or neighboring code without confirming it exists at the new version. The Cordova bridge layers:
   - **JS** — `www/CleverTap.js`: add the `CleverTap.prototype.<action> = function (args, successCallback) { cordova.exec(...) }`. Keep JS a thin pass-through (only the existing `convertDateToEpochInProperties` normalization is allowed).
   - **Android — the THREE touches** (a missed one is a silent runtime no-op, not a compile error):
     1. `src/android/CleverTapFunction.java` — add the enum constant whose action string equals the JS action.
     2. `src/android/CleverTapPlugin.java` — add the `case` in the `execute()` switch.
     3. `src/android/CleverTapPlugin.java` — add the private implementation (use `executeWithArgs`, `cordova.getThreadPool().execute`, `sendPluginResult`).
   - **iOS — TWO touches** — `src/ios/CleverTapPlugin.h` (declare `- (void)<action>:(CDVInvokedUrlCommand *)command;`) **and** `src/ios/CleverTapPlugin.m` (implement, wrapping SDK work in `[self.commandDelegate runInBackground:^{ … }]`).
   - The action string MUST be identical across the JS `cordova.exec` action, the `CleverTapFunction` enum string, and the iOS selector name. Use the type mapping in `api-wrapper-patterns` and `native-sdk-changelog-analysis/references/type-mapping.md`.

4b. **Add an Example-app demo for EVERY surfaced API in ALL 4 sample apps — mandatory, do NOT skip.** Follow the `example-app-patterns` skill. Clients integrate via different stacks, so each sample must demo the API:
   - `Samples/Cordova/ExampleProject/www/js/index.js` — an `eventsMap` `["Label", fn]` entry under the right `["title", …]` group.
   - `Samples/IonicCordova/IonicAngularProject/src/app/home/home.page.ts` (+ `home.page.html`).
   - `Samples/IonicCapacitorAngularV2/ct-demo-ionic-angular-cap/src/app/home/home.page.ts` (+ `home.page.html`).
   - `Samples/IonicCapacitor/IonicCapReactProject` — the 3-touch (`helper/CleverTapActions.tsx` enum + `controllers/CleverTapAPIController.tsx` case + `data/*.ts` item).
   Use concrete realistic values. If a third-party typings package lacks the new method, cast `(CleverTap as any)` / `// @ts-ignore`. Every surfaced item's `files_touched` MUST include its sample-demo files. Do this even if the method already existed from a prior sync.

5. **Apply build-manifest propagations** (only if the diff shows them):
   - Android `minSdk` increased → bump `android-minSdkVersion` in the example `Samples/Cordova/ExampleProject/config.xml` and note it in the CHANGELOG.
   - iOS deployment target moved → note it in the CHANGELOG / host-setup docs.
   - New always-required Android permissions → declare in `plugin.xml`.
   - Record each propagation in `build_propagated`.

6. **Bump versions** using the `version-detection` skill. Set the native pin for THIS platform; bump the wrapper's own version everywhere else.
   - **Native pin for THIS platform** → set to `${NEW_VERSION}` in `plugin.xml`:
     - Android: `<framework src="com.clevertap.android:clevertap-android-sdk:${NEW_VERSION}"/>`.
     - iOS: `<pod name="CleverTap-iOS-SDK" spec="${NEW_VERSION}" />`.
     - Also update the matching `README.md` "Supported Versions" line for this platform.
   - **The wrapper's OWN version** → bump by semver:
     - **Patch**: no API changes surfaced; native pin bump only.
     - **Minor** (common): one or more additive APIs surfaced; no breaking changes.
     - **Major**: a `REMOVED` public method applied, a `CHANGED` row that added a required parameter, a propagated `minSdk` / deployment-target bump, or a host-impacting breaking change.
     - Edit in lockstep: `plugin.xml` (top `<plugin ... version="X.Y.Z">`), `package.json` (`"version"`), **both** `libVersion` integers — `src/android/CleverTapPlugin.java` AND `src/ios/CleverTapPlugin.m` (use the skill's conversion, e.g. `5.2.0` → `50200`).
   - **Coordination:** Sync Android runs first and performs the wrapper-version bump (all plugin-version locations including BOTH `libVersion` files); when Sync iOS runs second, the wrapper version is already bumped — verify it and re-emit the same `version_bump` decision, do NOT bump it twice. Each platform always sets its OWN native pin (and its own README line).

7. **Update `CHANGELOG.md`** following the `changelog-generation` skill — strict Cordova format, entry at the TOP, dated `${RELEASE_DATE}`, correct platform tags (`[Android Platform]`, `[iOS Platform]`, `[Android and iOS Platform]`), and a native-SDK support line with a valid version-anchor link. Derive the anchor from the date in the diff's `changelog.target_entry` (no WebFetch needed). Translate native jargon into Cordova/host-app terms.

## Cross-platform coordination — important

The workflow runs **Sync Android FIRST, then Sync iOS** (sequential, sharing the runner's filesystem). The JS layer (`www/CleverTap.js`) is shared. If Sync Android already added a method to `www/CleverTap.js`, that file ALREADY contains it when Sync iOS runs.

**Other platform's sync runs after yours in this workflow: `${OTHER_PLATFORM_SYNCING}`**

**Your PRIMARY job is the native bridge for YOUR platform, regardless of JS-layer state.** For every method in YOUR platform's `api_diff`, even if the JS method already exists (added by the previous sync), ensure YOUR platform's native implementation is present:
- **iOS (you):** confirm a matching `.h` declaration + `.m` implementation exists in `src/ios/CleverTapPlugin.{h,m}`. If missing, add it.
- **Android (you):** confirm the `CleverTapFunction` enum constant + `execute()` switch case + private method exist. If any is missing, add it.

Do NOT conclude "nothing to do" just because `www/CleverTap.js` already has the method — the JS wrapper alone is not a complete bridge.

### Completing the OTHER platform's bridge — verify-or-flag, never guess

The regex diff sometimes catches an API on one platform but misses it on the other. A strict "stay in your lane" rule would leave the other platform's bridge missing (a JS method whose native side doesn't exist → a silent no-op / error at runtime). So completing the other platform's bridge is ALLOWED, with rules:

- **If `${OTHER_PLATFORM_SYNCING}` is `true`:** the other platform's sync runs AFTER you in this same workflow, with its own diff and its own native source. Do NOT add or edit its native bridge files — it will handle its side with better information.
- **If `${OTHER_PLATFORM_SYNCING}` is `false`:** you are the last (or only) sync in this run. If the shared JS layer references a method whose other-platform native implementation is missing, you may add it — but ONLY after source-verifying EVERY native symbol against the OTHER platform's cached native source (`~/.cache/clevertap-sdk-versions/...`, Read/Grep tools). If that platform's source is not in the cache at the relevant version, or the symbol cannot be confirmed, do NOT write it — add it to `flagged_for_review` (type `unconfirmed`) describing exactly which platform's bridge is missing which method. A flagged gap is recoverable; a guessed selector is a broken build.

## Handling native method overloads

Native SDKs sometimes ship overloads (e.g. `foo()` and `foo(arg)`). The established Cordova pattern: **one JS method with an optional trailing parameter / optional callback**; the native side null-checks and routes. Surface BOTH overloads under a single JS method — do NOT defer this. Defer ONLY when the native callback delivers a custom struct with undocumented fields, or the API needs a builder / multi-step setup that doesn't fit `(args..., optional param)`.

## Source verification — MANDATORY before writing ANY native call

The single biggest source of broken builds is calling a native method/selector that doesn't exist. The rule:

**Before you write ANY call to a native SDK symbol (in `CleverTapPlugin.java` or `CleverTapPlugin.m`), confirm its exact name and signature in the cached native source at the NEW version.** The diff tool already downloaded it to `~/.cache/clevertap-sdk-versions/<repo>-<tag>/` (e.g. `clevertap-android-sdk-corev${NEW_VERSION}` / `clevertap-ios-sdk-${NEW_VERSION}`).

- **Android:** check `clevertap-core/src/main/java/com/clevertap/android/sdk/CleverTapAPI.java` (or the class the diff names).
- **iOS:** check `CleverTapSDK/CleverTap.h` and its category headers (`CleverTap+Inbox.h`, `CleverTap+DisplayUnit.h`, …). ObjC selectors include every part: `recordChargedEventWithDetails:andItems:` is NOT `recordChargedEventWithDetails:items:`.

**HOW to check — use the Read / Grep / Glob TOOLS, not Bash.** Bash commands that reference paths outside your working directory are DENIED by the permission system; the Read/Grep/Glob tools work on any absolute path. If a Bash grep on `~/.cache/...` gets denied, that is your cue to use the Grep tool instead — do NOT proceed unverified.

This applies to every method you implement (from the diff or the recall pass), to native calls in code that ALREADY exists in files you're completing, and to the other platform's bridge code if you touch it.

**If you cannot find the symbol in the native source, do NOT write the call.** Put the item in `flagged_for_review` (type `unconfirmed`) with what you looked for and where. A flagged item is recoverable by the reviewer; a guessed selector is a broken build.

Record the outcome per surfaced item via `"source_verified": true|false` in your structured output.

## Constraints — strict

- **Do not ask questions.** Auto-decide and record it.
- **Do not invent APIs.** Only surface what's in `api_diff` or confirmed in source during the recall pass.
- **Never guess a native symbol.** Source verification (above) is mandatory for every native call you write or complete.
- **Do not touch the Ionic/awesome-cordova-plugins typings** — that's a separate repo / workflow.
- **Do not "improve" surrounding code.** Touch only what the patterns require.
- **Do not commit or push.** The wrapping CI handles git. You only modify the working tree.
- **Cost-aware:** keep token usage reasonable — but this NEVER means skipping required steps. Finish the job, then emit.

## Before you emit — completion gate (MANDATORY)

You are **NOT done** until every item below is true. **Before emitting the structured JSON, re-open each file and verify** — do not rely on memory. If anything is missing or partial, **do it now**, then re-check.

For each API in your `surfaced` list:
- [ ] **JS** — `CleverTap.prototype.<action>` in `www/CleverTap.js`.
- [ ] **Android** — enum constant in `CleverTapFunction.java` + `case` in `CleverTapPlugin.java` `execute()` + private method in `CleverTapPlugin.java`.
- [ ] **iOS** — declaration in `CleverTapPlugin.h` + implementation in `CleverTapPlugin.m`.
- [ ] **Every native symbol it calls was source-verified** (`source_verified: true`) — or the item lives in `flagged_for_review`, not `surfaced`.
- [ ] **Example demo** added in **all 4 sample apps** (see step 4b).

Version bump (from `version-detection`) — every one of these must be edited:
- [ ] `plugin.xml` — top `version="..."` **and** this platform's native pin (`clevertap-android-sdk:` / `CleverTap-iOS-SDK` spec).
- [ ] `package.json` (`"version"`).
- [ ] `src/android/CleverTapPlugin.java` (`libVersion` integer).
- [ ] `src/ios/CleverTapPlugin.m` (`libVersion` integer).
- [ ] `README.md` "Supported Versions" line for this platform.

Changelog:
- [ ] `CHANGELOG.md` — a new dated entry at the TOP.

Only after all boxes are genuinely satisfied (verified by re-reading), emit the JSON below. If you bumped the wrapper version anywhere, ALL plugin-version locations (incl. both `libVersion` files) must reflect the same new version (no partial bumps).

## Output — required

At the end, write a structured JSON log to stdout (CI captures it to `claude-output-${PLATFORM}.json`). Schema:

```json
{
  "platform": "${PLATFORM}",
  "module": "${MODULE}",
  "old_version": "<resolved>",
  "new_version": "${NEW_VERSION}",
  "surfaced": [
    {"name": "<method_name>", "rationale": "<one sentence>", "files_touched": ["..."], "source_verified": true}
  ],
  "skipped": [
    {"name": "<method_name>", "rationale": "<one sentence>"}
  ],
  "deferred": [
    {"name": "<method_name>", "rationale": "<one sentence>", "next_step": "<what a human should do>"}
  ],
  "flagged_for_review": [
    {"type": "removal|deprecation|signature|behavior|unconfirmed", "name": "<api or feature>", "changelog_version": "<v>", "rationale": "<what the changelog said and why it was NOT auto-applied>"}
  ],
  "build_propagated": [
    {"change": "minSdk 21->23", "files": ["Samples/Cordova/ExampleProject/config.xml"]}
  ],
  "version_bump": {
    "from": "5.0.0",
    "to": "5.1.0",
    "bump_type": "minor",
    "rationale": "Adds <method>(...); no breaking changes."
  },
  "docs_updated": ["CHANGELOG.md", "README.md"],
  "native_changelogs": {
    "target_version": "${NEW_VERSION}",
    "target_entry": "<paste the diff.json's target_entry verbatim>",
    "intermediate_entries": [
      {"version": "<v>", "entry": "<paste the diff.json's intermediate entry verbatim>"}
    ]
  },
  "tokens_used": <integer>,
  "cost_usd_estimate": <float>
}
```

**`native_changelogs` is required.** Copy the diff.json's `changelog` block VERBATIM into this field — the PR-description generator renders the full native release narrative from it (target version plus every intermediate version when this sync spans more than one native release).

If anything fundamentally went wrong (e.g. the diff tool failed, or the pin file was not found), still emit valid JSON with an `error` field describing what happened — let CI handle it cleanly rather than crashing.

## Tone

This run produces a PR that a human reviews. The structured log becomes the body of that PR. Write each rationale as one short sentence explaining the decision to the reviewer, in plain Cordova/host-app terms.
