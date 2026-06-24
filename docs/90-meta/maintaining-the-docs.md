# Maintaining the docs when code changes

> **Who this is for:** a new joinee who just changed some code and needs to keep the onboarding kit
> (the Markdown pages *and* the generated HTML) correct. Follow the scenario that matches what you did.

> 🤖 **Prefer to let Claude do it?** Run the **`update-docs` skill**
> (`.claude/skills/update-docs/`) — it automates this whole playbook: it reads your git diff, finds
> the affected pages, surgically updates the Markdown **and** HTML, re-hardens changed diagrams, and
> verifies. This page is the manual version / the skill's reference.

## The golden rules (read once)

1. **Markdown + Mermaid (`docs/**`) are the source of truth.** They render on GitHub and feed both
   the HTML and the interactive tutor. Always edit these first.
2. **The HTML in `docs/_generated/` is generated output** — never hand-edit it. It's gitignored.
   You *regenerate* it from the Markdown, then run the **inline-SVG hardening** pass so diagrams work
   offline (see [`how-this-kit-is-built.md`](./how-this-kit-is-built.md)).
3. **Diagrams are Mermaid text**, committed in `docs/10-diagrams/*.mmd` and in fenced ```mermaid
   blocks inside pages. Edit the text; never edit a rendered SVG.
4. **Anchor explanations on symbol names, not line numbers** (e.g. `acquire_sources`, not "line 156").
5. **When in doubt about *what* to re-check, use [`drift-checklist.md`](./drift-checklist.md)** — it maps
   every source file to the docs that depend on it.

The three scenarios below all end with the **same two shared procedures** (Validate, Regenerate &
Harden HTML), written once at the bottom. Don't skip them.

---

## Scenario A — You changed an existing wrapper repo
*(e.g. edited the Cordova bridge, a `.claude/skill`, the dispatch workflow, or version locations in
`clevertap-cordova` / `clevertap-flutter` / `clevertap-react-native`.)*

1. **Find the affected pages.** Open [`drift-checklist.md`](./drift-checklist.md) and look up the
   file(s) you changed. Typical hits:
   - bridge code / `.claude/skills` → `10-diagrams/bridge-layers-<wrapper>.mmd`,
     `20-walkthroughs/build-<wrapper>-action.md`, `40-troubleshooting/03-source-verification-failures.md`
   - dispatch `native-release-sync.yml` (inputs) → `20-walkthroughs/wrapper-dispatch.md`,
     `30-runbook/02-trigger-a-sync.md`
   - version locations → `30-runbook/04-review-the-pr.md` and any version-count mention
2. **Edit those Markdown pages** so they match the new reality. Keep the page's format (shape diagram
   → annotated code → table → 🟦 sidebars → ✅ Check yourself). If you quoted code that changed,
   re-paste the real code (trimmed, keep the ①②③ markers).
3. **New jargon?** Add it to [`../GLOSSARY.md`](../GLOSSARY.md) **and** a flashcard in
   [`../50-retention/flashcards.md`](../50-retention/flashcards.md).
4. **Wrapper-specific diagram changed?** (e.g. a new Android touch) → edit
   `10-diagrams/bridge-layers-<wrapper>.mmd`.
5. Run **Shared Procedure 1 (Validate)** and **Shared Procedure 2 (Regenerate & Harden HTML)**.

---

## Scenario B — You created a NEW wrapper
*(e.g. `clevertap-unity`. First make it work in the automation — see the hub skill
`.claude/skills/onboard-wrapper-sync/SKILL.md` — then document it here.)*

The kit is **hub-centric**: the 4-layer model, diff tool, conductor, and retention are shared, so most
of the kit needs **no change**. You only add the wrapper-specific bits:

1. **Bridge diagram.** Create `10-diagrams/bridge-layers-<wrapper>.mmd` showing that wrapper's bridge
   (how its language calls Android/iOS). Copy `bridge-layers-cordova.mmd` as a starting shape.
2. **Build-action walkthrough (optional but recommended).** If its CI build has quirks, add
   `20-walkthroughs/build-<wrapper>-action.md` (model it on `build-cordova-action.md`).
3. **Thin pointer in the new wrapper repo.** Add `<new-wrapper-repo>/docs/ONBOARDING-POINTER.md`
   pointing back to this hub kit (copy `clevertap-cordova/docs/ONBOARDING-POINTER.md`, swap the
   wrapper-specific lines: its `.claude/skills`, its dispatch path, its bridge diagram).
4. **Mention it where wrappers are listed.** Edit
   [`../00-primer/04-repos-and-where-things-live.md`](../00-primer/04-repos-and-where-things-live.md)
   to include the new wrapper. Glance at `docs/README.md` and the GLOSSARY's "Wrapper SDK" entry —
   update if they enumerate wrappers.
5. **New jargon** (e.g. Unity's C#/IL2CPP terms) → [`../GLOSSARY.md`](../GLOSSARY.md) + a flashcard.
6. **Add a drift-checklist row** in [`drift-checklist.md`](./drift-checklist.md) mapping the new
   wrapper's source files → the new docs.
7. Run **Shared Procedure 1** and **Shared Procedure 2**.

> You do **not** need to duplicate the primer, diff-tool walkthroughs, runbook, troubleshooting, or
> retention for a new wrapper — those are shared. Only the bridge + pointer + a mention.

---

## Scenario C — You changed the wrapper-tooling source (this hub repo)
*(e.g. `tools/diff_native_api.py`, `.github/workflows/sync.yml`, a composite action under
`.github/actions/`, a prompt in `prompts/`, or a script in `scripts/`.)*

This is the highest-impact case — the walkthroughs explain this code line-by-line, so they drift easily.

1. **Map the change to pages.** Use [`drift-checklist.md`](./drift-checklist.md). Common ones:
   - `diff_native_api.py` (a given section) → the matching `20-walkthroughs/diff-native-api/0X-*.md`
     page **and** the related `10-diagrams/diff-*.mmd`
   - `sync.yml` gating → `20-walkthroughs/sync-yml.md` + `10-diagrams/conductor-gating.mmd` +
     `10-diagrams/end-to-end-sequence.mmd` + `30-runbook/03-read-the-run.md`
   - `claude-sync` action → `20-walkthroughs/claude-sync-action.md` + `10-diagrams/claude-sync-dataflow.mmd`
   - `prompts/sync-orchestrator-*.md` → `20-walkthroughs/orchestrator-prompt-cordova.md`,
     `40-troubleshooting/02` & `03`
   - `scripts/open-combined-pr.sh` (labels) → `30-runbook/04-review-the-pr.md`, `exercises.md`
2. **Tip:** if `visual-explainer` is installed, run **`/diff-review`** on your git diff — it tells you
   which pages a change touches.
3. **Update the Markdown.** For a line-by-line walkthrough page: re-quote the real code (trimmed, keep
   ①②③ markers), fix the annotation table, and update the shape diagram if control/data flow changed.
   Update the matching `.mmd` if the diagram is now wrong.
4. **Re-quoted code must be verbatim** from the current source — open the file and copy; don't
   reconstruct from memory. If `visual-explainer` is installed, run **`/fact-check`** on the page
   against the source to catch mismatches.
5. **New jargon** → GLOSSARY + flashcard. **New failure mode** → a `40-troubleshooting/` page + a
   `50-retention/exercises.md` drill if it's instructive.
6. Run **Shared Procedure 1** and **Shared Procedure 2**.

---

## Shared Procedure 1 — Validate (Markdown side)

Run from the repo root (`clevertap-wrapper-tooling/`):

- **Mermaid still valid?** Validate every `.mmd` you touched and every ```mermaid block on edited
  pages (use the Mermaid render tool / `visual-explainer` `/fact-check`, or just confirm it renders in
  GitHub's preview). A broken diagram blocks the HTML step.
- **No dead links?** The pages cross-link heavily. Quick check:
  ```bash
  python3 - <<'PY'
  import re, pathlib
  root = pathlib.Path("docs")
  link = re.compile(r'\[[^\]]+\]\(([^)#?]+\.md)(?:[#?][^)]*)?\)')
  bad = []
  for md in root.rglob("*.md"):
      for m in link.finditer(md.read_text(encoding="utf-8", errors="replace")):
          t = m.group(1)
          if t.startswith(("http", "mailto:")): continue
          if not (md.parent / t).resolve().exists(): bad.append((str(md), t))
  print("dead links:", bad or "none ✔")
  PY
  ```
  *(This flags real `.md` links; ignore hits that are regex/code inside fenced blocks.)*
- **`fact-check` log:** append a row to [`fact-check-log.md`](./fact-check-log.md) noting what you
  changed and that you verified it.

## Shared Procedure 2 — Regenerate & Harden the HTML

The HTML in `docs/_generated/` must be rebuilt for any page you changed, then hardened so diagrams
work offline. Full details: [`how-this-kit-is-built.md`](./how-this-kit-is-built.md).

1. **Regenerate the affected page(s).** With `visual-explainer` installed (after a Claude Code
   restart its `/` commands load): re-run the relevant generator over the updated Markdown into
   `docs/_generated/`. For a quick refresh of one page, regenerating just that page is fine.
2. **Harden: inline the diagram SVGs (do NOT skip).** Run the inline-SVG post-step from
   `how-this-kit-is-built.md` on the regenerated page(s): render each diagram to SVG, inject it into
   the `.mermaid-canvas`, and strip the CDN/module loader. Without this, diagrams hang on "Loading…"
   offline / on `file://` in Safari / in preview webviews.
3. **Verify the whole folder** (catches a page that slipped back to the CDN):
   ```bash
   cd docs/_generated
   echo "CDN refs (want 0):";        grep -l 'cdn.jsdelivr' *.html || echo "  none ✔"
   echo "module loaders (want 0):";  grep -l 'type=\"module\"' *.html || echo "  none ✔"
   echo "pages missing inline svg:"; for f in $(grep -l 'diagram-source\|class=\"mermaid\"' *.html); do \
       grep -q '<svg' "$f" || echo "  $f"; done; echo "  (blank = all good ✔)"
   ```
4. **Spot-check** one regenerated page in a browser, **offline** (turn off Wi-Fi or open via
   `file://`): the diagrams should appear immediately, and zoom/pan should work.

---

## When you're done

- Commit the **Markdown/Mermaid** changes (the `docs/_generated/` HTML is gitignored and stays out of
  the commit — it's regenerable build output).
- If you changed the kit's structure (new pages/sections), update `docs/README.md`'s table of
  contents and, for the HTML site, `docs/_generated/index.html`'s TOC + the prev/next chain
  (the file map lives in `docs/_generated/_site-spec.md`).

> 🧠 **The one-line mental model:** *edit Markdown → validate → regenerate HTML → harden (inline SVG)
> → verify → commit Markdown.* The HTML is always downstream of the Markdown.

**Next:** [drift-checklist.md →](./drift-checklist.md) · [how-this-kit-is-built.md →](./how-this-kit-is-built.md)
