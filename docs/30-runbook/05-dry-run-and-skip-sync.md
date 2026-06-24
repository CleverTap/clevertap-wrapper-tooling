# Dry-run and skip-sync — testing safely

> Real syncs cost money (the AI) and touch protected branches. This page shows the safe ways to
> *practice* and *test*: the `skip_sync` flag, a `base_ref` test baseline, and fork testing.

---

## `skip_sync = true` — builds only, $0 AI

The cheapest test. When `skip_sync` is `true`, the run:

- **still** runs the **pre-sync build** (to check the pipeline compiles), but
- **skips** the AI Sync steps and the post-sync build.

That means **$0 of AI cost** and a few minutes of CI time. Use it to iterate on the build pipeline —
e.g. when a new toolchain version breaks the example app build — without paying for the Brain.

> ### 🟦 Beginner sidebar: why iterate with skip_sync?
> Build-pipeline problems (a missing config file, a dependency version) have nothing to do with the
> AI. Fixing them by repeatedly running the full sync would waste money on the AI each time.
> `skip_sync` lets you loop on just the build, free. See [Glossary → Soft cap / cost](../GLOSSARY.md).

**How:** in the [trigger form](./02-trigger-a-sync.md), set `skip_sync` = `true`. Pick a real version
pair so the pre-sync build is meaningful.

---

## `base_ref` — test against a baseline branch

`base_ref` controls which branch the run syncs *from* and opens the PR *against*. For production you
leave it at the default integration branch. For testing, point it at a **baseline branch** — a branch
you've prepared to represent an "old" state you want to sync forward from.

This lets you exercise a real old→new gap (e.g. pin rolled back to `8.1.0`, sync to `8.2.0`) without
touching the integration branch at all.

> ### ⚠️ Old release *tags* often don't make good baselines
> A tempting idea is "just check out an old release tag and sync from there." In practice, old tags
> frequently **don't build on today's toolchain** (compiler/Gradle/CocoaPods drift). The reliable
> pattern is a baseline **branch** based on current `develop` with the version pins *rolled back* —
> it builds today, and represents the old state for the diff.

> ### ⚠️ When you hand-make a baseline, mind the lockfiles
> If your baseline changes an iOS pin, delete the relevant `Podfile.lock` yourself (a stale lock
> conflicts with a changed podspec). The automatic post-sync path handles this in a real run, but a
> hand-built baseline is on you.

---

## Fork testing — the full safe sandbox

The most complete test runs the *entire* pipeline on a **personal fork** of the wrapper repo, where
every branch is unprotected and any PR the run opens is harmless. The hub's **`TESTING.md`** is the
authoritative, step-by-step procedure. The shape of it:

1. **Fork** the wrapper repo to your account.
2. Push a branch carrying the **dispatch workflow** (`native-release-sync.yml`) + `CODEOWNERS`.
3. Set the fork's **default branch** to that branch so the **Run workflow** button appears in the UI.
4. **Install** the `clevertap-wrapper-sync` App on the fork and add the **four secrets** to the fork.
5. **Run** — first with both modules `none` or `skip_sync=true` to confirm the workflow loads, then
   with a real version pair for a full end-to-end test.

A green fork run produces a branch, a PR against the fork's base branch (authored by
`clevertap-wrapper-sync[bot]`), the structured PR body, green builds, and a cost report — exactly
like production, but disposable.

> ### 🟦 Beginner sidebar: why a fork?
> The real repo's integration branch is **protected** — you can't merge without approval, and you
> can't get approval without proving the workflow works. A fork breaks that chicken-and-egg: every
> branch is unprotected, so you can test freely, then copy the proven workflow to the real repo via a
> normal PR. See `TESTING.md` in the hub.

> ### ⚠️ The App on a fork can't touch the real repo
> A GitHub App only has permissions on the repos it's *installed* on. Installing it on your fork
> grants nothing on the real repo. All test pushes/PRs stay on the fork.

---

## Which test should I use?

| Situation | Use |
|---|---|
| The example build broke (toolchain bump, missing config). | **`skip_sync=true`** — loop on the build, $0 AI. |
| You want to test a real old→new sync without touching `develop`. | **`base_ref`** pointing at a baseline branch. |
| You want a full, end-to-end rehearsal before going to production. | **Fork testing** per `TESTING.md`. |

---

## ✅ Check yourself

<details>
<summary>1. What does <code>skip_sync=true</code> still run, and what does it skip?</summary>

It **still runs the pre-sync build** (so you can iterate on the build pipeline), but **skips** the AI
Sync steps and the post-sync build — so it costs **$0 of AI**.
</details>

<details>
<summary>2. Why prefer a rolled-back baseline *branch* over an old release *tag* for testing?</summary>

Old tags often **don't build on today's toolchain** (compiler/Gradle/CocoaPods have moved on). A
baseline branch off current `develop` with the version pins rolled back builds today *and* represents
the old state for the diff.
</details>

<details>
<summary>3. Why is fork testing safe for the real repo?</summary>

A GitHub App only has permissions on repos it's installed on. On a fork, every branch is unprotected
and any PR the run opens lives on the fork — it can't touch the real repo. You only graduate to the
real repo by copying the proven workflow via a normal, reviewed PR.
</details>

**Next:** [Troubleshooting → 01 — failure modes →](../40-troubleshooting/01-failure-modes.md)
