# Graduation checklist — the bar to be signed off

> The concrete bar a fresher must clear to be considered "fluent" in wrapper-sync. Tick each box only
> when you can do it **unaided** — no peeking at the docs. Group order: understand it → read its code
> → operate it. When every box is ticked and the [capstone](./capstone.md) is passed, get signed off.

> 🧠 A box is honest only if you could do it **woken at 2am**. "I read about it" is not a tick;
> "I can produce it from memory" is.

---

## Concepts (understand it)

- [ ] I can name the **four layers** in order and say what each does in one phrase
      (Trigger → Conductor → Brain → Ground truth). → [onion](../00-primer/02-the-4-layer-onion.md)
- [ ] I can state the **single most important idea**: the YAML wraps no APIs — Layer ② only sequences;
      Layer ③ (Claude) writes the code.
- [ ] I can explain **why the diff tool exists vs. Claude** (deterministic facts vs. hallucination
      risk; "librarian vs. editor").
- [ ] I can explain **ground truth vs. recall pass** and the ~80% / ~20% split.
- [ ] I can explain why the **output is always a PR** and the human approval is never removed.
- [ ] I can explain **why the pre-sync build runs first** (fail fast, $0 AI) and why a **post-sync
      failure is non-fatal**.
- [ ] I can correctly use the triage vocabulary: **surfaced / skipped / deferred / flagged for review**.
- [ ] I can decide a **SemVer bump** from a diff (removed public method → MAJOR; new method → MINOR;
      fixes → PATCH).
- [ ] I know the only real labels in play: `auto-generated`, `new-api`, `bug-fix-only`,
      `breaking-change`, `build-failed`, `incomplete-sync`.

## Code reading (read its code)

- [ ] I can read a `sync.yml` **gating expression** and predict true/false across scenarios — and say
      why it uses `!= 'failure'` not `== 'success'`, and what `!cancelled()` buys.
      → [sync.yml](../20-walkthroughs/sync-yml.md)
- [ ] I can trace `acquire_sources`' **three tiers** (local clone → cache → download) and build the
      right tag (e.g. `corev8.2.0`). → [source acquisition](../20-walkthroughs/diff-native-api/02-source-acquisition.md)
- [ ] I can decode `_JAVA_PUBLIC_METHOD`: groups 1/2/3 = return type / name / params, and what the
      negative lookahead does. → [extraction](../20-walkthroughs/diff-native-api/03-surface-extraction-java-kotlin.md)
- [ ] I can explain `compute_diff` as **set arithmetic** (`new - old`, `old - new`, signature-set
      compare) and why everything is `sorted()`. → [diffing](../20-walkthroughs/diff-native-api/05-diffing.md)
- [ ] I can explain the **changelog recall pass** and `changelog_only_methods`, including why version
      strings are parsed to tuples of ints. → [cross-validation](../20-walkthroughs/diff-native-api/08-changelog-crossvalidation.md)
- [ ] I can name the **3 Android touches + 2 iOS touches** and explain the "silent no-op" risk.
      → [orchestrator prompt](../20-walkthroughs/orchestrator-prompt-cordova.md)
- [ ] I can read the `claude-sync` `run:` block: `set +e` → `rc=$?` → `jq result` → `exit $rc`, and
      what that does to the PR gates. → [claude-sync](../20-walkthroughs/claude-sync-action.md)
- [ ] I can locate the **real conventions** in the wrapper's `.claude/skills/` (version-detection,
      api-wrapper-patterns, native-sdk-changelog-analysis, example-app-patterns, changelog-generation,
      ionic-native-typings) and say how a **prompt** differs from a **skill**.
      → [repos & where things live](../00-primer/04-repos-and-where-things-live.md)

## Operations (operate it)

- [ ] I can describe the **trigger form** inputs and run an Android-only vs. both-platform sync.
- [ ] I can run a **dry-run (`skip_sync=true`)** and say exactly what runs (pre-sync build) and what's
      skipped (AI sync + post-sync build), at **$0 AI**. → [dry-run](../30-runbook/05-dry-run-and-skip-sync.md)
- [ ] I can explain a **`base_ref` baseline branch** and why a rolled-back branch beats an old release
      tag for testing.
- [ ] I can **read a run** and tell which step/layer a failure happened in, and find the uploaded
      **artifacts** (Claude output JSON / stream / stderr).
- [ ] I can map the four common **failure modes** symptom → cause → fix (pre-sync abort; `build-failed`
      PR; no-op/already-pinned; setup token/App/secret/branch). → [failure modes](../40-troubleshooting/01-failure-modes.md)
- [ ] I know the system needs **four secrets** (App ID, App private key, Anthropic key, Slack URL) and
      that the App only has permissions on repos it's installed on.

## The exam

- [ ] I completed the [**capstone**](./capstone.md) — Parts A, B, and C — **unaided**.
- [ ] I drilled the [**flashcards**](./flashcards.md) and got the domain, triage, and 4-layer cards
      cold.
- [ ] I did the [**exercises**](./exercises.md) hands-on (not just read the solutions).

---

## Sign-off

| Field | Value |
|-------|-------|
| Fresher name | __________________________ |
| Capstone completed (date) | __________________________ |
| Reviewer / signed off by | __________________________ |
| Sign-off date | __________________________ |
| Notes / areas to revisit | __________________________ |

> Once signed off, you're cleared to **review a real wrapper-sync PR** (and to pair on running one).
> The next native release is your first solo trace — from click to merge.

---

**Next:** back to the [kit README](../README.md) — or revisit any walkthrough you fumbled above.
