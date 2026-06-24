# Shared spec for the HTML kit site (read before generating any page)

This makes ~35 self-contained HTML pages feel like ONE site. Every generated page MUST follow this.
(This file lives in the gitignored `docs/_generated/` and is a build-time spec, not shipped content.)

## Canonical look — match `system-overview.html`
Open `docs/_generated/system-overview.html` and **reuse its `<style>` block and its Mermaid
zoom/pan `<script>` verbatim** so every page is visually identical. That means:
- **Aesthetic:** Blueprint — light-first with a dark variant via `prefers-color-scheme`; faint
  two-axis grid background; precise low-opacity borders; monospace section labels with a leading
  hairline rule.
- **Fonts:** IBM Plex Sans (body) + IBM Plex Mono (labels/code). Load via Google Fonts `<link>`.
- **Palette:** deep blue `#1e3a5f` + gold `#b8860b` accents; semantic teal/amber/rose/green allowed.
- **Forbidden (AI slop):** Inter/Roboto; violet/indigo/fuchsia; cyan-magenta-pink; gradient text;
  glowing/pulsing shadows; emoji in section headers; three-dot code-window chrome.

## Every page's skeleton
```
<!DOCTYPE html><html lang="en"><head>… fonts + the shared <style> …</head>
<body>
  <!-- TOP NAV (same on every page) -->
  <nav class="kit-nav">
     <a href="index.html">◀ Onboarding Kit</a>
     <span class="crumb">SECTION · Page Title</span>
     <a href="NEXT_FILE.html">Next: Next Title ▶</a>   <!-- omit if last -->
  </nav>

  <main class="kit-content"> … the page content … </main>

  <!-- FOOTER NAV -->
  <footer class="kit-foot">
     <a href="PREV_FILE.html">◀ Prev Title</a>
     <a href="index.html">⌂ Kit home</a>
     <a href="NEXT_FILE.html">Next Title ▶</a>
  </footer>
</body></html>
```
Self-contained: only CDN links (fonts, mermaid). No browser auto-open, no Vercel, no git.

## Faithful content rendering rules
Translate the source Markdown into styled HTML — don't just dump it:
- **Headings/paragraphs/lists/tables** → semantic HTML; tables get the data-table styling (sticky
  header, subtle zebra rows, `<code>` in cells). Right-align numeric columns.
- **Code blocks** → a card with a small filename/language label header (NO traffic-light dots),
  `white-space: pre-wrap`, IBM Plex Mono. Keep the circled markers ①②③ intact. Do NOT lose any code.
- **🟦 "Beginner sidebar" blockquotes** → a distinct **callout box** (info style, blue tint).
- **🧠 analogy lines** → a callout box (gold/amber tint, lightbulb-free — use a styled label, not emoji).
- **⚠️ warning blocks** → a warning callout (rose tint).
- **"✅ Check yourself"** and any **`<details><summary>…</summary>…</details>`** → render as native
  HTML `<details>` (they fold/unfold in the browser). Style the summary as a clickable Q card.
  This interactivity is essential — preserve EVERY question and its folded answer.
- **```mermaid blocks and `.mmd` references** → use the FULL diagram-shell with zoom/pan (copy the
  structure + JS from `system-overview.html`). Never a bare `<pre class="mermaid">`. Pull the Mermaid
  source from the matching `docs/10-diagrams/*.mmd` when the page references one; otherwise from the
  embedded block.
- **Relative links between source pages** → rewrite to the corresponding generated `.html` filename
  (see the file map). Links to source code files (e.g. `tools/diff_native_api.py`) can stay as text
  or point to the repo path; don't break them.

## File map + reading order (use for prev/next links and index.html TOC)
Filenames are flat in `docs/_generated/`. Order = the fresher's path.

| # | File | Title | Section |
|---|------|-------|---------|
| 0 | `index.html` | Onboarding Kit — Start Here | (landing) |
| 1 | `primer-01-what-is-wrapper-sync.html` | What is wrapper-sync? | Primer |
| 2 | `primer-02-the-4-layer-onion.html` | The 4-Layer Onion | Primer |
| 3 | `primer-03-a-day-in-the-life.html` | A Day in the Life | Primer |
| 4 | `primer-04-repos-and-where-things-live.html` | Repos & Where Things Live | Primer |
| 5 | `glossary.html` | Glossary | Reference |
| 6 | `walk-README.html` | Walkthroughs — Overview & Ranking | Walkthroughs |
| 7 | `walk-diff-00-overview.html` | diff tool — Overview | Walkthroughs · diff tool |
| 8 | `walk-diff-02-source-acquisition.html` | diff tool — Source Acquisition | Walkthroughs · diff tool |
| 9 | `walk-diff-03-surface-extraction-java-kotlin.html` | diff tool — Java/Kotlin Extraction | Walkthroughs · diff tool |
| 10 | `walk-diff-04-surface-extraction-objc.html` | diff tool — Obj-C Extraction | Walkthroughs · diff tool |
| 11 | `walk-diff-05-diffing.html` | diff tool — Diffing | Walkthroughs · diff tool |
| 12 | `walk-diff-06-build-manifest-android.html` | diff tool — Android Build Manifest | Walkthroughs · diff tool |
| 13 | `walk-diff-07-build-manifest-ios.html` | diff tool — iOS Build Manifest | Walkthroughs · diff tool |
| 14 | `walk-diff-08-changelog-crossvalidation.html` | diff tool — Changelog Cross-validation | Walkthroughs · diff tool |
| 15 | `walk-diff-09-output-rendering.html` | diff tool — Output Rendering | Walkthroughs · diff tool |
| 16 | `walk-diff-10-main-orchestration.html` | diff tool — main() | Walkthroughs · diff tool |
| 17 | `walk-sync-yml.html` | The Conductor (sync.yml) | Walkthroughs |
| 18 | `walk-claude-sync-action.html` | The Brain (claude-sync) | Walkthroughs |
| 19 | `walk-build-cordova-action.html` | The Cordova Build Action | Walkthroughs |
| 20 | `walk-orchestrator-prompt-cordova.html` | Reading the Prompt as a Program | Walkthroughs |
| 21 | `walk-wrapper-dispatch.html` | The Trigger Form | Walkthroughs |
| 22 | `runbook-01-prerequisites.html` | Runbook — Prerequisites | Runbook |
| 23 | `runbook-02-trigger-a-sync.html` | Runbook — Trigger a Sync | Runbook |
| 24 | `runbook-03-read-the-run.html` | Runbook — Read the Run | Runbook |
| 25 | `runbook-04-review-the-pr.html` | Runbook — Review the PR | Runbook |
| 26 | `runbook-05-dry-run-and-skip-sync.html` | Runbook — Dry Run & skip_sync | Runbook |
| 27 | `trouble-01-failure-modes.html` | Troubleshooting — Failure Modes | Troubleshooting |
| 28 | `trouble-02-when-claude-misses-an-api.html` | Troubleshooting — Missed API | Troubleshooting |
| 29 | `trouble-03-source-verification-failures.html` | Troubleshooting — Source Verification | Troubleshooting |
| 30 | `trouble-04-cost-and-caps.html` | Troubleshooting — Cost & Caps | Troubleshooting |
| 31 | `trouble-05-faq.html` | Troubleshooting — FAQ | Troubleshooting |
| 32 | `retention-README.html` | Retention — How to Lock It In | Retention |
| 33 | `retention-flashcards.html` | Flashcards | Retention |
| 34 | `retention-exercises.html` | Exercises | Retention |
| 35 | `retention-capstone.html` | Capstone | Retention |
| 36 | `retention-graduation-checklist.html` | Graduation Checklist | Retention |

`index.html` also links (under "Big picture") to the existing `system-overview.html` (diagrams) and
`onboarding-slides.html` (deck). Prev of #1 = index; Next of #36 = index (or none).

Source markdown lives at the obvious paths: primer `docs/00-primer/`, walkthroughs
`docs/20-walkthroughs/` (diff pages under `diff-native-api/`), runbook `docs/30-runbook/`,
troubleshooting `docs/40-troubleshooting/`, retention `docs/50-retention/`, glossary `docs/GLOSSARY.md`.
