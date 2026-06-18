# Source verification failures

> The single most expensive bug class this system has hit is **Claude writing a call to a native
> method that doesn't exist.** This page explains why it happens, the rule that prevents it, and a
> sneaky tool-permission gotcha that once defeated that rule.

---

## The cardinal rule: verify or flag, never guess

Before Claude writes a call to any native method/selector, it must **find that exact symbol in the
real native source**. If it can't confirm the symbol exists, it must **flag it for review** rather
than write the call.

Why so strict? Because a guessed method **breaks the build**. There's no "close enough" — either the
selector exists in the native SDK or it doesn't.

> ### 🟦 Beginner sidebar: source verification
> The rule that the AI must locate the real method/selector in the native source *before* writing a
> call to it. Guessing = a broken build. Non-negotiable. See
> [Glossary → Source verification](../GLOSSARY.md).

---

## The real incident: a copied-verbatim phantom selector

A real run failed because the **prompt's own reference code** contained a non-existent iOS selector
(`fetchInbox`, where the only real selector was `fetchInboxWithCallback:`). Claude copied the
reference verbatim into the iOS bridge. The post-sync build failed — caught by the build gate, and
the PR opened with a `build-failed` label.

Two lessons came out of it:

1. **Reference code in prompts must itself be source-verified.** Claude treats example code as
   trustworthy and will copy it. A phantom in the example becomes a phantom in the output.
2. **Verification must run on every native call**, even ones that look obviously correct.

The fix in tooling: corrected the reference code, added the mandatory "verify-or-flag, never guess"
instruction, a `source_verified` field in the output schema, and a cross-platform coordination flag.

> 🧠 **Analogy:** a recipe that lists an ingredient the store doesn't stock. A cook who follows it
> blindly comes home empty-handed. The fix is to check the shelf (the source) for *every* ingredient,
> and to not print fictional ingredients in the recipe in the first place.

---

## The sneaky gotcha: Bash is denied outside the working directory

Here's the trap that once defeated verification. The diff tool caches the downloaded native source
*outside* the wrapper checkout (e.g. under a cache directory in the home folder). When Claude tried
to grep that cached source with a **Bash** command, the command was **denied** — the allowlist only
permits Bash inside the wrapper's working directory.

So Claude's verification attempts silently failed, and it fell back to... guessing. Bad.

**The fix:** use the **Read / Grep / Glob tools**, not Bash, to inspect native source. Those tools
work on any absolute path; Bash is the one restricted to the cwd. The prompts now explicitly say
"use the Grep tool, not Bash" for native-source checks.

> ### ⚠️ If you're editing prompts or skills: don't reach for Bash to read files
> Bash commands referencing paths outside the wrapper checkout get denied (a security boundary). For
> reading or searching any file — especially cached native source — use the **Read**, **Grep**, and
> **Glob** tools. They aren't path-restricted the way Bash is.

---

## Two more rules that keep verification working

- **Skills must be committed to `base_ref`.** Claude discovers the wrapper's `.claude/skills/` from
  the checked-out branch. If a skill that teaches verification isn't committed to the branch the run
  syncs from, Claude won't have it. Commit skills before relying on them in a run.

- **Never use `--bare` (or otherwise strip the working tree).** Verification reads files from a real
  working tree. A bare checkout has no files to read, so verification can't run.

> ### 🟦 Beginner sidebar: `.claude/skills/`
> Per-repo expert instructions Claude auto-discovers from the checked-out repo. They're the *real*
> conventions for that wrapper. If they're not on the branch being synced, Claude can't use them. See
> [Glossary → `.claude/skills/`](../GLOSSARY.md).

---

## Symptom → cause → fix

| Symptom | Cause | Fix |
|---|---|---|
| Post-sync build fails on an unknown method/selector. | Claude wrote a call to a symbol that doesn't exist (guessed or copied from bad reference). | Fix the call on the branch; ensure prompts' reference code is source-verified. |
| Claude "couldn't verify" and over-flagged. | Verification via **Bash** was denied (path outside cwd). | Prompts must use **Read/Grep/Glob** tools for native source, not Bash. |
| Verification rules seem absent in a run. | The skill teaching them wasn't committed to `base_ref`. | Commit `.claude/skills/` to the synced branch before running. |

---

## ✅ Check yourself

<details>
<summary>1. Why must Claude verify a native symbol in source before calling it?</summary>

Because a guessed method that doesn't exist **breaks the build** — there's no "close enough." The
rule is "verify or flag, never guess": confirm the exact selector in source, or raise it for a human.
</details>

<details>
<summary>2. Claude's allowlisted <code>Bash(grep:*)</code> got denied while checking cached native source. Why, and the fix?</summary>

Bash is restricted to the wrapper's **working directory**; the cached native source lives outside it
(in a cache dir), so the command was denied. Fix: use the **Read/Grep/Glob tools**, which aren't
path-restricted, for native-source checks.
</details>

<details>
<summary>3. Why must the wrapper's skills be committed to <code>base_ref</code>?</summary>

Claude discovers `.claude/skills/` from the checked-out branch. If the skill (e.g. the one teaching
source verification) isn't on the branch being synced, Claude never sees it.
</details>

**Next:** [04 — cost and caps →](./04-cost-and-caps.md)
