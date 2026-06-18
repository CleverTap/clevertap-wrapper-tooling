# Review the PR — read what the robot produced

> The run finished and opened a pull request. **This is the one human step that's never automated
> away.** This page teaches you to read the auto-PR and decide whether to merge.

The PR is authored by `clevertap-wrapper-sync[bot]`, on a branch named `task/release_<name>`, opened
against your `base_ref`.

---

## The structured PR body

Claude writes the PR body to a fixed shape so you always know where to look. The key sections come
straight from the [triage vocabulary](../GLOSSARY.md):

| Section | What it lists | What you do with it |
|---|---|---|
| **Surfaced** | Native changes the AI **implemented** in the wrapper (added/updated bridge code). | Skim each — does the new method look right across JS/Android/iOS? |
| **Skipped** | Changes the AI deliberately **did not** expose (e.g. internal-only helpers). | Sanity-check nothing important was skipped. |
| **Deferred** | Changes the AI couldn't safely auto-apply, **with a reason**. | These need a human — decide if they're follow-up work. |
| **Flagged for review** | Things the AI **couldn't confirm** (e.g. a method named in the changelog it couldn't find in source). Rendered near the top. | Look hardest here — these are the genuine "please check me" items. |
| **Native changelog** | The verbatim changelog entry/entries for the synced version(s), including intermediate versions if the sync skipped some. | Read it to understand the release without leaving the PR. |
| **Cost** | The AI cost of the run. | Just awareness. |

> ### 🟦 Beginner sidebar: surfaced / skipped / deferred / flagged
> These are the four decisions the AI makes per change. **Surfaced** = done. **Skipped** = on purpose
> not done. **Deferred** = left for a human, with a reason. **Flagged for review** = couldn't be
> *confirmed*, so raised instead of guessed. See [Glossary → the triage vocabulary](../GLOSSARY.md).

---

## The labels

Labels tell you the shape of the PR at a glance. The ones this system uses:

| Label | Means |
|---|---|
| **`auto-generated`** | This PR came from wrapper-sync (always present). |
| **`new-api`** | At least one new native API was surfaced. |
| **`breaking-change`** | The sync involved a breaking change (e.g. a `minSdk` bump or removed API). |
| **`build-failed`** | The post-sync build did **not** compile. A human must fix the branch before merge. |
| **`incomplete-sync`** | The sync didn't fully complete — review carefully; some items may be missing. |

> ### ⚠️ `build-failed` is expected sometimes — and it's *not* a hard stop
> Per the system's "Option A" design, the PR opens even when the post-sync build fails. You pull the
> branch locally, fix the compile error, push, and the PR updates. The human-review gate is what
> guarantees correctness — not the build passing in CI.

---

## The cost comment

A separate comment reports the AI cost. If the run exceeded the **soft cap** (around $3), the comment
flags that — but the run was *not* stopped by it; the cap is informational. Typical real runs have
cost a couple of dollars, so a much higher number is worth a glance.

> ### 🟦 Beginner sidebar: soft cap
> A cost threshold that, if crossed, posts an informational PR comment. It does **not** abort the
> run. See [Glossary → Soft cap](../GLOSSARY.md) and
> [troubleshooting → cost and caps](../40-troubleshooting/04-cost-and-caps.md).

---

## A pre-merge checklist

Before you merge, check:

- [ ] **Surfaced methods look right.** Spot-check that each new method is wired across all bridge
  layers (JS/Android/iOS) and demoed where the wrapper's conventions require it.
- [ ] **Flagged-for-review items are resolved.** Each flag is something the AI *couldn't confirm* —
  decide and act, or split into follow-up.
- [ ] **Deferred items are acknowledged.** Are they genuinely out of scope for this PR?
- [ ] **Version pins are consistent.** The wrapper pins live in several places; the diff/summary
  should show them all bumped together.
- [ ] **No `build-failed` label** — or if there is one, you've pulled the branch, fixed the build,
  and pushed.
- [ ] **The changelog entry** reads correctly for the release.

> ### 🟦 Beginner sidebar: cross-run shape variance
> Claude may produce a slightly different (still-correct) shape across independent runs — e.g.
> merging an overloaded method vs. keeping two separate methods. That's normal; review the result on
> its own merits rather than against an exact expected diff.

When it all checks out, **approve and merge.** The wrapper is now in step with the native release.

---

## ✅ Check yourself

<details>
<summary>1. Which PR section deserves the *most* scrutiny, and why?</summary>

**Flagged for review.** Those are items the AI *couldn't confirm* (e.g. a method named in the
changelog it couldn't find in source). It raised them instead of guessing, so a human must decide.
</details>

<details>
<summary>2. The PR has a <code>build-failed</code> label. Can you still merge?</summary>

Not as-is. The label means Claude's edits didn't compile. By design the PR still opens (Option A),
but you must pull the branch, fix the build, and push before merging. The human-review gate is the
real correctness check.
</details>

<details>
<summary>3. The cost comment says the run exceeded the soft cap. Did the run stop?</summary>

No. The soft cap is **informational** — it posts a comment but never aborts the run. It just flags a
run that cost more than usual so a human can take a look.
</details>

**Next:** [05 — dry-run and skip-sync (testing safely) →](./05-dry-run-and-skip-sync.md)
