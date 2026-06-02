# clevertap-wrapper-tooling

Shared automation for syncing CleverTap wrapper SDKs (React Native first; Flutter, Unity, Cordova later) with new releases of the underlying native iOS and Android SDKs.

This repo holds:

- A reusable GitHub Actions workflow that each wrapper repo calls.
- A Python tool that diffs the public API surface, build manifest, and changelog of a CleverTap native SDK between two tagged versions.
- The prompts and shell helpers used to drive Claude in headless mode during CI.

## What it does

When the wrapper team's maintainer clicks the "native-release-sync" workflow button in a wrapper repo's Actions tab, this tooling:

1. Mints a short-lived token via the `clevertap-wrapper-sync` GitHub App.
2. Checks out the wrapper repo at `develop`, creates a branch `task/release_<release-name>`.
3. Runs Claude headless with the wrapper's sync skill in `--auto-apply` mode.
4. Claude diffs the native SDKs, walks the triage decision tree, applies surfaceable changes, defers anything ambiguous, propagates build-manifest changes (minSdk, deployment target, new permissions).
5. Runs lint + Example app build on both platforms. On code-level failure, asks Claude to self-heal (max 3 attempts).
6. Opens a PR against `develop` with a structured description: surfaced / skipped / deferred / build manifest / cost.
7. If self-heal exhausts or hits a non-recoverable error, posts to Slack instead.

The maintainer's only job is clicking "Run workflow" and reviewing the PR.

## Layout

```
.
├── README.md
├── tools/
│   └── diff_native_api.py       # Diffs native SDKs (API + build manifest + changelog).
│                                # Canonical copy; wrapper repos may keep a mirror
│                                # for local sync skill invocations.
├── .github/workflows/
│   └── sync.yml                 # The reusable workflow (workflow_call entry).
├── prompts/
│   ├── sync-orchestrator.md     # Headless Claude prompt for the sync skill.
│   ├── self-heal.md             # Code-level retry prompt for lint/build failures.
│   └── pr-description.md        # Template Claude fills for the PR body.
└── scripts/
    ├── run-with-self-heal.sh    # Wraps a command in the 3-retry loop.
    ├── compute-cost.sh          # Sums Claude tokens, posts soft-cap PR comment.
    ├── open-combined-pr.sh      # Generates PR body + opens PR.
    └── slack-notify.sh          # POST to Slack on non-recoverable failure.
```

## Calling this workflow from a wrapper repo

Each wrapper repo adds a thin dispatch workflow that calls this one. Example for React Native:

```yaml
# .github/workflows/native-release-sync.yml in clevertap-react-native
name: native-release-sync
on:
  workflow_dispatch:
    inputs:
      android_module:   { type: choice, options: [none, core, pushtemplates, hms], default: core }
      android_version:  { type: string }
      ios_module:       { type: choice, options: [none, core, pushtemplates], default: core }
      ios_version:      { type: string }
      release_name:     { type: string }

jobs:
  sync:
    uses: piyush-kukadiya/clevertap-wrapper-tooling/.github/workflows/sync.yml@v1
    with:
      wrapper:         react-native
      android_module:  ${{ inputs.android_module != 'none' && inputs.android_module || '' }}
      android_version: ${{ inputs.android_version }}
      ios_module:      ${{ inputs.ios_module != 'none' && inputs.ios_module || '' }}
      ios_version:     ${{ inputs.ios_version }}
      release_name:    ${{ inputs.release_name }}
    secrets:
      app_id:            ${{ secrets.CLEVERTAP_WRAPPER_SYNC_APP_ID }}
      app_private_key:   ${{ secrets.CLEVERTAP_WRAPPER_SYNC_PRIVATE_KEY }}
      anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
      slack_webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Required secrets per wrapper repo

| Secret | What it's for |
|---|---|
| `CLEVERTAP_WRAPPER_SYNC_APP_ID` | GitHub App ID — public-ish, stored as secret for convention |
| `CLEVERTAP_WRAPPER_SYNC_PRIVATE_KEY` | App private key (the `.pem` contents) |
| `ANTHROPIC_API_KEY` | Existing CleverTap-org Anthropic key |
| `SLACK_WEBHOOK_URL` | Channel for failure pings |

## Running the diff tool locally

```bash
python3 tools/diff_native_api.py \
    --platform android --module core \
    --old-version 8.1.0 --new-version 8.2.0 \
    --local-path /path/to/local/clevertap-android-sdk
```

Outputs land in `~/.cache/clevertap-sdk-diff/<platform>-<module>-<old>-to-<new>/{diff.json,diff.md}`. Stdlib-only Python — no `pip install` needed.

## Ownership

This repo lives under `piyush-kukadiya/clevertap-wrapper-tooling` temporarily. It will be transferred to `CleverTap/clevertap-wrapper-tooling` once org admin access is back. After the transfer, the only file that needs updating in wrapper repos is the `uses:` line in their dispatch workflow.

## Versioning

Tag releases on this repo (`v1`, `v2`, etc.). Wrapper repos pin to a tag so an in-flight change here doesn't break someone else's auto-sync. Use `@v1` (a moving tag) for "latest v1.x" or `@v1.0.0` to pin exactly.

## Adding a new wrapper

1. Register the `clevertap-wrapper-sync` App on the new wrapper repo.
2. Copy the small dispatch workflow above into the new wrapper repo, change `wrapper:` input.
3. Add the four secrets to the new wrapper repo.
4. Write the per-wrapper sync skill (the bridge mechanics differ between RN, Flutter, Unity).
5. Click "Run workflow" once to verify.
