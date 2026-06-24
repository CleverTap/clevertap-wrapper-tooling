# The repos, and where everything lives

> You've seen *what* the system does and *how a run flows*. This page answers a flatter question
> that trips up newcomers: **which files live in which repo, and why?**

There are two *kinds* of repo in this story. Getting them straight makes every other page click.

---

## The two kinds of repo

```
┌──────────────────────────────────────────────────────────────────────┐
│  THE HUB         CleverTap/clevertap-wrapper-tooling                  │
│  (one, shared)   The brains and the machinery. Written once.          │
│                                                                       │
│   • .github/workflows/sync.yml        ← the reusable Conductor (②)    │
│   • .github/actions/                   ← composite actions (setup,    │
│                                          claude-sync, open-pr, build) │
│   • tools/diff_native_api.py           ← the Ground-truth diff (④)    │
│   • prompts/                           ← the prompts Claude runs (③)  │
│   • scripts/                           ← cost / PR / Slack helpers     │
└──────────────────────────────────────────────────────────────────────┘
                         ▲  called by
                         │
┌──────────────────────────────────────────────────────────────────────┐
│  THE WRAPPERS    CleverTap/clevertap-cordova                          │
│  (many, thin)    CleverTap/clevertap-flutter                          │
│                  CleverTap/clevertap-react-native                     │
│                                                                       │
│   • .github/workflows/native-release-sync.yml  ← the Trigger (①),     │
│                                                   a tiny "doorbell"    │
│   • .claude/skills/                            ← the wrapper's own     │
│                                                   know-how             │
│   • the actual bridge code the automation edits (JS / Dart / Kotlin / │
│     Obj-C) + the example apps                                         │
└──────────────────────────────────────────────────────────────────────┘
```

> 🧠 **Analogy:** the **hub** is a commercial kitchen — ovens, recipes, the head chef. Each **wrapper
> repo** is a restaurant's front door with a tiny "ring for service" bell. The bell doesn't cook; it
> calls the kitchen. The kitchen is shared by every restaurant.

---

## The hub: `clevertap-wrapper-tooling` (written once, shared by all)

This is the repo you're reading the docs *in*. It holds every reusable piece, so the three wrappers
don't each maintain their own copy.

| Lives here | What it is | Onion layer |
|---|---|---|
| `.github/workflows/sync.yml` | The **reusable workflow** — sequences the steps and gates them. | ② Conductor |
| `.github/actions/setup`, `claude-sync`, `open-pr`, `build/*` | **Composite actions** — reusable bundles of steps the conductor calls. | ② |
| `prompts/` (e.g. `sync-orchestrator-cordova.md`, `pr-description.md`) | The **written instructions** handed to Claude. | ③ Brain |
| `tools/diff_native_api.py` | The **diff tool** — cold facts about what changed in the native SDK. | ④ Ground truth |
| `scripts/` (cost, PR, Slack) | Shell helpers for cost reporting, opening the PR, failure pings. | ② |

> ### 🟦 Beginner sidebar: reusable workflow & composite action
> A **reusable workflow** is a `.yml` file other workflows can *call*, like a shared function. A
> **composite action** is a smaller reusable bundle of steps. Both let us write the logic once in the
> hub and reuse it from every wrapper. See [Glossary](../GLOSSARY.md).

---

## The wrappers: `clevertap-cordova` (and flutter, react-native)

Each wrapper repo carries only two automation-related things plus its own code:

| Lives here | What it is | Onion layer |
|---|---|---|
| `.github/workflows/native-release-sync.yml` | The **dispatch workflow** — the button/form a maintainer clicks. It mostly just *calls* `sync.yml` in the hub and passes along versions + secrets. | ① Trigger |
| `.claude/skills/` | The wrapper's **expert know-how** — the real conventions Claude must follow for *this* wrapper. | (feeds ③) |
| bridge code + example apps | The actual files the automation reads and edits. | — |

For Cordova specifically, the `.claude/skills/` set is:

- **`version-detection`** — every place a version number lives, and the `libVersion` integer rule.
- **`api-wrapper-patterns`** — how to wrap one native method across JS / Android / iOS.
- **`native-sdk-changelog-analysis`** — how to categorize changes and the triage decision tree.
- **`example-app-patterns`** — how to demo a method in **all four** Cordova sample apps.
- **`changelog-generation`** — the exact CHANGELOG format and link anchors.
- **`ionic-native-typings`** — exposing a method to Ionic/Angular via the typings package.

> ### 🟦 Beginner sidebar: prompt vs. skill
> The **prompt** (in the hub) is the *task* — "sync this wrapper to these versions." The **skills**
> (in the wrapper) are the *know-how* — the wrapper's real conventions. Claude reads the skills to
> learn how to do the task correctly. See [Glossary → `.claude/skills/`](../GLOSSARY.md).

---

## The "thin pointer" model — why split it this way?

The wrapper's dispatch workflow is deliberately **tiny**. It doesn't contain any sync logic; it just
*points at* the hub and says "run your shared workflow, here are my versions and secrets." This is
the **thin pointer** model.

Why it's worth it:

- **Fix once, fix everywhere.** A bug in the sync logic is fixed in the hub, and all wrappers get
  the fix. No copy-pasting across three repos.
- **Adding a new wrapper is cheap.** Drop in the small dispatch file, add the secrets, write the
  wrapper's skills, install the App — and it reuses the whole shared machine.
- **Each wrapper pins a hub version.** The dispatch's `uses:` line points at a hub tag (e.g. `@v1`),
  so an in-flight change in the hub doesn't surprise a wrapper mid-release.

> 🧠 **Analogy:** the dispatch file is a **TV remote**, not the TV. It has just enough buttons to
> say "do the thing"; all the actual circuitry lives in the set (the hub).

> ### 🟦 Beginner sidebar: the four secrets
> Each wrapper repo stores four encrypted **secrets** the run needs: the GitHub App's ID, the App's
> private key, the Anthropic API key, and a Slack webhook URL. The dispatch passes them into the hub
> workflow. You'll set these up in the [runbook](../30-runbook/01-prerequisites.md).

---

## ✅ Check yourself

<details>
<summary>1. The diff tool, the prompts, and <code>sync.yml</code> — which repo are they in?</summary>

The **hub** (`clevertap-wrapper-tooling`). All the reusable machinery — Conductor, Brain's prompts,
Ground-truth diff tool, composite actions, helper scripts — is written once in the hub.
</details>

<details>
<summary>2. What are the only automation files that live in a wrapper repo like clevertap-cordova?</summary>

A tiny **dispatch workflow** (`native-release-sync.yml`, the Trigger button) and the wrapper's
**`.claude/skills/`** (its expert know-how) — plus the bridge code and example apps the automation
edits. The sync *logic* lives in the hub.
</details>

<details>
<summary>3. Why is the dispatch workflow kept so thin?</summary>

So the sync logic is written once in the hub and shared by every wrapper. Fix a bug in the hub and
all wrappers benefit; adding a new wrapper just means dropping in the small pointer file. That's the
"thin pointer" model.
</details>

**Next:** [Runbook → 01 — prerequisites (what you need before running a sync) →](../30-runbook/01-prerequisites.md)
