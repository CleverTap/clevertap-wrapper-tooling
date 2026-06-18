# Failure modes — symptom → cause → fix

> Things break. This page is the map of the *common* breakages, each as **symptom → cause → fix**.
> Most aren't real emergencies — several are by design.

For a quick read of *where* in the run a failure happened, keep
[03 — read the run](../30-runbook/03-read-the-run.md) handy.

---

## 1. The run aborts at the pre-sync build gate

**Symptom:** the run stops early, at "Pre-sync build." No Sync steps ran. No PR. Cost is $0.

**Cause:** the example app was **already broken** on `base_ref`, *before* any AI changes. The
pre-sync gate exists exactly to catch this and fail fast.

**Fix:** this isn't a sync problem — it's a build-pipeline problem. Fix the build first:

- Iterate with **`skip_sync=true`** so each attempt costs $0 AI (see
  [05 — dry-run and skip-sync](../30-runbook/05-dry-run-and-skip-sync.md)).
- Common culprits seen before: a missing `google-services.json` (the Google Services plugin needs it
  even without Firebase — CI writes a stub), a stale lockfile fighting a strict install, or a
  toolchain/SDK-level drift.

> 🧠 **Analogy:** the gate is a **smoke detector that won't let you start cooking** if the kitchen's
> already on fire. Annoying, but it saved you the cost of a doomed AI run.

---

## 2. The PR opened with a `build-failed` label

**Symptom:** a PR exists, but it carries a **`build-failed`** label and a warning banner. The run is
marked failed and Slack may have pinged.

**Cause:** the **post-sync** build failed — Claude's edits didn't compile. By design ("Option A") the
PR opens anyway rather than throwing the work away.

**Fix:** this is **non-fatal and expected sometimes**. A human:

1. pulls the branch locally,
2. fixes the compile error,
3. pushes — the PR updates,
4. then reviews and merges as normal.

A classic example: an edit that referenced a native method/selector that doesn't actually exist (see
[02 — when Claude misses an API](./02-when-claude-misses-an-api.md) and
[03 — source verification failures](./03-source-verification-failures.md)).

---

## 3. A no-op commit / "nothing happened"

**Symptom:** the Sync step ran and succeeded, but there's no meaningful diff — or no PR worth
opening.

**Cause:** you asked to sync to a version **already pinned** in the wrapper. Claude correctly detects
there's no work to do and exits cleanly. This is *correct behavior*, not a bug.

**Fix:** pick a target version that actually **differs** from the current pin. To see the full
pipeline, sync forward to a genuinely newer version (or use a rolled-back
[`base_ref` baseline](../30-runbook/05-dry-run-and-skip-sync.md)).

---

## 4. The run failed at setup (no PR, often a Slack ping)

**Symptom:** the run dies in the **Setup** step, before any build or sync. Often the token-minting
sub-step is red.

**Causes & fixes:**

| Cause | Fix |
|---|---|
| **App private key newlines mangled** → `Invalid keyData`. | Re-paste the `.pem` with exact bytes (`cat key.pem \| pbcopy`); verify the key is valid before saving the secret. |
| **GitHub App not installed** on the target repo (or fork). | Install `clevertap-wrapper-sync` on that repo with access to it. |
| **A required secret is missing.** | Confirm all four secrets exist (Settings → Secrets → Actions). The Slack one is optional — the script skips gracefully when empty. |
| **Branch already exists** (`task/release_<name>`) from a prior failed run. | Re-run with a unique **`release_name`**. |
| **`uses:` points at a stale/wrong hub location.** | The dispatch's `uses:` must point at the current hub path + tag (e.g. `@v1`); note `uses:` does **not** follow org redirects. |

> ### 🟦 Beginner sidebar: token minting
> The first thing setup does is ask the GitHub App for a short-lived **token**. If the App isn't
> installed or its key is malformed, this fails immediately and nothing else can run. See
> [Glossary → GitHub App / Token](../GLOSSARY.md).

---

## Quick triage table

| What you see | Most likely | Where to go |
|---|---|---|
| Stopped at pre-sync build, $0 cost | Build broken before any sync | This page §1; [skip-sync](../30-runbook/05-dry-run-and-skip-sync.md) |
| PR with `build-failed` label | Claude's edits didn't compile | This page §2; [source verification](./03-source-verification-failures.md) |
| Sync ran but no real change | Synced to the already-pinned version | This page §3 |
| Died in Setup / Slack ping, no PR | Token/App/secret/branch issue | This page §4 |
| A changelog method seems missing | Diff regex miss / unconfirmed | [02 — when Claude misses an API](./02-when-claude-misses-an-api.md) |

---

## ✅ Check yourself

<details>
<summary>1. The run stopped at pre-sync build with $0 cost. Is this a sync bug?</summary>

No — it's the **build pipeline** that was already broken on `base_ref`. The pre-sync gate fails fast
to avoid paying for AI on a doomed run. Fix the build (iterate with `skip_sync=true`), then retry.
</details>

<details>
<summary>2. A PR opened with a <code>build-failed</code> label. Emergency?</summary>

No — it's the expected "Option A" behavior. Claude's edits didn't compile, so the PR opens anyway for
a human to pull, fix, push, and merge. Nothing was lost.
</details>

<details>
<summary>3. Setup failed with <code>Invalid keyData</code>. What's the cause?</summary>

The GitHub App **private key's newlines were mangled** when pasted into the secret. Re-paste the
exact `.pem` bytes and verify the key before saving.
</details>

**Next:** [02 — when Claude misses an API →](./02-when-claude-misses-an-api.md)
