# Prerequisites — what you need before running a sync

> This is the start of the **runbook** — the "actually do it yourself" section. Before you can run
> a sync you need a little access and a little setup. None of it is hard; this page lists it all.

If you only want to *understand* the system, the [primer](../00-primer/) is enough. Read on when
you're going to *run* one.

---

## Where you'll be working: the Actions tab

Everything you do as an operator happens in one place: the wrapper repo's **Actions** tab on GitHub.
That's the web page that lists workflows and lets you click **Run workflow**. You don't need a
terminal, Python, or a local checkout to run a sync — it all happens on GitHub's servers.

> ### 🟦 Beginner sidebar: GitHub Actions
> **GitHub Actions** is GitHub's built-in automation. It runs scripts on GitHub's own machines
> ("runners") when something happens — here, when you click a button. See
> [Glossary → GitHub Actions](../GLOSSARY.md).

---

## Access you need

| You need | Why |
|---|---|
| **Access to the wrapper repo** (e.g. `clevertap-cordova`) with permission to run Actions. | So you can open the Actions tab and click **Run workflow**. |
| **The Anthropic API key** for the CleverTap org. | The Brain (Claude) runs against it. It's stored as a repo secret; you only need to *have set it*, not type it each time. |
| **Knowledge of who owns the GitHub App** | If something needs the App reinstalled or a permission changed, you'll need whoever administers the `clevertap-wrapper-sync` App. |

If you're testing on a **fork** rather than the real repo, the same access applies to your fork.
See [05 — dry-run and skip-sync](./05-dry-run-and-skip-sync.md) and the hub's `TESTING.md`.

---

## The four secrets

The run needs four **secrets** stored in the wrapper repo (Settings → Secrets and variables →
Actions). You set these up *once* per repo; after that, runs read them automatically.

| Secret | What it's for |
|---|---|
| `CLEVERTAP_WRAPPER_SYNC_APP_ID` | The GitHub App's ID. |
| `CLEVERTAP_WRAPPER_SYNC_PRIVATE_KEY` | The App's private key (the `.pem` contents). |
| `ANTHROPIC_API_KEY` | The CleverTap-org Anthropic key — pays for the AI run. |
| `SLACK_WEBHOOK_URL` | The channel to ping on a failed run. |

> ### 🟦 Beginner sidebar: secret
> A **secret** is an encrypted value stored in repo settings. Workflows can read it, but humans
> can't see it after saving. See [Glossary → Secret](../GLOSSARY.md).

> ### ⚠️ Gotcha: paste the private key carefully
> When you paste the App's `.pem` private key into the secret, **line breaks must be preserved**.
> Pasting through some editors/browsers can mangle the newlines, and the token-minting step then
> fails with an `Invalid keyData` error. The clean way is to copy the file's exact bytes (e.g.
> `cat key.pem | pbcopy` on a Mac) rather than re-typing or selecting in a rich-text editor.

---

## The GitHub App

The run acts as a **bot**, not as you. That bot is the `clevertap-wrapper-sync` **GitHub App**. It
must be **installed on the repo** you're running against (the real repo, or your fork for testing),
with access to that repo.

At run time the App **mints a short-lived token** — a temporary password that lets the bot push a
branch and open a PR, then expires when the run ends. You don't manage the token; the workflow does.

> ### 🟦 Beginner sidebar: GitHub App vs. a personal token
> Using an App (instead of a person's access token) means the automation has its own bot identity,
> short-lived tokens, and survives people leaving the team. The PR is authored by
> `clevertap-wrapper-sync[bot]`. See [Glossary → GitHub App](../GLOSSARY.md).

---

## A quick readiness checklist

Before your first run, confirm:

- [ ] You can open the wrapper repo's **Actions** tab and see **native-release-sync**.
- [ ] The four secrets are present (Settings → Secrets and variables → Actions).
- [ ] The `clevertap-wrapper-sync` App is **installed** on the repo you're targeting.
- [ ] You know the **base branch** the PR should target (the integration branch).
- [ ] You know the **native versions** you want to sync to (e.g. Android `core` → `8.2.0`).

If all five are checked, you're ready to trigger a sync.

---

## ✅ Check yourself

<details>
<summary>1. Do you need Python or a local checkout to run a sync?</summary>

No. As an operator you work entirely in the wrapper repo's **Actions** tab on GitHub. The diff tool,
the AI, and the builds all run on GitHub's servers.
</details>

<details>
<summary>2. How many secrets does a wrapper repo need, and what's the one easy-to-break one?</summary>

**Four**: the App ID, the App private key, the Anthropic key, and the Slack webhook URL. The
easy-to-break one is the **private key** — its newlines must be preserved when pasted, or
token-minting fails with `Invalid keyData`.
</details>

<details>
<summary>3. Whose identity opens the PR?</summary>

The **`clevertap-wrapper-sync` GitHub App** (a bot). It mints a short-lived token at run time;
the PR is authored by `clevertap-wrapper-sync[bot]`, not by you.
</details>

**Next:** [02 — trigger a sync (click by click) →](./02-trigger-a-sync.md)
