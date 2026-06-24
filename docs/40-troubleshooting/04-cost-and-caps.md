# Cost and caps

> The AI run costs real money. This page explains the **soft cap**, why it doesn't stop a run, and
> where the *authoritative* cost number comes from.

---

## The soft cap (~$3): a comment, not a brake

Every run sums up its AI cost. There's a **soft cap** set around **$3**. If a run exceeds it, the
workflow **posts an informational PR comment** flagging the overage.

The key word is **soft**: crossing the cap does **not** stop the run. The reasoning — you don't want
to fail *mid-PR-creation* and leave a half-finished mess. Far better to let the run finish, open the
PR, and post a "this cost more than usual" note for a human to notice.

> ### 🟦 Beginner sidebar: soft cap vs. hard cap
> A **soft cap** reports and keeps going. A **hard cap** would abort. This system uses a soft cap on
> purpose. (A future true guardrail might add a between-platform hard stop + a `--max-turns` limit on
> the sync calls — that's noted as a possible enhancement, not current behavior.) See
> [Glossary → Soft cap](../GLOSSARY.md).

---

## What a normal run costs

Real runs have typically cost on the order of a **couple of dollars** — well under the $3 cap. The
cap was set low *on purpose* so it catches anomalies (a runaway loop, an unusually large diff)
without firing on ordinary runs. If you see a cost far above a few dollars, it's worth a look.

> 🧠 **Analogy:** the soft cap is a **dashboard warning light**, not a kill switch. It says "hey,
> you're burning more fuel than usual" — but it lets you finish the trip and decide for yourself.

---

## Where the *authoritative* cost comes from

This matters if you're reading the numbers yourself. Claude sometimes writes cost/token estimates
*inside its own prose* — **don't trust those.** The reliable figures come from the **CLI envelope**:

- `total_cost_usd` — the authoritative dollar cost.
- `usage.input_tokens` / `usage.output_tokens` — the authoritative token counts.

These live in the JSON envelope the CLI wraps around the response, not in the text Claude generated.
The cost script reads the envelope fields for exactly this reason.

> ### 🟦 Beginner sidebar: the CLI envelope vs. the result text
> When Claude runs headless with JSON output, the CLI wraps the answer in an **envelope** with
> trustworthy metadata (`total_cost_usd`, `usage.*`). Inside that envelope, `.result` holds Claude's
> own text — which may contain self-reported numbers that drift. Read the envelope, not the prose.
> See [Glossary → stream-json / jq](../GLOSSARY.md).

---

## A note on which models run

Even when you pick `sonnet` (the default), a run uses **more than one model**: the lead reasoning
model you chose, plus a cheaper model for small auxiliary calls. The per-model split shows up in the
run's output under a `modelUsage` block, and the cost report **sums all models** correctly — so the
total you see already includes everything.

---

## ✅ Check yourself

<details>
<summary>1. A run exceeds the $3 soft cap. What happens to the run?</summary>

Nothing stops it. The cap is **soft** — it posts an informational PR comment but lets the run finish
and open the PR. Failing mid-PR-creation would be worse than a slightly costly run.
</details>

<details>
<summary>2. Where's the trustworthy cost figure — the number Claude wrote, or somewhere else?</summary>

Somewhere else: the **CLI envelope's `total_cost_usd`** (and `usage.*` for tokens). Numbers Claude
writes inside its own prose can drift and aren't authoritative.
</details>

<details>
<summary>3. You picked <code>sonnet</code>. Does the cost include only Sonnet?</summary>

No — a run also uses a cheaper model for auxiliary calls. The `modelUsage` block shows the split, and
the cost report **sums all models**, so the reported total is complete.
</details>

**Next:** [05 — FAQ →](./05-faq.md)
