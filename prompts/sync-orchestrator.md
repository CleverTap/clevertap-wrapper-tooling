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

## Cross-platform coordination — important

The sync workflow runs **Sync Android FIRST**, then **Sync iOS** (sequential, not parallel). They share the runner's filesystem. If Sync Android added a method to the JS layer, that file ALREADY contains the method when Sync iOS runs.

**Your job is the bridge for YOUR platform**, regardless of JS-layer state:

- Sync Android adds: Android `CleverTapModuleImpl` + both arch shims + JS wrapper + TS spec/types + CHANGELOG.
- Sync iOS adds: iOS `RCT_EXPORT_METHOD` in `CleverTapReact.mm` + CHANGELOG.
- BOTH may write to the JS wrapper / TS spec — that's fine; the second sync sees the edit already exists and is a no-op for those files.

For every method in YOUR platform's diff, even if `src/index.js` already exports it (because the other Sync just added it), **ensure your platform's bridge code is present**. Concretely:

- **iOS (you):** open `ios/CleverTapReact/CleverTapReact.mm`. For each ADDED method in the iOS diff, confirm there's a matching `RCT_EXPORT_METHOD(<name> ...)` block. If missing, ADD it. Then surface that method in your structured log (even if the JS wrapper was added by a previous sync).
- **Android (you):** open `android/src/main/java/com/clevertap/react/CleverTapModuleImpl.java` AND both arch shims. For each ADDED method in the Android diff, confirm there's a matching public method on the impl AND `@ReactMethod` / `override` declarations on the two shims. If missing, add them.

**Do not conclude "nothing to do" just because the JS layer already has the method. The JS wrapper alone is not a complete bridge — the per-platform implementation must exist on YOUR side.**

## Handling native method overloads

Native SDKs sometimes ship method overloads, e.g.:

- Android: `foo()` and `foo(SomeCallback)`
- iOS: `foo` and `fooWithCallback:`

JS has no method overloading. The established pattern in this codebase: **one JS method with an optional callback parameter.** The bridge null-checks the callback and routes to the right native overload.

Reference implementation (Android):

```java
public void fetchInbox(Callback callback) {
    CleverTapAPI cleverTap = getCleverTapAPI();
    if (cleverTap == null) {
        Log.e(TAG, ErrorMessages.CLEVERTAP_NOT_INITIALIZED);
        return;
    }
    if (callback == null) {
        cleverTap.fetchInbox();
    } else {
        cleverTap.fetchInbox((FetchInboxCallback) success ->
            callback.invoke(null, success));
    }
}
```

Reference implementation (iOS .mm):

```objective-c
RCT_EXPORT_METHOD(fetchInbox:(RCTResponseSenderBlock)callback) {
    if (callback == NULL) {
        [[CleverTap sharedInstance] fetchInbox];
    } else {
        [[CleverTap sharedInstance] fetchInboxWithCallback:^(BOOL success) {
            callback(@[[NSNull null], @(success)]);
        }];
    }
}
```

JS surface: `CleverTap.fetchInbox(callback?)` — host apps call it with or without a callback. Same shape on both platforms.

**Surface BOTH overloads under a single JS method with optional callback.** Don't defer the callback overload citing "needs JS API design" — the pattern is established and the (error, value) Node-style callback shape is derivable from the native callback's argument type.

When you encounter an overload pair in the diff, BOTH go in your `surfaced` list, with the rationale "overload pair handled via single JS method with optional callback parameter."

**Defer ONLY when:**
- The native callback delivers a custom struct/object with multiple fields whose meaning isn't documented in the native header (genuinely ambiguous JS shape).
- The native method takes a Builder, configuration object, or other multi-step setup that doesn't fit `(args..., optional callback)`.

## Constraints — strict

- **Do not ask questions.** Defer ambiguous items instead.
- **Do not invent APIs.** Only surface what's in the diff.
- **Do not "improve" surrounding code.** Touch only files the recipe requires.
- **Do not commit or push.** The wrapping CI handles git. You only modify the working tree.
- **Cost-aware:** keep token usage reasonable. If you find yourself reading dozens of files, stop and emit what you have.
- **Defer judiciously.** Defer ONLY when the JS API shape is genuinely ambiguous — complex struct callbacks with undocumented fields, builder patterns, multi-method interaction patterns. Do NOT defer cases where the decision tree gives a concrete answer (overloads → optional callback; async with completion handler → Promise<T> or optional callback). Defer is a fallback for genuinely hard cases, not a default for "this looks a bit different."

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
