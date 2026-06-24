# Drift checklist — what to re-check when the code changes

When you edit a source file, the docs that explain it can go stale. This table maps **each source
file → the docs that depend on it.** After changing a source file, re-read the listed pages, fix any
mismatch, and run `visual-explainer`'s `/fact-check` over them (log it in
[`fact-check-log.md`](./fact-check-log.md)).

> This table is the *lookup*. For the full **step-by-step** ("I changed a wrapper / created a new
> wrapper / changed the tooling source → what do I do, including the HTML?"), follow
> [`maintaining-the-docs.md`](./maintaining-the-docs.md).

> Tip: `visual-explainer`'s `/diff-review` takes a git diff and tells you which pages a change
> touches — a faster way to find the affected rows below.

## Source → docs map

| If you change… | Re-check these docs |
|----------------|---------------------|
| `tools/diff_native_api.py` — **acquire** section | `20-walkthroughs/diff-native-api/02-source-acquisition.md`; `10-diagrams/diff-tool-pipeline.mmd`, `diff-tool-callgraph.mmd` |
| `diff_native_api.py` — **extraction** (`_extract_java/_kotlin`, regexes) | `…/03-surface-extraction-java-kotlin.md`; flashcards (Python), `exercises.md` (regex decode) |
| `diff_native_api.py` — **Obj-C** extraction | `…/04-surface-extraction-objc.md` |
| `diff_native_api.py` — `compute_diff` | `…/05-diffing.md` |
| `diff_native_api.py` — Android/iOS **build manifest** | `…/06-build-manifest-android.md`, `…/07-build-manifest-ios.md`; `10-diagrams/diff-json-shape.mmd` |
| `diff_native_api.py` — **changelog** functions | `…/08-changelog-crossvalidation.md`; `40-troubleshooting/02-when-claude-misses-an-api.md` |
| `diff_native_api.py` — `write_outputs`/`_render_*` | `…/09-output-rendering.md`; `10-diagrams/diff-json-shape.mmd` |
| `diff_native_api.py` — `main()`/argparse | `…/10-main-orchestration.md`; `README.md` (the run command) |
| `.github/workflows/sync.yml` — steps/gating | `20-walkthroughs/sync-yml.md`; `10-diagrams/conductor-gating.mmd`, `end-to-end-sequence.mmd`; `30-runbook/03-read-the-run.md`; `exercises.md` (gating drill) |
| `.github/actions/claude-sync/action.yml` | `20-walkthroughs/claude-sync-action.md`; `10-diagrams/claude-sync-dataflow.mmd` |
| `.github/actions/build/cordova/action.yml` | `20-walkthroughs/build-cordova-action.md`; `40-troubleshooting/01-failure-modes.md` |
| `.github/actions/open-pr/` + `scripts/open-combined-pr.sh` (labels) | `30-runbook/04-review-the-pr.md`; `40-troubleshooting/*`; `exercises.md` (label recall) |
| `prompts/sync-orchestrator-cordova.md` | `20-walkthroughs/orchestrator-prompt-cordova.md`; `40-troubleshooting/02`, `03` |
| wrapper `.github/workflows/native-release-sync.yml` (inputs) | `20-walkthroughs/wrapper-dispatch.md`; `30-runbook/02-trigger-a-sync.md` |
| wrapper `.claude/skills/**` (conventions) | `10-diagrams/bridge-layers-cordova.mmd`; `20-walkthroughs/build-cordova-action.md`; `40-troubleshooting/03` |
| Any new jargon introduced anywhere | `GLOSSARY.md` + `50-retention/flashcards.md` |

## After any doc change

- [ ] All ` ```mermaid ` blocks and `.mmd` files still validate (Mermaid render tool / `/fact-check`).
- [ ] No dead relative links (the pages cross-link heavily).
- [ ] Regenerate the HTML layer if you publish it (`/generate-web-diagram`, `/generate-slides`).
- [ ] Append a line to [`fact-check-log.md`](./fact-check-log.md).

## Adding a new wrapper (flutter/react-native/future)

The kit is hub-centric. For a new wrapper, the only wrapper-specific docs are the **bridge diagram**
(`10-diagrams/bridge-layers-<wrapper>.mmd`) and any per-wrapper notes in the build walkthrough — plus
a thin pointer file in that wrapper repo (see the cordova example, `docs/ONBOARDING-POINTER.md`).
Everything else (diff tool, conductor, brain, retention) is shared.

**Next:** [fact-check-log.md →](./fact-check-log.md)
