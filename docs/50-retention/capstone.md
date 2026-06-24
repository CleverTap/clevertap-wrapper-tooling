# Capstone — explain it back, unaided

> This is the exam. **Close the other tabs.** Do every part *before* opening any fold. If you can
> finish this with no notes, you've passed the "woken at 2am" test — you understand wrapper-sync, not
> just recognize it.

Three parts: (A) fill in the end-to-end flow, (B) answer the scenarios, (C) write a 5-sentence
plain-English summary. Model answers are folded.

---

## Part A — Fill in the end-to-end flow

Complete each blank `____` from memory. This is the whole system as a skeleton.

1. A maintainer opens the **wrapper** repo's Actions tab, runs `____` (the file), fills a form
   (versions + secrets) and clicks Run. This is **Layer ① ____**.
2. That file does almost nothing itself — it `____` the hub's `sync.yml`. The hub repo is named `____`.
3. `sync.yml` is **Layer ② ____**. Its cleverness is not domain knowledge — it's `____` (deciding
   which steps run via `if:` conditions).
4. Setup mints a short-lived `____` for the `____` GitHub App, checks out the wrapper, and makes a
   fresh `____` (e.g. `task/release_<name>`).
5. The **pre-sync build** runs *before* any AI. If it fails, the run stops and `____` of AI cost is
   spent.
6. The conductor hands a rendered prompt to `____` — **Layer ③ ____** — invoked headless as `____`.
7. Claude first runs `____` (**Layer ④ ____**), reads `diff.json` as `____`, then does the `____`
   pass over the changelog to catch the ~`____`% the regex missed.
8. Before writing any native call, Claude must `____` the symbol in real source; if it can't, it puts
   the item in `____` instead of guessing.
9. For each surfaced Android method it makes `____` touches; for iOS, `____` touches; and the `____`
   string must match across JS, Android, and iOS.
10. The **post-sync build** runs. A failure is `____` (fatal / non-fatal) — the PR still opens with a
    `____` label.
11. The conductor commits, pushes, and opens a `____` (the system's output, every time) with labels
    and a `____` comment.
12. A `____` reviews and merges. The automation does the tedious 90%; this step is never automated away.

<details><summary>Answers</summary>

1. `native-release-sync.yml`; **Trigger**.
2. **calls**; `clevertap-wrapper-tooling`.
3. **Conductor**; **gating**.
4. **token**; `clevertap-wrapper-sync`; **branch**.
5. **$0**.
6. **Claude**; **Brain**; `claude -p "<prompt>"`.
7. `diff_native_api.py` (the diff tool); **Ground truth**; **ground truth**; **recall**; ~**20**%.
8. **source-verify** (find it in source); `flagged_for_review` (type `unconfirmed`).
9. **3** (enum constant + `execute()` case + private method); **2** (`.h` declaration + `.m`
   implementation); **action** string.
10. **non-fatal**; `build-failed`.
11. **pull request**; **cost**.
12. **human** (maintainer).
</details>

---

## Part B — Scenario questions

Answer each in 2–4 sentences before opening the fold.

### B1. A run opened a PR with a `build-failed` label. What happened, and what do you do?

<details><summary>Model answer</summary>

The **post-sync build failed** — Claude's edits didn't compile. By design the PR opens anyway (rather
than discarding the work), gets the `build-failed` label and a warning banner, and the run goes red
(Slack may ping). It's **non-fatal**: a human pulls the branch, fixes the compile error, pushes
(updating the PR), then reviews and merges. A common underlying cause is a referenced native
method/selector that doesn't actually exist.
</details>

### B2. Claude flagged a method `for_review` (type `unconfirmed`). Why might that be?

<details><summary>Model answer</summary>

Claude couldn't **source-verify** the symbol — it was named in the changelog (or implied by the diff)
but Claude could not find the exact method/selector in the native source at the new version. The rule
is "verify or flag — never guess," because guessing a non-existent symbol would break the build. So
it raised a flag for a human to confirm rather than writing an unconfirmed call. "A flagged gap is
recoverable; a guessed selector is a broken build."
</details>

### B3. The run stopped at the pre-sync build with $0 cost and no PR. Is this a sync bug?

<details><summary>Model answer</summary>

No. The example app was **already broken on `base_ref`** before any AI changes; the pre-sync gate
exists to catch exactly this and fail fast so no AI money is wasted. It's a **build-pipeline** problem
(e.g. missing `google-services.json`, a stale lockfile, toolchain/SDK drift), not a sync problem. Fix
the build — iterating cheaply with `skip_sync=true` ($0 AI) — then retry.
</details>

### B4. A sync ran and succeeded but produced no meaningful diff / no PR. Why?

<details><summary>Model answer</summary>

You asked to sync to a version that's **already pinned** in the wrapper, so Claude correctly found no
work to do and exited cleanly; the Commit step set `no_changes=true`, and the Push/Open-PR gates
refuse to run on an empty diff. This is *correct behavior*, not a bug. Pick a target version that
genuinely differs (or use a rolled-back `base_ref` baseline) to see the full pipeline.
</details>

### B5. The native changelog names a new method, but it's absent from the diff's `added` bucket. What's going on, and what catches it?

<details><summary>Model answer</summary>

The diff tool finds methods with **regex (~80% coverage)**, so the declaration likely slipped past
(multi-line signature, `@JvmOverloads`, Kotlin default params, odd formatting) — or it carried a
restriction annotation (`@RestrictTo`/`@Hide`) and was filtered out on purpose. `compute_diff` can
only sort what was extracted, so it isn't buggy. The **changelog recall pass** catches it: names the
changelog mentions but neither surface contains become `changelog_only_methods` with a `⚠️`, so a
human/Claude source-verifies them.
</details>

### B6. Setup failed with `Invalid keyData` and no PR opened. Cause and fix?

<details><summary>Model answer</summary>

The GitHub App's **private key newlines were mangled** when pasted into the secret, so token minting
failed immediately and nothing downstream could run. Re-paste the exact `.pem` bytes
(`cat key.pem | pbcopy`) and verify the key before saving the secret. (Other setup failures: App not
installed on the repo, a missing required secret, or a `task/release_<name>` branch left over from a
prior run — use a unique `release_name`.)
</details>

---

## Part C — The 5-sentence summary

**Task:** Without notes, write a **5-sentence** plain-English summary of the whole system — what it's
for, the four layers, the ground-truth/recall idea, and the output. Then compare.

<details><summary>Model answer</summary>

When CleverTap ships a new native Android/iOS SDK, wrapper-sync lets a maintainer click one button to
catch a wrapper (Cordova/RN/Flutter) up to it automatically. It's a **four-layer onion**: a Trigger
button in the wrapper repo calls a Conductor workflow (`sync.yml`) in the shared hub, which hands a
written prompt to the Brain (Claude, running headless), which leans on a Ground-truth Python tool
(`diff_native_api.py`) that reports exactly what changed. The diff tool is regex-based and catches
~80% of API changes, so Claude does a **recall pass** over the native changelog to catch the rest, and
must **source-verify** every native symbol before writing a call — flagging anything it can't confirm
rather than guessing. Claude writes the bridge code on all sides (JS + Android 3-touch + iOS 2-touch),
bumps versions, updates the changelog and all four sample apps; builds run before (fail fast, $0 AI)
and after (failure is non-fatal — the PR opens with a `build-failed` label). The output is always a
**pull request** a human reviews and merges — the automation does the tedious 90%, and the human
approval is never removed.
</details>

---

## Self-grade

- **Part A:** 10+/12 blanks correct → solid. Anything you missed → re-drill that
  [flashcard](./flashcards.md) topic.
- **Part B:** for each, did you name the *cause* AND the *action*? Vague "you fix it" doesn't count.
- **Part C:** did you hit all four layers, ground-truth/recall, source-verify, and "output is a PR"?

Cleared all three unaided? Go sign off on the [graduation checklist](./graduation-checklist.md).

---

**Next:** [graduation-checklist.md — the bar to be signed off →](./graduation-checklist.md)
