# A day in the life of one sync

> You've met the [4-layer onion](./02-the-4-layer-onion.md). Now let's watch it *run* — one real
> sync, start to finish, narrated. Nothing new to memorize here; this is the onion in motion.

Our example: the Android **core** module just released **8.2.0**. The wrapper is currently pinned
at **8.1.0**. A maintainer wants to catch the wrapper up. (iOS isn't part of this release, so they'll
sync Android only.)

Follow along with the picture: [end-to-end sequence diagram](../10-diagrams/end-to-end-sequence.mmd).

---

## Scene 1 — the click (Layer ①, Trigger)

The maintainer opens the wrapper repo on GitHub, goes to the **Actions** tab, picks
**native-release-sync**, and clicks **Run workflow**. A small form appears. They fill in:

- `android_module` → `core`
- `android_version` → `8.2.0`
- `ios_module` → `none` (this release is Android-only)
- leave the rest at defaults

…and click the green button. That's the entire human effort until the PR shows up.

> 🧠 **Analogy:** they pressed the **vending-machine button**. Nothing is made *by* the button — it
> just tells the machine behind the glass to start.

---

## Scene 2 — setup (Layer ②, Conductor)

The button **called** the shared workflow in the hub repo (`sync.yml`). The conductor now does the
boring-but-essential prep:

1. **Mints a bot token** — a short-lived password so the `clevertap-wrapper-sync` GitHub App can act
   on the repo (push a branch, open a PR) without anyone's personal account.
2. **Checks out the wrapper repo** at its base branch.
3. **Creates a fresh branch** like `task/release_<name>` so nothing touches the base branch until a
   human reviews.
4. **Installs the Claude CLI** so the Brain can run later.

> ### 🟦 Beginner sidebar: GitHub App & token
> A **GitHub App** is a bot identity. Instead of using a person's login, the workflow asks the App to
> **mint a token** — a temporary password that expires when the run ends. See
> [Glossary → GitHub App](../GLOSSARY.md).

---

## Scene 3 — the pre-sync build gate

Before spending a single cent on the AI, the conductor **builds the example app as-is** — on the
unchanged code. Why? To fail fast and cheap.

> ### ⚠️ Why build *before* changing anything?
> If the example app is already broken on the base branch, there's no point paying for an AI sync
> into a pipeline that can't compile. So: build first. **If this build fails, the run stops here and
> $0 of AI cost is spent.**

In our run the pre-sync build is green, so we continue.

---

## Scene 4 — Claude syncs Android (Layer ③, Brain → Layer ④, Ground truth)

Now the real work. The conductor hands Claude a **written prompt** (with the version blanks filled
in: old `8.1.0`, new `8.2.0`). Claude, running headless, does this:

1. **Runs the diff tool** (`diff_native_api.py`) for Android core `8.1.0 → 8.2.0`. This is Layer ④,
   the cold-facts tool. It reports exactly what changed: methods added/removed/changed, build-setting
   changes, and the relevant changelog text.
2. **Reads the result as ground truth** — then does a **recall pass**: re-reads the native changelog
   to catch anything the diff tool's regex missed (~20% of changes).
3. **Triages each change**: for every new/changed method, decides **surface / skip / defer / flag**.
   - *Surface* = implement it in the wrapper.
   - *Skip* = deliberately don't expose (e.g. internal helper).
   - *Defer* = can't safely auto-apply; leave a note for a human.
   - *Flag for review* = can't even *confirm* it (e.g. a method named in the changelog it can't find
     in the source), so it raises a flag instead of guessing.
4. **Source-verifies before writing.** For any method it implements, it first finds the exact
   method/selector in the real native source. **Guessing a method that doesn't exist = a broken
   build**, so the rule is "verify or flag — never guess."
5. **Writes the bridge code** across all the layers the Cordova wrapper needs (JavaScript, Android,
   iOS), **bumps every version location**, **updates the changelog**, and **adds demos in the
   example apps**.
6. **Emits a structured summary** of everything it did, plus the cost.

> 🧠 **Analogy:** Claude is the **chef**; the diff tool is the **librarian who only tells you what's
> truly on the shelf**. The chef cooks creatively but only with real ingredients the librarian
> confirms exist.

(If this had been a both-platforms release, the conductor would run **Sync Android, then Sync iOS** —
two passes. Here it's Android only.)

---

## Scene 5 — the post-sync build

The conductor **rebuilds the example app** — this time on Claude's edited code — to see if the
changes actually compile.

> ### 🟦 Beginner sidebar: post-sync build failure is *not* fatal
> If this build fails, the run does **not** throw away the work. The PR still opens, but it gets a
> **`build-failed`** label and a warning banner. A human pulls the branch, fixes the compile error,
> and pushes. The human-review gate is what catches problems — not a hard stop.

In our run the post-sync build is green.

---

## Scene 6 — commit, push, open the PR

The conductor:

1. **Commits** Claude's edits and **pushes** the branch.
2. **Asks Claude to write the PR description** — a structured body listing surfaced / skipped /
   deferred / flagged-for-review items, the native changelog, and the cost.
3. **Opens the pull request** against the base branch, applying labels (e.g. `auto-generated`, and
   `new-api` if methods were surfaced).
4. **Posts a cost comment** and pings Slack only if something failed.

> ### 🟦 Beginner sidebar: the cost comment
> Every run sums the AI cost. There's a **soft cap** (around $3). If a run goes over, the workflow
> posts an informational PR comment — it does **not** stop the run. Real runs have typically cost a
> couple of dollars. See [Glossary → Soft cap](../GLOSSARY.md).

---

## Scene 7 — the human reviews

A PR notification lands. The maintainer opens it, reads the structured summary, checks the surfaced
methods and the version bumps, confirms the build is green (or fixes it if `build-failed`), and
**merges.** Done — the wrapper is now in step with Android core 8.2.0.

---

## The whole run in one breath

> Maintainer fills the form and clicks → conductor sets up a branch and bot token → pre-sync build
> gate (fail fast, $0 AI) → Claude diffs the native SDK, triages, source-verifies, edits the bridge,
> bumps versions, updates changelog + examples → post-sync build (failure is non-fatal) → commit,
> push, PR opens with a structured body + labels + cost comment → human reviews and merges.

---

## ✅ Check yourself

<details>
<summary>1. In our example, why did the maintainer set <code>ios_module</code> to <code>none</code>?</summary>

Because this was an **Android-only** release (core `8.1.0 → 8.2.0`). One dispatch cleanly handles
Android-only, iOS-only, or both — you just leave the other platform's module at `none`.
</details>

<details>
<summary>2. The pre-sync build runs before Claude. What does a failure there save?</summary>

It saves **AI cost**. If the example app is already broken, the run aborts before paying for any AI
work — there's no point syncing into a pipeline that can't compile.
</details>

<details>
<summary>3. The post-sync build fails. Does the PR still open?</summary>

**Yes.** A post-sync build failure is non-fatal: the PR opens with a `build-failed` label and a
warning banner. A human pulls the branch, fixes the compile error, and pushes.
</details>

<details>
<summary>4. What does "verify or flag — never guess" protect against?</summary>

A broken build. If Claude wrote a call to a native method that doesn't actually exist (e.g. one it
only saw named in a changelog), the post-sync build would fail. So it must find the real
method/selector in source first, or **flag it for a human** instead of guessing.
</details>

**Next:** [04 — the repos, and where everything lives →](./04-repos-and-where-things-live.md)
