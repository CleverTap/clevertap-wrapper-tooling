# Wrapper-Sync — Onboarding Kit

Welcome. This kit teaches the **wrapper-sync automation** from zero. It assumes you know
**nothing** about Python, git, GitHub Actions, or even what a "wrapper SDK" is. By the end
you should be able to explain the whole system to someone else — that's the bar.

> **What is this system, in one breath?**
> When CleverTap ships a new native Android/iOS SDK, someone clicks **one button** and a robot
> (Claude, running on GitHub's servers) reads what changed, updates the wrapper code to match,
> and opens a pull request for a human to review. This kit explains every moving part of that.

---

## How to use this kit

Read in order. Each page ends with a **"Check yourself"** block — *answer the questions before
moving on*. Trying to recall an answer is what makes it stick; re-reading does almost nothing.

| Stage | Folder | What you get |
|-------|--------|--------------|
| 1. Get the big picture | [`00-primer/`](./00-primer/) | What the system is, why it exists, the **4-layer onion** mental model, a day-in-the-life. |
| 2. See it | [`10-diagrams/`](./10-diagrams/) | Pictures of the flow, the architecture, and the data shapes. |
| 3. Read the code, line by line | [`20-walkthroughs/`](./20-walkthroughs/) | Every confusing file explained with a diagram + plain-English annotations + beginner sidebars. |
| 4. Do it yourself | [`30-runbook/`](./30-runbook/) | How to actually run a sync, read the result, and debug cheaply. |
| 5. When it breaks | [`40-troubleshooting/`](./40-troubleshooting/) | Known failure modes as symptom → cause → fix. |
| 6. Prove you learned it | [`50-retention/`](./50-retention/) | Flashcards, hands-on exercises, and the capstone + graduation checklist. |
| (reference) | [`GLOSSARY.md`](./GLOSSARY.md) | Every jargon word, defined for a beginner. |

**Start here:** [`00-primer/01-what-is-wrapper-sync.md`](./00-primer/01-what-is-wrapper-sync.md)

---

## The one mental model to anchor on

Everything in this system is a **4-layer onion**. A maintainer's click travels *down* the
layers; a finished pull request travels back *up*.

```
        ┌──────────────────────────────────────────────────────────┐
   ①    │  TRIGGER   — a button/form in a wrapper repo               │  "I want to sync to v8.2.0"
        └──────────────────────────────────────────────────────────┘
                              │ calls
        ┌──────────────────────────────────────────────────────────┐
   ②    │  CONDUCTOR — sync.yml: sequences the steps, no brains      │  "do A, then B, then C…"
        └──────────────────────────────────────────────────────────┘
                              │ hands a prompt to
        ┌──────────────────────────────────────────────────────────┐
   ③    │  BRAIN     — Claude (an AI) does the actual wrapping       │  "decide what to change & change it"
        └──────────────────────────────────────────────────────────┘
                              │ relies on
        ┌──────────────────────────────────────────────────────────┐
   ④    │  GROUND TRUTH — diff_native_api.py: the cold, hard facts   │  "here is exactly what changed"
        └──────────────────────────────────────────────────────────┘
```

The single most important idea — and the one beginners miss — is layer ②→③:
**the YAML file does not wrap any APIs. It just hands a written prompt to an AI, and the AI does the work.**
Hold onto that and the rest falls into place. Full explanation:
[`00-primer/02-the-4-layer-onion.md`](./00-primer/02-the-4-layer-onion.md).

---

## A note for maintainers of this kit

- The diagrams in [`10-diagrams/`](./10-diagrams/) are **Mermaid text** committed to git — they
  are the source of truth and render automatically on GitHub.
- The pretty HTML/slide versions are **generated** from these by the `visual-explainer` plugin
  into `docs/_generated/` (gitignored). Never hand-edit generated HTML.
- When the code changes, follow [`90-meta/maintaining-the-docs.md`](./90-meta/maintaining-the-docs.md)
  — the step-by-step for keeping the Markdown *and* HTML correct after you change a wrapper, add a new
  wrapper, or change the tooling source. (Quick lookup of what depends on what:
  [`90-meta/drift-checklist.md`](./90-meta/drift-checklist.md).)
