# Exercises — do it, don't read it

> Reading explanations is recognition. *Doing* is recall. Each drill below has a **task**, a folded
> **hint**, and a folded **solution**. Attempt the task first — open the real files, run the real
> commands — then check the hint, then grade yourself against the solution.

These cover the whole system: tracing a run through the [4 layers](../00-primer/02-the-4-layer-onion.md),
reading [`sync.yml` gates](../20-walkthroughs/sync-yml.md), the [3-touch rule](../20-walkthroughs/orchestrator-prompt-cordova.md),
[regex decoding](../20-walkthroughs/diff-native-api/03-surface-extraction-java-kotlin.md),
[source acquisition](../20-walkthroughs/diff-native-api/02-source-acquisition.md), and
[failure modes](../40-troubleshooting/01-failure-modes.md).

---

## Exercise 1 — Trace one run from click to PR, naming each layer

**Task:** A maintainer syncs Android core `8.1.0 → 8.2.0` (iOS not in this release). Narrate the run
from the click to the merged PR, and at each phase name **which of the four layers** is acting.

<details><summary>Hint</summary>

The four layers are ① Trigger, ② Conductor, ③ Brain, ④ Ground truth. A click travels *down* the
layers; a PR travels back *up*. Walk the conductor's step order: setup → pre-sync build → sync →
post-sync build → commit/push/PR. See [a day in the life](../00-primer/03-a-day-in-the-life.md).
</details>

<details><summary>Solution</summary>

1. **Click** — maintainer fills the form (`android_version=8.2.0`, `ios_module=none`) and runs it.
   → **Layer ① Trigger** (`native-release-sync.yml` in the wrapper repo).
2. The trigger **calls** the hub's `sync.yml`. → **Layer ② Conductor.**
3. **Setup:** mint a bot token, check out the wrapper, make a fresh branch, install the Claude CLI.
   → Layer ②.
4. **Pre-sync build** of the example app, *before* any AI cost. Green here, so continue. → Layer ②
   (it calls the `build/cordova` action).
5. **Sync Android:** the conductor hands Claude a rendered prompt → **Layer ③ Brain.** Claude runs
   `diff_native_api.py` (**Layer ④ Ground truth**), reads `diff.json`, does the recall pass over the
   changelog, triages each change (surface/skip/defer/flag), **source-verifies**, writes the bridge
   (JS + Android 3-touch + iOS 2-touch), bumps versions, updates the changelog + all 4 sample apps,
   emits structured JSON. (iOS sync is skipped — no iOS version.)
6. **Post-sync build** — rebuild with Claude's edits. → Layer ②.
7. **Commit → push → open PR** with labels (`auto-generated`, `new-api` if methods surfaced) + cost
   comment; Slack only on failure. → Layer ②. The PR is the output traveling back *up*.
8. **Human reviews and merges.** Layer ② produced it; the human is never removed.
</details>

---

## Exercise 2 — Predict what an `if:` gate evaluates to

**Task:** The real **Open combined PR** gate from [`sync.yml`](../20-walkthroughs/sync-yml.md) is:

```
!cancelled()
&& env.no_changes != 'true'
&& steps.sync_android.outcome != 'failure'
&& steps.sync_ios.outcome != 'failure'
&& (steps.sync_android.outcome == 'success' || steps.sync_ios.outcome == 'success')
```

For each scenario, decide **true (PR opens)** or **false (PR skipped)** and why:

- **(a)** Android-only run: `sync_android=success`, `sync_ios=skipped`, `no_changes` unset, not cancelled.
- **(b)** Both ran: `sync_android=success`, `sync_ios=failure`, not cancelled.
- **(c)** Both skipped: `sync_android=skipped`, `sync_ios=skipped`, not cancelled.

<details><summary>Hint</summary>

It's one big AND — every line must be true. Remember a *skipped* step's outcome is `skipped`, not
`failure` and not `success`. `env.no_changes` unset is not the string `'true'`. The final clause
needs **at least one** `== 'success'`.
</details>

<details><summary>Solution</summary>

- **(a) TRUE — PR opens.** `!cancelled()`✓; `no_changes != 'true'`✓ (unset ≠ 'true'); android `!=
  'failure'`✓; ios `skipped != 'failure'`✓; last clause: android `== 'success'`✓ (OR is satisfied).
  This is exactly why the gate uses `!= 'failure'` — so a skipped iOS doesn't block an Android-only run.
- **(b) FALSE — PR skipped.** The clause `steps.sync_ios.outcome != 'failure'` is **false** (ios *did*
  fail), so the whole AND is false. A failed sync means Claude errored mid-edit — don't ship a
  half-done PR.
- **(c) FALSE — PR skipped.** Lines 1–4 pass (skipped ≠ failure), but the **last clause fails**:
  neither android nor ios is `'success'`. Both skipped = no real work, so no PR.
</details>

---

## Exercise 3 — Name all 3 Android touches + 2 iOS touches for a new JS method

**Task:** A new method `getUserEventLog(...)` was added in `www/CleverTap.js`. List every native edit
required to make it actually work — Android (3) and iOS (2) — and name the one thing that must be
identical across all sides.

<details><summary>Hint</summary>

On Android, a missed touch is a *silent no-op*, not a compile error. Two of the three Android touches
are in the same file. See the
[3-touch rule](../20-walkthroughs/orchestrator-prompt-cordova.md#key-section-4--the-android-3-touch-rule-a-loop-body-that-must-not-skip).
</details>

<details><summary>Solution</summary>

**Android — 3 touches:**
1. `src/android/CleverTapFunction.java` — add the **enum constant**.
2. `src/android/CleverTapPlugin.java` — add the **case in the `execute()` switch**.
3. `src/android/CleverTapPlugin.java` — add the **private implementation method**.

**iOS — 2 touches:**
1. The **`.h` declaration**.
2. The **`.m` implementation**.

**Must be identical across all sides:** the **action string** — used by the JS `cordova.exec`, the
Android enum string, and the iOS selector. If they don't match, the call never reaches the native
method.

(And per the kit's house rule, the method also needs a runnable demo in **all four** sample apps.)
</details>

---

## Exercise 4 — Decode a piece of `_JAVA_PUBLIC_METHOD`

**Task:** Given the regex:

```python
_JAVA_PUBLIC_METHOD = re.compile(
    r"^\s*public\s+"
    r"(?!class\b|interface\b|enum\b|@interface\b|static\s+final\b)"
    r"([\w\<\>\[\],\s\?\.]+?)\s+"
    r"(\w+)\s*"
    r"\(([^)]*)\)"
)
```

Answer: (a) what do groups 1, 2, 3 capture? (b) what does the `(?!...)` piece do and why is it
needed? (c) why does the params group `[^)]*` contribute to the ~80% coverage limit?

<details><summary>Hint</summary>

See the [regex anatomy](../20-walkthroughs/diff-native-api/03-surface-extraction-java-kotlin.md#regex-anatomy--decode-_java_public_method-once-and-youve-got-it).
`(?!...)` is a *negative lookahead*. `[^)]` means "any char except `)`".
</details>

<details><summary>Solution</summary>

**(a)** Group 1 = **return type** (allows `<>`, `[]`, `,`, `?`, `.` so `List<String>` works), group 2
= **method name** (`\w+`), group 3 = **parameters** (everything between the parens).

**(b)** It's a **negative lookahead**: the line must NOT continue with `class`/`interface`/`enum`/
`@interface`/`static final`. Without it, `public class CleverTapAPI {` would be misread as a method.
It keeps matches to *methods only* (and excludes `static final` constants).

**(c)** `[^)]*` is "any chars except `)`", so it **cannot handle a `)` inside the parameters** (e.g.
a method reference). Combined with the line-oriented matching, things like Kotlin default args,
`@JvmOverloads`-generated overloads, and unusual wrapping slip past — that's the deliberate ~20%
miss, caught later by the changelog recall pass.
</details>

---

## Exercise 5 — Spot the bug: a public method is missing from the diff

**Task:** The native changelog clearly says `8.2.0` added `setLocaleLanguage(...)`, but the diff
tool's `added` bucket doesn't list it. List the likely causes (with rough probabilities), and name
the mechanism designed to catch this.

<details><summary>Hint</summary>

Where does the diff tool *find* methods, and what does it *deliberately filter out*? And what is the
"recall pass" for? See
[extraction](../20-walkthroughs/diff-native-api/03-surface-extraction-java-kotlin.md) and
[changelog cross-validation](../20-walkthroughs/diff-native-api/08-changelog-crossvalidation.md).
</details>

<details><summary>Solution</summary>

**Likely causes:**
- **~80%: a regex extraction miss.** The declaration wrapped across lines, was generated via
  `@JvmOverloads`, used Kotlin default params, or was formatted in a way the line-oriented regex
  didn't match — so it never entered either surface, and `compute_diff` can only sort what was
  extracted. `compute_diff` is **not** buggy.
- **~the rest: a restriction annotation.** If the method carried `@RestrictTo`/`@Hide`/`@Internal`/
  `@VisibleForTesting`, `_is_restricted` filtered it out on purpose (it shouldn't be surfaced).

**What catches it:** the **changelog recall pass**. It extracts method names from the changelog prose
and computes `changelog_only_methods = changelog_mentioned − (new_surface ∪ old_surface)`, printing a
`⚠️` for any name the changelog mentions but neither surface contains — making the parser miss
visible so a human (or Claude) source-verifies it.
</details>

---

## Exercise 6 — Walk the 3-tier source acquisition for a GitHub-only version

**Task:** The diff tool needs Android core source at `8.2.0`. There is **no local clone** and **no
cache** for it. Trace what `acquire_sources` does, step by step, naming the tag it builds and the
final fallback.

<details><summary>Hint</summary>

The three tiers, fastest-first: local clone → cache → download. `REPOS[(platform, module)]` gives the
repo + tag format. Android core tags look like `corev{ver}`. See
[source acquisition](../20-walkthroughs/diff-native-api/02-source-acquisition.md).
</details>

<details><summary>Solution</summary>

1. Look up `REPOS[("android","core")]` → repo `CleverTap/clevertap-android-sdk`, tag format
   `corev{ver}`.
2. Build the tag: `tag_fmt.format(ver="8.2.0")` → **`corev8.2.0`**. Short repo slug =
   `clevertap-android-sdk`.
3. **Tier 1 (local clone):** no `local_path` (or it lacks tag `corev8.2.0`) → fall through.
4. **Tier 2 (cache):** `cache_dir / "clevertap-android-sdk-corev8.2.0"` doesn't exist → fall through.
5. **Tier 3 (download):** `_download_and_extract` fetches
   `https://github.com/CleverTap/clevertap-android-sdk/archive/refs/tags/corev8.2.0.tar.gz`, unpacks
   it into a staging area, **strips the single top-level folder** GitHub wraps it in, and returns the
   destination as the source root. (If the tag didn't exist, it exits with a clear message pointing
   to the repo's tags page.)
</details>

---

## Exercise 7 — Decide the SemVer bump for a removed public method

**Task:** The diff for a sync shows a public method in the `removed` bucket (it existed in the old
version, gone in the new). What **SemVer bump** should the wrapper take, and why?

<details><summary>Hint</summary>

SemVer: MAJOR = breaking, MINOR = new backward-compatible features, PATCH = fixes only. A *removed*
public method is something host apps may already be calling. See [Glossary → SemVer](../GLOSSARY.md).
</details>

<details><summary>Solution</summary>

**A MAJOR bump.** Removing a public method is a **breaking change** — any host app calling it will
break when it upgrades. SemVer reserves MAJOR for exactly this. (Contrast: a new backward-compatible
method = MINOR; a fix-only release = PATCH.) The removal would also appear in `flagged_for_review`
with `type: "removal"` so a human consciously confirms the break, and the PR would carry a
`breaking-change` label.
</details>

---

## Exercise 8 — Map a symptom to cause and fix (build-failed label)

**Task:** A run finished and a PR exists, but it carries a **`build-failed`** label and a warning
banner; the run is red and Slack pinged. What happened, and what do you do?

<details><summary>Hint</summary>

Which build runs *after* Claude's edits? Is this fatal? See
[failure modes §2](../40-troubleshooting/01-failure-modes.md).
</details>

<details><summary>Solution</summary>

**Cause:** the **post-sync build failed** — Claude's edits didn't compile. By design ("Option A"),
the PR opens anyway rather than discarding the work; the `Flag post-sync build failure` step
(`always()`) turns the run red and pings Slack. A classic underlying cause is a referenced native
method/selector that doesn't actually exist.

**Fix (non-fatal, sometimes expected):** a human (1) pulls the branch locally, (2) fixes the compile
error, (3) pushes — the PR updates, (4) then reviews and merges as normal. Nothing was lost.
</details>

---

## Exercise 9 — Run a dry-run (skip_sync) sync mentally

**Task:** You want to confirm the build pipeline works after a toolchain bump, **without paying for
any AI**. Which flag do you set, what runs, what's skipped, and what does it cost?

<details><summary>Hint</summary>

See [dry-run and skip-sync](../30-runbook/05-dry-run-and-skip-sync.md). Which build still runs?
</details>

<details><summary>Solution</summary>

Set **`skip_sync = true`** in the trigger form (pick a real version pair so the build is meaningful).
The run **still executes the pre-sync build** (so you can iterate on the build pipeline) but
**skips** the AI Sync steps and the post-sync build → **$0 of AI cost**, a few minutes of CI. Perfect
for build-pipeline problems (missing config, dependency drift) that have nothing to do with the AI.
</details>

---

## Exercise 10 — Why is the diff tool separate from Claude?

**Task:** In 3–4 sentences, explain why the system has a deterministic Python diff tool (Layer ④) at
all, instead of just letting Claude read the SDK source and decide everything. Name the specific risk
the tool guards against and the rule Claude follows because of it.

<details><summary>Hint</summary>

Think about what an LLM can do that a regex parser cannot — and vice versa. "Librarian vs. editor."
See [the 4-layer onion](../00-primer/02-the-4-layer-onion.md).
</details>

<details><summary>Solution</summary>

An AI can **hallucinate** — confidently name a method or selector that doesn't exist, which for a
*compiled* bridge means a broken build. The diff tool is deterministic: it reports only what is
literally in the source, so it gives Claude a factual anchor it cannot make up. Claude is therefore
told to **trust the diff as ground truth** and to **source-verify** any symbol before writing a call
to it — and to **flag** anything it can't confirm rather than guess. The tool is the librarian (only
tells you what's truly on the shelf); Claude is the editor (decides what to publish) — kept honest by
the leash.
</details>

---

## Exercise 11 — Trace `claude-sync` capturing a Claude failure

**Task:** Inside the [`claude-sync` action](../20-walkthroughs/claude-sync-action.md), the
`claude -p` call exits non-zero. Walk what the shell does next, and what that ultimately does to the
PR.

<details><summary>Hint</summary>

Follow `set +e` → `rc=$?` → the `jq` extraction → the `if [ $rc -ne 0 ]` branch → `exit $rc`. Then
recall how the conductor's gates read this step's **outcome**.
</details>

<details><summary>Solution</summary>

1. `set +e` was on, so the non-zero exit doesn't abort the script.
2. `rc=$?` captures Claude's exit code; `set -e` restores strict mode.
3. `jq 'select(.type=="result")' | tail -1` still tries to write the result file (`|| true` so an
   empty stream doesn't fail the step).
4. `if [ $rc -ne 0 ]` is true → it prints `::error::`, dumps stderr and the last 50 stream events
   into log groups, then **`exit $rc`** — deliberately failing the step.
5. That makes the step's **outcome** `failure`. The conductor's commit/push/open-PR gates check
   `steps.sync_*.outcome != 'failure'`, so they **skip** — **no PR is opened from a broken sync.**
</details>

---

**Next:** [capstone.md — explain it back, unaided →](./capstone.md)
