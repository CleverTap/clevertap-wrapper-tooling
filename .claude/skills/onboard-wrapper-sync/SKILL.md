---
name: onboard-wrapper-sync
description: >
  Playbook for adding a NEW CleverTap hybrid wrapper SDK (e.g. Cordova, Unity)
  to the shared native-release sync automation. Use when wiring up a new wrapper
  repo so its maintainers can one-click sync the wrapper with new native Android/
  iOS SDK releases. Covers the per-wrapper contract, step-by-step onboarding, and
  the gotchas learned from React Native and Flutter.
---

# Onboarding a new wrapper to the native-release sync

This repo (`CleverTap/clevertap-wrapper-tooling`) is the shared engine that syncs CleverTap hybrid wrappers (React Native, Flutter, … Cordova next) with new native SDK releases. A maintainer clicks one button in the wrapper repo, Claude runs headless in CI, and a structured PR opens. This skill is how you onboard the **next** wrapper.

**Reference implementations:** Flutter is the freshest and closest to current design (`prompts/sync-orchestrator-flutter.md`, `.github/actions/build/flutter/`). React Native is the original (`prompts/sync-orchestrator.md`, `.github/actions/build/react-native/`). Read one of them alongside this skill — onboarding a new wrapper is mostly "do what Flutter did, swap the wrapper-specific parts."

## How the system is shaped

- **`.github/workflows/sync.yml`** — a thin **conductor** (reusable `workflow_call`). It runs shared composite actions and **branches on `inputs.wrapper`** only where the work is wrapper-specific (the build, the prompt, the tool allowlist, artifact paths).
- **Composite actions** (`.github/actions/`): `setup` (token, checkout, branch, Claude CLI), `claude-sync` (one headless `claude -p` per platform), `open-pr` (PR body + labels + `gh pr create`) — all **shared**; and `build/<wrapper>/` — **per wrapper**.
- **`tools/diff_native_api.py`** — wrapper-agnostic native SDK differ (API + build manifest + verbatim changelog). Reused as-is by every wrapper.
- **`prompts/sync-orchestrator-<wrapper>.md`** — the per-wrapper headless "auto-pilot" that reads the wrapper's `.claude/skills/` and applies changes. **`prompts/pr-description.md`** is shared.
- **The wrapper repo** supplies the domain knowledge: `.claude/skills/` (version locations, API-wrapper patterns, example-app patterns, changelog format) + the dispatch workflow.

## The per-wrapper contract

To support wrapper `X`, these five things must exist and agree:
1. **Dispatch** `X-repo/.github/workflows/native-release-sync.yml` with `wrapper: X` and `uses: CleverTap/clevertap-wrapper-tooling/.github/workflows/sync.yml@v1`.
2. **Build composite** `.github/actions/build/X/action.yml` — installs the toolchain and builds the example app for android/ios; exposes `android_outcome` / `ios_outcome` outputs; **swallows build failures** (exit 0, report via output) so the conductor decides.
3. **Conductor wiring** in `sync.yml`: `if: inputs.wrapper == 'X'` pre- and post-sync build steps, the prompt+allowlist branch in the `Resolve Claude config` step, and the artifact-upload paths.
4. **Prompt** `prompts/sync-orchestrator-X.md` (incl. the mandatory Example-demo step 4b).
5. **Domain skills** in `X-repo/.claude/skills/` — **committed to the `base_ref` branch the sync checks out** (incl. an example-app skill).

## Step-by-step (worked example: Cordova)

1. **GitHub App + secrets.** Install the `clevertap-wrapper-sync` App on the wrapper repo (and its test fork). Add 4 secrets: `CLEVERTAP_WRAPPER_SYNC_APP_ID`, `CLEVERTAP_WRAPPER_SYNC_PRIVATE_KEY`, `ANTHROPIC_API_KEY`, `SLACK_WEBHOOK_URL`.

2. **Dispatch workflow.** Copy Flutter's `native-release-sync.yml` into the wrapper repo; set `wrapper: cordova`; keep `uses: CleverTap/clevertap-wrapper-tooling/.github/workflows/sync.yml@v1`. Keep the inputs (`android_module/version`, `ios_module/version`, `release_name`, `base_ref`, `model`, `skip_sync`).

3. **Build composite** `.github/actions/build/cordova/action.yml`. Mirror `build/flutter`: inputs `phase` + `android_version` + `ios_version` + `wrapper_path`; outputs `android_outcome`/`ios_outcome`. Use Cordova's real build commands (e.g. `cordova platform add/build android`, `cordova build ios`). Include any "missing generated file" stubs the example needs (Flutter needs a `google-services.json` stub; check what Cordova needs). For iOS, delete the example `Podfile.lock` in the post-sync phase if the pin changed.

4. **Wire `sync.yml`.** Add the four `if: inputs.wrapper == 'cordova'` build steps (pre/post × … one composite call each, both platforms), a `cordova` branch in `Resolve Claude config` (set `prompt` = `prompts/sync-orchestrator-cordova.md` and the `allowed_tools` — include the diff tool + read/edit/git + Cordova's CLIs; exclude WebFetch/WebSearch), and the artifact-upload paths for Cordova's APK/app.

5. **Prompt** `prompts/sync-orchestrator-cordova.md`. Clone `sync-orchestrator-flutter.md` and swap the wrapper-specific parts: the layer/recipe references (Cordova's JS plugin layer + Android/iOS bridges), the version-location list, and the example-app demo location. **Keep verbatim**: the "no human / proceed" override; the diff-tool-as-ground-truth instruction; the **step-3b changelog recall pass** (source-verify, then act; behavior-only/unconfirmable → `flagged_for_review`); the **mandatory Example-app demo step (4b)** (example file required in each surfaced item's `files_touched`); **step-anchored progressive skill invocation** (invoke each skill via the Skill tool *at the step that needs it* — do NOT pre-read all skills upfront); the **end-of-run completion gate** (a "you are NOT done until…" checklist listing every version file + CHANGELOG + example demo, verified by re-reading before emitting); and the structured-output schema incl. `flagged_for_review` and `native_changelogs`.

6. **Domain skills** in the Cordova repo's `.claude/skills/`: a `version-detection` equivalent (where Cordova's version pins + own version live), an `api-wrapper-patterns` equivalent (how to add a method across Cordova's layers), an `example-app` equivalent (how to add a runnable demo for each API — every surfaced method MUST get one), and a `changelog-generation` equivalent. **Commit these skills to the branch the sync checks out (`base_ref`, default `develop`)** — the headless run reads skills from the checked-out wrapper repo, NOT from anyone's laptop. If they're only local/untracked, Claude can't read them and silently falls back to the prompt text (this is exactly how RN's Example demos got skipped before they were committed).

7. **Test on a fork.** Fork the wrapper repo; push the dispatch to a branch and make it the fork's **default branch** (so the `workflow_dispatch` UI/CLI sees it); ensure the fork has the branch the sync checks out (`develop` by default, or pass `base_ref`). Run **`skip_sync=true`** first (validates the build composite + wiring at $0 Claude). Then a full run. If the wrapper is already at the latest native version (no gap), create a **`develop`-based baseline with rolled-back pins** (and optionally hand-remove a couple of recently-added wrapper methods) and pass it via `base_ref`.

## Cross-wrapper gotchas checklist
- **`uses:` does NOT follow org redirects** — reference `CleverTap/clevertap-wrapper-tooling@v1` directly; a moved/renamed owner 422s the dispatch.
- **Old release tags often don't build on the current toolchain** (e.g. Flutter's "Built-in Kotlin" migration; stale CocoaPods constraints). For realistic tests use **`develop` + rolled-back pins**, not an old tag.
- **Changing the iOS pin ⇒ regenerate Pods** — delete the example `Podfile.lock` or `pod install` fails with "specs too out-of-date".
- **Generated/build files leak into PRs** — gitignore them in the wrapper repo (Flutter: `example/ios/Flutter/ephemeral/`).
- **Unique `release_name` per run** — the conductor bails if `task/release_<name>` already exists.
- **Headless Claude can't read files outside its cwd** — the PR-body prompt has the sync logs inlined for this reason; don't switch it back to path-passing.
- **Wrapper skills must be committed to the `base_ref` branch** — the CI runner is a fresh VM and checks out the wrapper at `base_ref`; it never sees your laptop. If a referenced skill isn't in that checkout, Claude silently proceeds on prompt text alone (how RN's Example demos got skipped). Commit the skills, or keep the prompt self-contained for critical steps.
- **Never add `--bare` to the `claude -p` call** — it skips auto-discovery of the wrapper's `.claude/skills`, disabling skill invocation. Non-bare loads them like an interactive run (that's what we want).
- **The model can voluntarily stop before finishing** (`stop_reason:"end_turn"`, `subtype:"success"`) even with plenty of context left and no turn/cost cap — it "satisfices". This is why the prompt MUST end with the completion gate, and why `open-combined-pr.sh` runs a deterministic completeness check: if the committed diff is missing `CHANGELOG.md` or the wrapper's canonical version file, it adds an `incomplete-sync` label + ⚠️ banner (non-blocking). Bigger-context models do NOT fix this (the failure isn't context exhaustion).
- **Inspect the step trace** — runs upload `claude-stream-*.jsonl` (full tool-call transcript) and print a trace in the Actions log; check it to confirm Claude actually read the skills / touched the Example app. This is free (formatting only — no extra tokens).
- **`gh run watch` is flaky on slow networks** — prefer a resilient poll loop.
- **Soft cost cap is informational only** — it posts a PR comment over the threshold; it does NOT abort. Add a real guardrail (between-platform hard stop + `--max-turns`) if you need one.
- **Cross-run shape variance** — independent Claude runs may produce slightly different (still-correct) wrapper shapes; the human PR review is the gate.

## Pointers
- Reference impl (current): Flutter — `prompts/sync-orchestrator-flutter.md`, `.github/actions/build/flutter/action.yml`, and `CleverTap/clevertap-flutter/WRAPPER_SYNC_HANDOFF.md`.
- Original: React Native — `prompts/sync-orchestrator.md`, `.github/actions/build/react-native/action.yml`.
- Test procedure: `TESTING.md` (this repo).
