# When Claude misses an API

> "The native SDK added a method, but the PR didn't surface it." Sometimes that's correct (it was
> internal). Sometimes it's a real miss. This page explains *why* misses happen and the safety net
> that catches most of them.

---

## Why a miss can happen: the regex ~80% rule

The Ground-truth diff tool (`diff_native_api.py`, Layer ④) finds methods using **regex** —
pattern-matching on the source text — not a full language parser. That's a deliberate trade-off:
regex is simple and stdlib-only, and it catches about **80%** of API changes reliably.

The other ~20%? Methods written in a shape the patterns don't quite match (unusual formatting,
macros, multi-line declarations) can slip past the regex.

> ### 🟦 Beginner sidebar: regex vs. AST
> **Regex** describes text patterns ("a line starting with `public`, then a word, then `(`"). A full
> parser would build an **AST** (a complete grammar tree) and never miss — but it's far more complex.
> The diff tool chooses regex on purpose and backs it up with a recall pass. See
> [Glossary → Regex / AST](../GLOSSARY.md).

---

## The safety net: the changelog recall pass

The diff tool isn't the only signal. After reading the diff, Claude runs a **recall pass**: it
re-reads the native SDK's **changelog** and cross-checks it against the diff tool's output. Any
public API the changelog *names* that the regex diff *missed* gets picked up here.

For each recovered item, Claude must **source-verify** it against the new native header/source, then
decide: implement it, remove it, keep-deprecated, or update its signature — exactly like a normal
diffed change.

> 🧠 **Analogy:** the diff tool is a **metal detector** that finds ~80% of the coins. The recall pass
> is **then reading the treasure map** (the changelog) to find the ones the detector walked past.

---

## When it *can't* confirm: `flagged_for_review`

What if the changelog mentions something but Claude **cannot find it in the source** — or it's a
behavior-only note with no method to wrap? Then Claude does **not** guess. It puts the item under
**`flagged_for_review`**, rendered near the top of the PR body, with a short note on why.

This is the system's honesty valve: better to surface "I saw this mentioned but couldn't confirm it"
than to invent a method that breaks the build.

> ### 🟦 Beginner sidebar: flagged for review
> A specific kind of deferral: the AI couldn't *confirm* something, so it raises a flag for a human
> instead of acting on it. The whole "verify-or-flag, never guess" rule exists to keep the AI from
> hallucinating APIs. See [Glossary → Flagged for review](../GLOSSARY.md) and
> [03 — source verification failures](./03-source-verification-failures.md).

---

## So when *I* spot a missing API, what do I do?

1. **Check the PR's `flagged_for_review` section first.** It may already be there with a reason.
2. **Check `skipped`.** Maybe it was deliberately not exposed (internal helper) — that's fine.
3. If it's genuinely missing and *should* be surfaced, add it by hand using the wrapper's
   conventions (for Cordova, the `api-wrapper-patterns` and `example-app-patterns` skills describe
   the exact recipe), then push to the PR branch.
4. Consider whether the diff tool's regex should be improved — but that's a hub change, not a per-run
   fix.

---

## ✅ Check yourself

<details>
<summary>1. Roughly what fraction of API changes does the regex diff catch on its own?</summary>

About **80%**. The diff tool uses regex (not a full parser) on purpose; the remaining ~20% are caught
by the changelog **recall pass**.
</details>

<details>
<summary>2. The changelog names a method but Claude can't find it in source. What does it do?</summary>

It puts the item under **`flagged_for_review`** (near the top of the PR) with a reason, rather than
guessing. "Verify-or-flag, never guess."
</details>

<details>
<summary>3. You spot a missing API in a PR. What's your first move?</summary>

Check the PR's **`flagged_for_review`** and **`skipped`** sections — it may have been raised for a
human already, or deliberately not exposed. If it's a genuine miss that should be surfaced, add it by
hand following the wrapper's skills and push.
</details>

**Next:** [03 — source verification failures →](./03-source-verification-failures.md)
