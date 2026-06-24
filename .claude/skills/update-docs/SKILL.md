---
name: update-docs
description: >
  Keep the onboarding kit under docs/ in sync after code changes. Use after
  editing a CleverTap wrapper repo (clevertap-cordova / -flutter / -react-native)
  or the wrapper-tooling hub source (tools/diff_native_api.py, .github/workflows,
  .github/actions, prompts/, scripts/) — it finds the affected docs from a git
  diff, surgically updates BOTH the Markdown and the generated HTML pages,
  re-hardens any changed diagrams to inline SVG, verifies, and logs. Also handles
  adding docs for a brand-new wrapper or a new tooling file.
---

# update-docs — keep the onboarding kit correct after code changes

The onboarding kit lives in `docs/`. It has two representations that must agree:

- **Markdown + Mermaid** (`docs/**/*.md`, `docs/10-diagrams/*.mmd`) — the **source of truth**; renders on GitHub.
- **Generated HTML site** (`docs/_generated/*.html`) — the hosted, self-contained Blueprint-styled pages with **inline-SVG** diagrams. Gitignored, but **shipped by hosting**, so it must stay correct.

Your job when invoked: take a code change and bring **both** representations back in sync, the cheap
and safe way — **surgical edits to only the affected pages**, never a full regenerate.

> ⚠️ **Cost note (by design):** updating the HTML uses the LLM (you). That trade was chosen to keep
> the bespoke design. So **be surgical**: touch only the pages the change actually affects. A typical
> single-file change should edit a handful of pages, not the whole site.

> 📚 **This skill operationalizes the human playbook.** Read these before acting; do not duplicate
> their content — follow them:
> - `docs/90-meta/maintaining-the-docs.md` — the step-by-step playbook (the three scenarios).
> - `docs/90-meta/drift-checklist.md` — the **source-file → affected-docs** map (your routing table).
> - `docs/90-meta/how-this-kit-is-built.md` — the **inline-SVG hardening** procedure for HTML diagrams.
> - `docs/_generated/_site-spec.md` — the HTML **style/format/nav contract** + the page **file-map**.
> - `references/html-surgical-edits.md` (in this skill) — how to edit the HTML surgically.

---

## Workflow

### 1. Detect what changed
- **Hub changes:** in `clevertap-wrapper-tooling`, run `git diff` for the relevant range. Default to
  `git diff origin/main...HEAD`; if the user gives a range/refs or names files, use those. Also check
  uncommitted work: `git status -s` + `git diff` / `git diff --staged`.
- **Wrapper changes:** the wrapper repos are local siblings at
  `~/codebases/clevertap/clevertap-{cordova,flutter,react-native}` (and any new one). Run `git diff`
  there to see what changed in a wrapper's bridge code, `.claude/skills`, dispatch workflow, or
  version locations.
- The user may instead **describe** the change in prose — accept that and skip the diffing.
- Produce a concrete **list of changed source files/areas**. If nothing relevant changed, say so and stop.

### 2. Map changes → affected docs
For each changed file, look it up in `docs/90-meta/drift-checklist.md` to get the exact pages,
`.mmd` diagrams, glossary entries, and flashcards that depend on it. Build the **work list** of
`docs/**/*.md` pages to edit (and their `docs/_generated/*.html` counterparts via the file-map in
`docs/_generated/_site-spec.md`). When unsure whether a page is affected, open it and check.

### 3. Update the Markdown (the judgment step)
For each affected `.md` page, make **targeted** edits that keep the page's established format:
**shape diagram → annotated code → annotation table → 🟦 beginner sidebars → ✅ Check-yourself**.
- **Re-quote real, current code** from the source file (open it; copy verbatim, trimmed with `...`,
  keep the circled ①②③ markers). Never reconstruct code from memory.
- Fix the **annotation table** rows that reference changed lines.
- If control/data flow changed, update the page's `.mmd` (or embedded ```mermaid block) and the
  matching standalone file in `docs/10-diagrams/`.
- **New jargon** → add to `docs/GLOSSARY.md` **and** a flashcard in `docs/50-retention/flashcards.md`.
- **New failure mode** → add to the right `docs/40-troubleshooting/*.md` (and an exercise if instructive).
- Keep explanations anchored on **symbol names, not line numbers** (mark any line span "approx").

### 4. Update the HTML — surgically (see `references/html-surgical-edits.md`)
For each Markdown page you changed, open its `docs/_generated/<page>.html` counterpart (file-map in
`_site-spec.md`) and apply the **same** change **in place**:
- Locate the matching section/code-card/annotation-table/callout and edit just that.
- **Keep the rest of the file byte-identical.** Do not re-flow, re-theme, or regenerate the page.
  After editing, `git diff` (or a visual diff) should show only the intended lines.
- Match the existing HTML shapes (code-card header, callout boxes, `<details>` Q-cards) — the contract
  is in `_site-spec.md`; the mechanics are in `references/html-surgical-edits.md`.

### 5. Re-harden changed diagrams to inline SVG
Only if a diagram's source changed:
- Render the **new** Mermaid source to SVG with the Mermaid render MCP tool
  (`mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram`). Confirm `valid:true`. If the
  source has literal angle brackets like `<module>` and the renderer throws a `TAGSTART` parse error,
  HTML-escape `<`/`>` in the copy you send the renderer only.
- Replace the old inline `<svg>…</svg>` inside that page's `.mermaid-canvas` with the new one. **Do not
  hand-write SVG** and **do not** reintroduce a CDN `import`/`<script type="module">` — the page must
  stay offline-safe. Full procedure: `docs/90-meta/how-this-kit-is-built.md`. Keep large SVG strings in
  files/scripts, not in your reply.

### 6. Verify (always)
From the repo root:
- **Dead links:** run the checker from `docs/90-meta/maintaining-the-docs.md` (Shared Procedure 1) over `docs/`.
- **Offline-safe HTML:** `grep -l 'cdn.jsdelivr' docs/_generated/*.html` → none; `grep -l 'type="module"' docs/_generated/*.html` → none.
- **Diagrams present:** each touched diagram page still contains an inline `<svg`.
- **Mermaid valid:** any changed `.mmd`/block validates.
Fix anything that fails before finishing.

### 7. Log
Append a row to `docs/90-meta/fact-check-log.md`: date, what changed, pages touched, result (`clean`
or what you fixed).

---

## Scope handlers

### A — Update existing pages on code change
The default path above (steps 1–7).

### B — A brand-new wrapper was added (e.g. Expo, Unity)
The kit is hub-centric, so most pages need no change. Add only the wrapper-specific bits (mirrors
Scenario B in `docs/90-meta/maintaining-the-docs.md`):
1. `docs/10-diagrams/bridge-layers-<wrapper>.mmd` — copy `bridge-layers-cordova.mmd` and adapt to that
   wrapper's bridge.
2. Optional `docs/20-walkthroughs/build-<wrapper>-action.md` if its CI build has quirks (model on
   `build-cordova-action.md`).
3. The wrapper repo's `docs/ONBOARDING-POINTER.md` (copy `clevertap-cordova/docs/ONBOARDING-POINTER.md`,
   swap its `.claude/skills`, dispatch path, and bridge-diagram references).
4. A mention in `docs/00-primer/04-repos-and-where-things-live.md` (and the GLOSSARY "Wrapper SDK"
   entry / `docs/README.md` if they enumerate wrappers).
5. New jargon → GLOSSARY + flashcard. A new `docs/90-meta/drift-checklist.md` row for the wrapper.
6. Generate the matching **HTML** for any new MD page, add it to `docs/_generated/index.html`'s TOC and
   the file-map + prev/next in `docs/_generated/_site-spec.md`, harden its diagrams (step 5), verify (step 6).

### C — A new tooling file was added to the hub
Scaffold a new walkthrough:
1. New `docs/20-walkthroughs/<file>.md` from the 4-zone template (exemplars:
   `docs/20-walkthroughs/diff-native-api/{00,02,03}*.md`).
2. Its `docs/_generated/walk-<file>.html`, wired into `index.html` TOC + `_site-spec.md` file-map +
   prev/next; harden diagrams; verify.
3. Add the new source file → page row to `docs/90-meta/drift-checklist.md`.

---

## Rules of thumb
- **Surgical, not wholesale.** Edit only what the change touches; keep everything else identical.
- **Source is ground truth.** Quote real code/YAML from the current files; never invent symbols.
- **MD and HTML say the same thing.** Make the same edit in both; don't let them diverge.
- **HTML stays offline-safe.** Inline SVG only; never a CDN/module loader.
- **Validate `<...>` in diagrams** through the renderer before injecting (TAGSTART trap).
- **Log every run** to `fact-check-log.md`.
- **Stop and ask** if a change is ambiguous (e.g., a behavior change with no obvious doc home) rather
  than guessing.

## Done checklist (report this)
- [ ] Changed files identified (and from which repo)
- [ ] Affected pages mapped via `drift-checklist.md`
- [ ] Markdown updated (code re-quoted from source; tables/diagrams/glossary/flashcards fixed)
- [ ] HTML counterparts updated surgically (diff shows only intended lines)
- [ ] Changed diagrams re-hardened to inline SVG
- [ ] Verify passed (links, no cdn/module, inline svg present, mermaid valid)
- [ ] Logged to `fact-check-log.md`
