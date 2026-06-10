# Testing the sync workflow without merging to a protected branch

The wrapper-sync workflow lives in this repo (`CleverTap/clevertap-wrapper-tooling`) but it operates on wrapper repos (`clevertap-react-native`, eventually `clevertap-flutter`, etc.) whose `develop` and `master` branches are protected. You can't merge a PR to `develop` without approval, and you can't get approval without showing the workflow works — chicken-and-egg.

This doc captures how we work around it: test on a personal fork of the wrapper repo, where every branch is unprotected. Once the workflow runs cleanly there, copy the workflow file to the real repo via a normal PR — by then it's a meaningful approval, not a blind one.

## Fork setup (already done for React Native)

We already set this up for the RN wrapper. Steps documented here so the same procedure works for Flutter / Unity later.

```bash
# 1. Fork the wrapper repo to your personal account
cd /path/to/local/clone/of/wrapper/repo
gh repo fork --clone=false --remote=true --remote-name=fork

# 2. Sync a local feature branch with the workflow file
git checkout develop
git pull origin develop              # make sure local develop matches upstream
git checkout -b task/setup-sync-automation
# (Add .github/workflows/native-release-sync.yml and .github/CODEOWNERS)
git add .github/
git commit -m "chore - add native-release-sync dispatch workflow + CODEOWNERS"

# 3. Push the feature branch to the fork (NOT origin)
git push fork task/setup-sync-automation
git push fork develop                # clean copy of develop; workflow checks this out

# 4. Set the fork's default branch to the feature branch so the
#    workflow_dispatch button shows up in the Actions UI
gh api -X PATCH /repos/<your-handle>/<repo-name> \
       -f default_branch=task/setup-sync-automation
```

After step 4, going to https://github.com/<your-handle>/<repo-name>/actions shows the `native-release-sync` workflow with a "Run workflow" button.

## Install the GitHub App on the fork too

The `clevertap-wrapper-sync` App needs to be installed on the fork (in addition to the real repo). It can be installed on multiple repos — no need to create a second App.

1. Go to the App's settings page (org settings → Developer settings → GitHub Apps → clevertap-wrapper-sync → Configure).
2. Under "Repository access", add `<your-handle>/<repo-name>` (e.g. `piyush-kukadiya/clevertap-react-native`).

Then add the four secrets to the FORK's repo settings (`Settings → Secrets and variables → Actions`):

- `CLEVERTAP_WRAPPER_SYNC_APP_ID`
- `CLEVERTAP_WRAPPER_SYNC_PRIVATE_KEY`
- `ANTHROPIC_API_KEY`
- `SLACK_WEBHOOK_URL`

Same values as you'd use in production. The Anthropic API key is the existing CleverTap-org one.

## Running a test

1. Go to https://github.com/<your-handle>/<repo-name>/actions
2. Pick `native-release-sync` from the left sidebar
3. Click "Run workflow" (top right)
4. In the dialog:
   - **Branch dropdown:** keep at `task/setup-sync-automation` (default), or pick whichever branch has the workflow YAML you want to test
   - **Inputs:**
     - First dry-run: leave `android_module` and `ios_module` as `none` to verify the workflow loads and bails cleanly.
     - Next: pick a known version pair (e.g. Android `core` + `8.1.0` against current pin `8.0.0`) to see real diff output.
5. Click "Run workflow"
6. Watch the run. The branch dropdown picks the workflow YAML; the YAML drives everything else.

## What success looks like

A green run produces:
- A new branch `task/release_<release-name>` on the fork
- A PR on the fork against `develop`
- PR description with structured sync-log sections
- PR authored by `clevertap-wrapper-sync[bot]`
- Lint + Android build + iOS Example app build all green
- Cost report at the bottom

The PR is "fake" — it lives on the fork. Close it (or merge into the fork's develop, doesn't matter). The point was proving the workflow works end-to-end.

## Iterating

The workflow YAML can be edited on the fork's feature branch freely. Each push triggers a fresh `workflow_dispatch` you can run from the UI. No PR or approval involved.

To iterate on the reusable workflow itself (this repo), edit it here, commit, push. The fork's feature workflow pins to `@v1`, which is a moving tag — force-update it as you iterate:

```bash
cd /path/to/clevertap-wrapper-tooling
# make changes...
git add .
git commit -m "..."
git push origin main
git tag -f v1
git push origin v1 --force
```

The next workflow run on the fork picks up the new `@v1`.

(Once we ship for real, switch the wrapper repos to pin a specific version like `@v1.0.0` instead of the moving `@v1` so production isn't surprised by an in-flight change.)

## Graduating to the real repo

When the workflow has run cleanly on the fork a few times:

1. Copy `.github/workflows/native-release-sync.yml` and `.github/CODEOWNERS` from the fork's `task/setup-sync-automation` branch to a feature branch in the real repo (`CleverTap/clevertap-react-native`).
2. Open a PR against `develop` (or `master`, whichever is the integration branch).
3. Request review.
4. Approver knows this has been tested on the fork and approves accordingly.
5. Merge.
6. Add the same four secrets to the real repo.
7. Install the App on the real repo.
8. From now on, the real repo's Actions tab shows `native-release-sync` and the maintainer runs it after each native release.

## Tearing down the fork

The fork is disposable. When you're done with this setup, either:

- Leave it (costs nothing, useful for future iteration).
- Delete it: `gh repo delete piyush-kukadiya/clevertap-react-native --yes`.

## Why this is safe

- All test pushes go to `fork`, never to `origin`. Branch protection on origin's `develop` would reject any accidental push anyway, but explicit remote naming is the belt-and-suspenders.
- Auto-PRs the workflow opens on the fork are against the fork's `develop`. They never touch the real repo.
- The GitHub App, when installed on the fork, only has permissions on the fork. It cannot do anything to the real repo unless also installed there with explicit consent.

## Same procedure for Flutter / Unity later

Repeat the fork → push → set-default → install App → test cycle. The same `clevertap-wrapper-sync` App and `clevertap-wrapper-tooling` reusable workflow serve every wrapper. Only the wrapper-side dispatch workflow file changes per wrapper.
