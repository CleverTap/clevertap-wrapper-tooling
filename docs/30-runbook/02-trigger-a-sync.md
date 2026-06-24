# Trigger a sync — click by click

> You have [the prerequisites](./01-prerequisites.md). Now let's actually click the button. This
> page walks the form field by field, in plain English.

---

## The clicks

1. Open the **wrapper repo** on GitHub (e.g. `clevertap-cordova`).
2. Click the **Actions** tab (top of the repo page).
3. In the left sidebar, click **native-release-sync**.
4. On the right, click the **Run workflow** dropdown button.
5. A small form drops down. Fill it in (next section), then click the green **Run workflow** button.

That's it — the run starts. The next page, [03 — read the run](./03-read-the-run.md), shows you how
to watch it.

> ### 🟦 Beginner sidebar: why a "Run workflow" button exists
> The dispatch workflow is set to trigger on `workflow_dispatch`, which means "run when a human
> clicks the button" (a manual run). That's what puts the **Run workflow** button in the UI. See
> [Glossary → `workflow_dispatch`](../GLOSSARY.md).

---

## The form, field by field

You don't fill in every field — you pick the platform(s) you're syncing and leave the rest at
defaults.

| Field | Plain English | Typical value |
|---|---|---|
| **`android_module`** | Which Android native module to sync. Pick `none` to skip Android entirely. | `core` (or `none`) |
| **`android_version`** | The Android version to sync *to*. Leave empty if `android_module` is `none`. | e.g. `8.2.0` |
| **`ios_module`** | Which iOS native module to sync. Pick `none` to skip iOS. | `core` (or `none`) |
| **`ios_version`** | The iOS version to sync *to*. Leave empty if `ios_module` is `none`. | e.g. `7.7.1` |
| **`release_name`** | A suffix for the branch the run creates (`task/release_<name>`). Defaults to today's date if left empty. | leave empty, or e.g. `2026-06-16` |
| **`base_ref`** | Which branch to sync *from* and open the PR *against*. Defaults to the integration branch. | leave at default for production |
| **`model`** | Which AI model leads the reasoning. | `sonnet` (default) |
| **`skip_sync`** | If `true`, skip the AI sync + post-sync build (builds only, $0 AI). | `false` for a real sync |

> ### 🟦 Beginner sidebar: module
> A native SDK is split into **modules** — Android has `core`, `pushtemplates`, `hms`; iOS has
> `core`, `pushtemplates`. Each is versioned separately, so you sync one at a time. See
> [Glossary → Module](../GLOSSARY.md).

---

## Common combinations

**Sync Android only** (an Android-only release):
- `android_module` = `core`, `android_version` = `8.2.0`
- `ios_module` = `none`, `ios_version` = empty

**Sync both platforms** (both natives released):
- `android_module` = `core`, `android_version` = `8.2.0`
- `ios_module` = `core`, `ios_version` = `7.7.1`

**Just test the build pipeline** (no AI, $0): set `skip_sync` = `true`. Covered in detail in
[05 — dry-run and skip-sync](./05-dry-run-and-skip-sync.md).

---

## Field notes worth knowing

- **Leave the other platform at `none`.** One run handles Android-only, iOS-only, or both — just set
  the platform you're *not* syncing to `none` and leave its version empty.

- **Sync to a version that actually differs from the current pin.** If you ask Claude to sync to the
  version already pinned, it correctly does **nothing** ("no work to do"). That's by design, but it
  means a no-op run won't show you the full pipeline.

- **Use a unique `release_name` if you're retrying.** The run creates a branch
  `task/release_<release_name>`. If that branch already exists from a previous failed run, the run
  bails. Pass a fresh `release_name` to retry without colliding.

- **`base_ref` is your testing lever.** For production, leave it at the default integration branch.
  For testing, point it at a baseline branch (see [05](./05-dry-run-and-skip-sync.md)).

- **`model` defaults to `sonnet`.** Use the alias (`sonnet` / `opus` / `haiku`), not a versioned id.
  Claude also uses a cheaper model internally for small auxiliary calls regardless of your choice.

> ### ⚠️ Gotcha: model names are aliases
> The CLI accepts `sonnet` / `opus` / `haiku` (or a full versioned id). A half-name like `sonnet-4-6`
> (missing the proper prefix) is rejected. Stick with the plain alias.

---

## ✅ Check yourself

<details>
<summary>1. You want to sync only iOS core to 7.7.1. What do you put in the Android fields?</summary>

Set **`android_module` = `none`** and leave **`android_version` empty**. Then `ios_module` = `core`
and `ios_version` = `7.7.1`. One run cleanly handles a single-platform sync.
</details>

<details>
<summary>2. You ran a sync, it failed halfway, and a <code>task/release_…</code> branch is stuck. How do you retry cleanly?</summary>

Pass a **unique `release_name`** on the retry. The run creates `task/release_<release_name>`; if that
branch already exists it bails, so a fresh name avoids the collision.
</details>

<details>
<summary>3. What happens if you sync to the version already pinned?</summary>

Claude correctly detects there's nothing to do and exits ("no work to do"). To exercise the full
pipeline, pick a version that differs from the current pin.
</details>

**Next:** [03 — read the run (watch it and understand each step) →](./03-read-the-run.md)
