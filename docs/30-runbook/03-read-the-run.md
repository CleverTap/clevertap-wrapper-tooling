# Read the run — watch it and understand each step

> You clicked **Run workflow**. A run appears in the Actions tab. This page teaches you to *read*
> it: what each step means, where the logs are, and where the downloadable outputs (artifacts) live.

Keep the [end-to-end sequence diagram](../10-diagrams/end-to-end-sequence.mmd) open alongside this —
the steps below map straight onto it.

---

## Watching the run

In the Actions tab, click the running entry (it'll have a spinning yellow dot). You'll see the job
and its **steps** listed top to bottom. Each step shows a status:

- 🟡 spinning = running
- ✅ green check = passed
- ❌ red X = failed
- ⚪ grey = skipped (a gate decided it shouldn't run)

Click any step to expand its **log** — the live console output of that step.

> ### 🟦 Beginner sidebar: job vs. step
> A workflow has one or more **jobs**; each job has ordered **steps**. A step runs a command or a
> composite action. See [Glossary → Job / step](../GLOSSARY.md).

---

## What each step means

The steps follow the [4-layer onion](../00-primer/02-the-4-layer-onion.md) in order:

| Step (roughly) | What it's doing | Onion layer |
|---|---|---|
| **Setup** | Mint the bot token, check out the wrapper at `base_ref`, make the `task/release_<name>` branch, install the Claude CLI. | ② Conductor |
| **Pre-sync build** | Build the example app on the *unchanged* code. **If this fails, the run stops here** ($0 AI spent). | ② (gate) |
| **Sync Android** | Claude runs the diff tool, triages, source-verifies, edits the Android bridge + versions + changelog + examples. | ③ Brain → ④ |
| **Sync iOS** | Same, for iOS. (Skipped if `ios_module = none`.) | ③ → ④ |
| **Post-sync build** | Rebuild the example app on Claude's edits. **Failure here does NOT stop the PR** — it adds a `build-failed` label. | ② |
| **Commit / push / open PR** | Package the edits, ask Claude to write the PR body, open the PR with labels. | ② |
| **Cost report** | Sum the AI cost; post a soft-cap comment if over the cap. Always runs. | ② |
| **Slack on failure** | Ping the channel only if something genuinely failed. | ② |

> ### 🟦 Beginner sidebar: why some steps are grey (skipped)
> The conductor uses **`if:` gates** to decide which steps run. For example, post-sync build and the
> PR steps are skipped when `skip_sync = true`. A grey step isn't an error — a gate just decided it
> shouldn't run. See [Glossary → `if:` / gating](../GLOSSARY.md).

---

## Reading the Sync step logs (the interesting part)

Expand a **Sync** step and you'll see Claude working: it emits one JSON event per line as it goes —
this is **stream-json**. Each line is a tool call or a result. You don't have to read it live; the
useful summary is extracted afterward.

> ### 🟦 Beginner sidebar: stream-json
> An output format where Claude prints one JSON event per line as it works. A script later reads the
> final `result` event to get the authoritative cost and token totals. See
> [Glossary → stream-json](../GLOSSARY.md).

If a Sync step fails, the workflow dumps Claude's captured **stderr** in a grouped log block — that's
where the real error message is. (Early versions lost stderr; it's now captured on purpose.)

---

## Where the outputs live (artifacts)

After the run, scroll to the run's summary page. At the bottom is an **Artifacts** panel with
downloadable files. Depending on the run you'll find:

- **`claude-output-android.json` / `claude-output-ios.json`** — Claude's full output per platform.
  The structured triage log (surfaced / skipped / deferred / flagged) lives *inside* the `.result`
  field as a fenced JSON block. The authoritative cost is in the CLI envelope's `total_cost_usd` and
  `usage.*` fields.
- **The built APK** (Android) and **iOS `.app`** — the post-sync build outputs, so a reviewer can
  download and side-load/inspect.

> ### 🟦 Beginner sidebar: artifact
> An **artifact** is a file a workflow saves for you to download afterward — build outputs, logs,
> Claude's JSON. See [Glossary → Artifact](../GLOSSARY.md).

---

## The fastest way to know how it went

You usually don't need to read logs at all:

- **All green + a PR opened** → success. Go read the PR ([04 — review the PR](./04-review-the-pr.md)).
- **Stopped at pre-sync build** → the pipeline was already broken; nothing was synced, $0 AI.
- **PR opened with a `build-failed` label** → Claude's edits didn't compile; a human fixes the
  branch. (Non-fatal — see [04](./04-review-the-pr.md) and
  [troubleshooting → failure modes](../40-troubleshooting/01-failure-modes.md).)
- **Failed before a PR + a Slack ping** → something broke in setup or the sync itself. See
  [troubleshooting](../40-troubleshooting/01-failure-modes.md).

---

## ✅ Check yourself

<details>
<summary>1. A step shows grey (skipped), not red. Is that a failure?</summary>

No. Grey means a **gate** (`if:` condition) decided the step shouldn't run — e.g. the iOS sync is
skipped when `ios_module = none`, and post-sync build is skipped when `skip_sync = true`. It's normal.
</details>

<details>
<summary>2. Where do you find the surfaced/skipped/deferred counts and the authoritative cost?</summary>

In the run's **Artifacts**: `claude-output-<platform>.json`. The triage log lives inside the
`.result` field as a fenced JSON block; the authoritative cost is the CLI envelope's
`total_cost_usd` (not numbers Claude wrote in its own prose).
</details>

<details>
<summary>3. A Sync step failed. Where's the real error message?</summary>

In the grouped log block where the workflow dumps Claude's captured **stderr**. Expand the failed
Sync step's log to find it.
</details>

**Next:** [04 — review the PR (read what the robot produced) →](./04-review-the-pr.md)
