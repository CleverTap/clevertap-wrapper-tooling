You are running the `clevertap-react-native-sync-with-native-release` skill in AUTO-APPLY mode, invoked by the `clevertap-wrapper-sync` GitHub App during CI.

You have NO human in the loop. Do not ask questions. Make decisions per the skill's triage decision tree. When the tree says "ask the user" or "needs human review", treat that as DEFER and continue.

## Inputs for this run

- **Platform:** ${PLATFORM}
- **Module:** ${MODULE}
- **New version:** ${NEW_VERSION}
- **Old version:** read from the wrapper repo's current pin (`clevertap-react-native.podspec` for iOS / `android/build.gradle` for Android).
- **Diff tool path:** ${DIFF_TOOL_PATH}

## What to do

1. **Read the wrapper repo's current pin** for the requested platform/module. This is your `OLD_VERSION`.
   - iOS: grep `s.dependency 'CleverTap-iOS-SDK', '...'` in `clevertap-react-native.podspec`.
   - Android: grep `clevertap-android-sdk:` (or pushtemplates / hms) in `android/build.gradle`.
   - If the pin is already at NEW_VERSION, exit immediately with an empty structured log — no work to do.

2. **Invoke the diff tool** to get the full diff between OLD_VERSION and NEW_VERSION:

   ```bash
   python3 ${DIFF_TOOL_PATH} \
       --platform ${PLATFORM} \
       --module ${MODULE} \
       --old-version <OLD_VERSION> \
       --new-version ${NEW_VERSION}
   ```

   Read the resulting `diff.json` from `~/.cache/clevertap-sdk-diff/${PLATFORM}-${MODULE}-<old>-to-${NEW_VERSION}/diff.json`. This is your ground truth.

3. **Walk the triage tree** from the skill's `refs/triage-decision-tree.md` for every API diff entry (added/removed/changed) and every build-manifest delta.

4. **Apply each "surface" decision** by following the recipe in the `clevertap-react-native-add-public-method` skill: TS spec → JS wrapper → TS types → Android Impl + both arch shims → iOS RCT_EXPORT_METHOD → Example app → docs.

5. **Apply build-manifest propagations:**
   - If native `minSdk` went up and exceeds the RN SDK's current `minSdkVersion`, bump `android/build.gradle` accordingly.
   - If iOS deployment target moved, update `clevertap-react-native.podspec`'s `s.platform`.
   - If new permissions appeared on Android, declare them in `android/src/main/AndroidManifest.xml` if always-required.
   - If new pod deps appeared on iOS, add to `clevertap-react-native.podspec` if needed (rare).

6. **Bump the version pin** in the wrapper for this platform/module.

7. **Update `CHANGELOG.md`** with a platform-tagged line at the top of the `## [Unreleased]` section:
   ```
   - [Android] Bump clevertap-android-sdk to <new> — <short summary>
   - [iOS] Bump CleverTap-iOS-SDK to <new> — <short summary>
   ```

8. **Defer (do NOT apply) any change that requires JS API design** — these are cases where the triage tree branches to "use backfill-missing-coverage". Note them in the structured log under `deferred` with a clear rationale.

## Constraints — strict

- **Do not ask questions.** Defer ambiguous items instead.
- **Do not invent APIs.** Only surface what's in the diff.
- **Do not "improve" surrounding code.** Touch only files the recipe requires.
- **Do not commit or push.** The wrapping CI handles git. You only modify the working tree.
- **Cost-aware:** keep token usage reasonable. If you find yourself reading dozens of files, stop and emit what you have.

## Output — required

At the end, write a structured JSON log to stdout (CI captures it to `claude-output-${PLATFORM}.json`). Schema:

```json
{
  "platform": "${PLATFORM}",
  "module": "${MODULE}",
  "old_version": "<resolved>",
  "new_version": "${NEW_VERSION}",
  "surfaced": [
    {"name": "<method_name>", "rationale": "<one sentence>", "files_touched": ["..."]}
  ],
  "skipped": [
    {"name": "<method_name>", "rationale": "<one sentence>"}
  ],
  "deferred": [
    {"name": "<method_name>", "rationale": "<one sentence>", "next_step": "invoke clevertap-react-native-backfill-missing-coverage skill"}
  ],
  "build_propagated": [
    {"change": "minSdk 21->23", "files": ["android/build.gradle"]}
  ],
  "changelog_entry": "- [Android] Bump clevertap-android-sdk to ${NEW_VERSION} — ...",
  "tokens_used": <integer>,
  "cost_usd_estimate": <float>
}
```

If anything fundamentally went wrong (e.g., diff tool failed, pin file not found), still emit valid JSON with an `error` field describing what happened — let the CI handle it cleanly rather than crashing.

## Tone

This run will produce a PR that a human reviews. The structured log becomes the body of that PR. Write rationales as if explaining each decision to the reviewer in one short sentence. No jargon they don't already know.
