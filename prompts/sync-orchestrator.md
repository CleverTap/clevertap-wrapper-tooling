You are running the `clevertap-react-native-sync-with-native-release` skill in AUTO-APPLY mode, invoked by the `clevertap-wrapper-sync` GitHub App during CI.

You have NO human in the loop. Do not ask questions. Make decisions per the skill's triage decision tree. When the tree says "ask the user" or "needs human review", treat that as DEFER and continue.

## Inputs for this run

- **Platform:** ${PLATFORM}
- **Module:** ${MODULE}
- **New version:** ${NEW_VERSION}
- **Old version:** read from the wrapper repo's current pin (`clevertap-react-native.podspec` for iOS / `android/build.gradle` for Android).
- **Diff tool path:** ${DIFF_TOOL_PATH}
- **Release date:** ${RELEASE_DATE} — human-readable date (e.g. "June 5 2026") used as the CHANGELOG heading date.

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

   The diff's `changelog` block has the shape:

   ```json
   "changelog": {
     "target_version": "8.3.0",
     "target_entry": "### Version 8.3.0 ...",
     "intermediate_entries": [
       {"version": "8.2.0", "entry": "### Version 8.2.0 ..."}
     ]
   }
   ```

   When the wrapper's current pin skipped versions (e.g., 8.1.0 pin and you're syncing to 8.3.0), `intermediate_entries` lists every version strictly between. Their changelog narrative is part of the cumulative diff you're applying — read them too. **The changelog is a SECOND detection source, not just narrative:** the diff tool is regex-based (~80% coverage) and can miss real API changes (multi-line signatures, `@JvmOverloads`, Kotlin default-param methods, etc.). You'll reconcile the changelog against `api_diff` in **step 3b** to recover anything the structural diff missed.

3. **Walk the triage tree** from the skill's `refs/triage-decision-tree.md` for every API diff entry (added/removed/changed) and every build-manifest delta.

3b. **Recall pass from the changelog (catch what the regex diff missed).** For every concrete public-API change the changelog names (in `target_entry` + `intermediate_entries`) that is NOT already covered by `api_diff`, you MUST **verify it against the new native source header before acting** — Android: `CleverTapAPI.java`; iOS: `CleverTap.h` (the same files used for return-type verification; fetch at the new version). Then:
   - **New API** — symbol exists in source and not already in the JS wrapper → surface it via the `clevertap-react-native-add-public-method` recipe (step 4). Mark a type `(inferred)` if you couldn't fully confirm it.
   - **Removed** — symbol is genuinely **absent** from the new source → remove/deprecate the JS method + its native bridges (this is a **MAJOR** bump).
   - **Deprecated** — symbol is **present but marked deprecated** (`@Deprecated` / `__attribute__((deprecated))`) → KEEP it, note the deprecation in docs. Do NOT delete it.
   - **Signature changed** — source confirms a new signature → update the JS wrapper + both arch shims + the iOS `RCT_EXPORT_METHOD` (**MAJOR** if a required parameter was added).
   - **Behavior-only change** — no symbol added/removed/changed (same API, different runtime behavior) → nothing to implement; add it to `flagged_for_review`.
   - **Cannot confirm in source** (symbol not found, or ambiguous changelog wording) → do NOT guess. Add it to `flagged_for_review` with what the changelog claimed.

   Items you acted on in 3b go in `surfaced` (or `skipped`) like any other. Items you could NOT safely auto-apply — behavior-only changes and anything unconfirmable — go in `flagged_for_review` so a human reviews them.

4. **Apply each "surface" decision** by following the recipe in the `clevertap-react-native-add-public-method` skill: TS spec → JS wrapper → TS types → Android Impl + both arch shims → iOS RCT_EXPORT_METHOD → Example app → docs.

4b. **Add an Example-app demo for EVERY surfaced method — mandatory, do NOT skip.** Follow the `clevertap-react-native-example-app` skill. Concretely, for each `surfaced` item: (1) add an `Actions` key in `Example/app/constants.js`; (2) add a handler in `Example/app/app-utils.js` that calls `CleverTap.<method>(...)` with **concrete realistic values** (demo the callback form for optional-callback overloads) plus a `showToast` + `console.log`; (3) wire the action into the menu in `Example/app/App.js` so it runs on tap. The three Example files MUST appear in that item's `files_touched`. Do this even if the bridge method already existed from a prior sync — a surfaced API without an Example demo is incomplete.

5. **Apply build-manifest propagations:**
   - If native `minSdk` went up and exceeds the RN SDK's current `minSdkVersion`, bump `android/build.gradle` accordingly.
   - If iOS deployment target moved, update `clevertap-react-native.podspec`'s `s.platform`.
   - If new permissions appeared on Android, declare them in `android/src/main/AndroidManifest.xml` if always-required.
   - If new pod deps appeared on iOS, add to `clevertap-react-native.podspec` if needed (rare).
   - **Propagate to `docs/install.md`.** If you bumped the Android pin in `android/build.gradle`, also update the matching `implementation 'com.clevertap.android:clevertap-android-sdk:<old>'` line inside a sample `dependencies { }` block in `docs/install.md`. Same for iOS deployment-target / minSdk bumps if `docs/install.md` quotes those numbers. Add `docs/install.md` to your `docs_updated` output field.

6. **Bump the version pin** in the wrapper for this platform/module.

7. **Bump the wrapper's own SemVer.** The wrapper has its own version independent of the native SDK. Pick a bump type:
   - **Patch** (e.g. 4.1.0 → 4.1.1): no diff entries crossed the triage tree; tooling-only correction.
   - **Minor** (e.g. 4.1.0 → 4.2.0): the common case — you surfaced one or more additive APIs and/or build-manifest tweaks that don't break existing callers.
   - **Major** (e.g. 4.1.0 → 5.0.0): any of:
     - a `REMOVED` row applied (you deleted a public RN method);
     - a `CHANGED` row that added a REQUIRED parameter;
     - native bumped `minSdk` or iOS `s.platform` and you propagated it;
     - native CHANGELOG announced a host-impacting breaking change (default flipped, behavior change, etc.).

   Read the current wrapper version from `package.json` `"version"`. Then edit THREE files in lockstep with the NEW wrapper version:
   - `package.json`: replace the `"version"` value.
   - `android/build.gradle`: replace `versionName "<old>"` with the new string; bump `versionCode` by `+10` for a minor bump, `+100` for major, `+1` for patch. The cadence already in use is 4.0.0→400, 4.1.0→410, 4.2.0→420.
   - `src/index.js`: replace `const libVersion = <NNNNN>` with `MAJOR*10000 + MINOR*100 + PATCH` (4.2.0 → 40200).

   Emit your decision in the structured output's `wrapper_version` field (see schema).

   Note: when Sync Android runs first, it does this bump; when Sync iOS runs second, the bump is already there — verify and re-emit the same `wrapper_version` decision (don't bump twice).

8. **Update `CHANGELOG.md` — versioned block format.** Do NOT write to `## [Unreleased]`. The project uses versioned blocks at the top of the file. Read existing entries (lines 8-30 for v4.1.0, 31-44 for v4.0.0) to match the exact style. Insert the new block ABOVE the most recent existing version block, following this template:

   ```
   Version <NEW_WRAPPER_VERSION> *(${RELEASE_DATE})*
   -------------------------------------------
   **What's new**
   * **[Android Platform]**
     * Supports [CleverTap Android SDK v<ANDROID_NEW>](https://github.com/CleverTap/clevertap-android-sdk/blob/master/docs/CTCORECHANGELOG.md#version-<MAJOR><MINOR><PATCH>-<month>-<year>).
     * <user-visible feature bullet>

   * **[iOS Platform]**
     * Supports [CleverTap iOS SDK v<IOS_NEW>](https://github.com/CleverTap/clevertap-ios-sdk/blob/master/CHANGELOG.md#version-<MAJOR><MINOR><PATCH>-<month>-<day>-<year>).
     * <user-visible feature bullet>

   **API changes**  (omit this section if there are none)
   * **[Android and iOS Platform]**  (or one-platform-only if applicable)
     * Adds `<methodName>(<args>)` — <one-line purpose>.

   **Breaking Changes**  (omit if none)
   * **[Android Platform]**
     * <breaking change>
   ```

   Rules for the bullets:

   - **Symmetrize across platforms.** If a feature appears in BOTH native diffs (e.g. App Inbox Cross-Device Sync, which lands in both Android 8.2.0 and iOS 7.7.0), call it out under BOTH platforms with the same headline. Don't list it under just one.
   - **Platform-asymmetric features** (e.g. iOS-only silent-in-foreground push) go under that platform only.
   - **Headline first, detail in parenthetical.** Example: "App Inbox Cross-Device Sync — inbox state (read, deleted) syncs across a user's devices automatically. Includes a pull-to-refresh gesture in the built-in App Inbox view, throttled to once every 5 minutes."
   - **Translate native jargon into host-app terms.** Pull facts from `native_changelogs.target_entry` and `native_changelogs.intermediate_entries`, but rewrite for a JS host-app reader. Don't paste verbatim.

   If a `## [Unreleased]` heading exists in the file from a prior partial run, delete it once your versioned block is in place.

9. **Document each surfaced API in `docs/usage.md`.** For every entry in your `surfaced` list, append a new `#### <Title Case Name>` block inside the matching `## H2` section. Use these heuristics to pick the section:

   - methods with "Inbox" in the name → `## App Inbox`
   - methods with "DisplayUnit" in the name → `## Native Display`
   - methods with "Profile" / "User" in the name → `## User Profiles`
   - methods with "Event" in the name → `## User Events`
   - methods with "FeatureFlag" → `## Feature Flag`
   - methods with "ProductConfig" → `## Product Config`

   If you can't confidently place an entry, note it in `deferred` instead of guessing.

   Style mirrors existing usage.md entries:

   ```
   #### <Title Case Name>

   *Available from CleverTap React Native SDK v<NEW_WRAPPER_VERSION>.*

   <One-paragraph plain-English description. NO internals like "fires on JS
   thread", "background dispatch queue", or native-class-name leaks. For
   callback-receiving methods, explain what the callback value is and when
   it's invoked.>

   ```javascript
   CleverTap.<methodName>(<realistic, concrete values>);
   ```
   ```

   The example MUST use concrete realistic values — never placeholders like `'Unit Id'` or `{key: 'value'}`. For methods that take a property bag, demonstrate mixed types (string, number, bool) so the reader sees what's serializable.

   Add `docs/usage.md` to `docs_updated`.

10. **Defer (do NOT apply) any change that requires JS API design** — these are cases where the triage tree branches to "use backfill-missing-coverage". Note them in the structured log under `deferred` with a clear rationale.

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
  "flagged_for_review": [
    {"type": "removal|deprecation|signature|behavior|unconfirmed", "name": "<api or feature>", "changelog_version": "<v>", "rationale": "<what the changelog said and why it was NOT auto-applied>"}
  ],
  "build_propagated": [
    {"change": "minSdk 21->23", "files": ["android/build.gradle"]}
  ],
  "changelog_entry": "- [Android] Bump clevertap-android-sdk to ${NEW_VERSION} — ...",
  "wrapper_version": {
    "from": "4.1.0",
    "to": "4.2.0",
    "bump_type": "minor",
    "rationale": "Adds fetchInbox(callback?) and pushDisplayUnitElementClickedEventForID; no breaking changes."
  },
  "docs_updated": ["docs/usage.md", "docs/install.md"],
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

**`native_changelogs` is required.** Copy the diff.json's `changelog` block VERBATIM into this field. It lets the PR-description generator render the full native release narrative — target version's entry plus every intermediate version's entry (when this sync spans more than one native release). For a single-version bump, `intermediate_entries` is an empty array.

If anything fundamentally went wrong (e.g., diff tool failed, pin file not found), still emit valid JSON with an `error` field describing what happened — let the CI handle it cleanly rather than crashing.

## Tone

This run will produce a PR that a human reviews. The structured log becomes the body of that PR. Write rationales as if explaining each decision to the reviewer in one short sentence. No jargon they don't already know.
