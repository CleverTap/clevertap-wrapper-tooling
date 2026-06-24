# FAQ

> The most common questions and gotchas, pulled together. If you skimmed everything else, this page
> is the cheat sheet. Each answer links to the fuller explanation.

---

<details>
<summary><strong>1. Does the YAML workflow actually write the wrapper code?</strong></summary>

No. The workflow (Layer ②, the Conductor) only **sequences and gates** steps. The actual
code-writing is done by **Claude** (Layer ③, the Brain), which the conductor hands a written prompt
to. This is the single idea beginners get backwards. See
[the 4-layer onion](../00-primer/02-the-4-layer-onion.md).
</details>

<details>
<summary><strong>2. I asked to sync but nothing changed. Broken?</strong></summary>

Almost certainly not. You probably synced to the version **already pinned** — Claude correctly
no-ops. Pick a target version that differs from the current pin. See
[failure modes §3](./01-failure-modes.md).
</details>

<details>
<summary><strong>3. The PR opened with a <code>build-failed</code> label. Is that an emergency?</strong></summary>

No — it's by design ("Option A"). Claude's edits didn't compile, so the PR opens anyway. A human
pulls the branch, fixes the build, pushes, and merges. See
[review the PR](../30-runbook/04-review-the-pr.md) and [failure modes §2](./01-failure-modes.md).
</details>

<details>
<summary><strong>4. The run died at setup with <code>Invalid keyData</code>. What now?</strong></summary>

The GitHub App **private key's newlines were mangled** when pasted into the secret. Re-paste the
exact `.pem` bytes (e.g. `cat key.pem | pbcopy`) and verify the key. See
[prerequisites](../30-runbook/01-prerequisites.md) and [failure modes §4](./01-failure-modes.md).
</details>

<details>
<summary><strong>5. How do I test without spending AI money or touching protected branches?</strong></summary>

Use **`skip_sync=true`** (builds only, $0 AI), a **`base_ref` baseline branch**, or full **fork
testing** per the hub's `TESTING.md`. See [dry-run and skip-sync](../30-runbook/05-dry-run-and-skip-sync.md).
</details>

<details>
<summary><strong>6. The native SDK added a method but the PR didn't surface it. Why?</strong></summary>

Could be three things: it was deliberately **skipped** (internal), it's in **`flagged_for_review`**
(named in the changelog but unconfirmable), or the regex diff missed it and the recall pass didn't
recover it. Check those PR sections first. See
[when Claude misses an API](./02-when-claude-misses-an-api.md).
</details>

<details>
<summary><strong>7. Why does the diff tool only catch ~80% of changes?</strong></summary>

It uses **regex** (pattern-matching), not a full parser — a deliberate simplicity trade-off. The
remaining ~20% are caught by the **changelog recall pass**. See
[when Claude misses an API](./02-when-claude-misses-an-api.md) and [Glossary → Regex](../GLOSSARY.md).
</details>

<details>
<summary><strong>8. Claude "couldn't verify" a method and over-flagged everything. Why?</strong></summary>

Most likely it tried to inspect the **cached native source with Bash**, which is denied outside the
working directory. The fix is to use the **Read/Grep/Glob tools** (not path-restricted) for
native-source checks. See [source verification failures](./03-source-verification-failures.md).
</details>

<details>
<summary><strong>9. The cost number Claude printed doesn't match the cost report. Which is right?</strong></summary>

The **cost report** — it reads the authoritative **CLI envelope** (`total_cost_usd`, `usage.*`).
Numbers Claude writes in its own prose can drift and aren't trustworthy. See
[cost and caps](./04-cost-and-caps.md).
</details>

<details>
<summary><strong>10. A run cost more than the $3 cap. Did it stop the PR?</strong></summary>

No. The cap is **soft** — it posts an informational comment but never aborts a run (so it can't leave
a half-finished PR). See [cost and caps](./04-cost-and-caps.md).
</details>

<details>
<summary><strong>11. I updated a skill but the run still behaved the old way. Why?</strong></summary>

Skills must be **committed to the `base_ref` branch** the run syncs from — Claude discovers
`.claude/skills/` from the checked-out branch. Commit your skill changes before the run picks them
up. See [source verification failures](./03-source-verification-failures.md).
</details>

<details>
<summary><strong>12. My retry bails immediately saying the branch exists. How do I get unstuck?</strong></summary>

A previous failed run left a `task/release_<name>` branch. Re-run with a **unique `release_name`** to
avoid the collision. See [trigger a sync](../30-runbook/02-trigger-a-sync.md) and
[failure modes §4](./01-failure-modes.md).
</details>

---

## ✅ Check yourself

<details>
<summary>1. Name the two "this looks broken but it's by design" behaviors.</summary>

(1) Syncing to the **already-pinned version** → Claude no-ops (Q2). (2) A **`build-failed`** PR still
opening, for a human to fix (Q3). Both are intended, not bugs.
</details>

<details>
<summary>2. What's the one-line fix for the two most common setup/retry failures?</summary>

`Invalid keyData` → **re-paste the private key with intact newlines** (Q4). Branch-exists on retry →
**use a unique `release_name`** (Q12).
</details>

**Next:** back to the [primer](../00-primer/01-what-is-wrapper-sync.md), or jump to the
[runbook](../30-runbook/01-prerequisites.md) to run your own sync.
