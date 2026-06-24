# How this kit is built (and how to keep it alive)

This page is for whoever **maintains** the onboarding kit — not the fresher learning from it.

## The two-layer design

The kit deliberately separates **truth** from **presentation**:

| Layer | What | Lives in | Edited by |
|-------|------|----------|-----------|
| **Source of truth** | Markdown pages + Mermaid diagrams (`.mmd` files and ` ```mermaid ` blocks) | `docs/**` (committed to git) | Humans, in pull requests |
| **Presentation** | Polished HTML / slide decks generated from the markdown | `docs/_generated/` (**gitignored**) | The `visual-explainer` plugin — never hand-edited |

**Rule:** only ever hand-edit the markdown and Mermaid. The HTML is build output. If you find
yourself editing generated HTML, stop — edit the source and regenerate.

> 🧠 **Analogy:** the `.md`/`.mmd` files are the *recipe*; the HTML is the *cooked dish*. You change
> the recipe and cook again — you don't carve the finished cake into a new shape.

## Why Mermaid-in-repo *and* visual-explainer?

- **Mermaid alone** is durable and reviewable (it renders right on GitHub, diffs cleanly in PRs) but
  plain-looking.
- **visual-explainer alone** is beautiful but its HTML is un-diffable and silently rots.
- **Together:** truth stays in git; beauty is regenerable. Best of both.

## Generating the HTML / slide layer

The `visual-explainer` plugin (third-party: `nicobailon/visual-explainer`) turns the committed docs
into self-contained HTML. Install once:

```
/plugin marketplace add nicobailon/visual-explainer
```

Then, from this repo, generate into the gitignored `docs/_generated/`:

- `/generate-web-diagram` — a polished, zoomable HTML version of a diagram (point it at a `.mmd` or
  a walkthrough page).
- `/generate-slides` — an onboarding deck (e.g. from `docs/00-primer/` + the end-to-end diagram).
- `/generate-visual-plan` — a visual roadmap of the learning path.
- `/project-recap` — a current-state snapshot of the automation.
- `/share-page` — (optional) deploy an HTML page to Vercel for a shareable URL.
  ⚠️ This **publishes externally** — only use it for internal, non-sensitive content.

The interactive *tutor* is separate from all this: it's `docs/ONBOARDING.md`, shared via Claude
Code's built-in `ShareOnboardingGuide`.

## ⚠️ Required post-step: inline the diagram SVGs (do not skip)

By default the generated HTML renders diagrams by importing `mermaid@11` from a CDN **at view
time** as an ES module (`<script type="module">`). That breaks in the most common ways a fresher
actually opens these files:

- **Offline** — no network, the import never resolves.
- **`file://` in Safari** (the default Mac browser) — Safari blocks ES-module imports from
  `file://` pages, so nothing renders.
- **Restricted/preview webviews** (IDE preview panes, sandboxed viewers) — remote modules blocked.

In every one of those, the diagram sits on **"Loading…"** forever with no error. To make the HTML
bulletproof, after generating, **pre-render each diagram to inline SVG** so the page needs no
network and no module. This is a one-pass post-process over `docs/_generated/`:

1. For each page, find every diagram source (`<script type="text/plain" class="diagram-source">`
   in walkthrough/primer pages; a `<pre class="mermaid">`/`<div class="mermaid">` in the slide deck).
2. Render each source to SVG (e.g. the Mermaid render MCP tool — it returns `rawSVG`; confirm
   `valid:true`. If a source has literal angle brackets like `<module>` it can trip the parser with a
   `TAGSTART` error — HTML-escape `<`/`>` in the copy you send to the renderer only, then re-render).
   Keep the large SVG strings in files / a script — don't pull them into the model's context.
3. Inject each SVG into its `.mermaid-canvas` (in document order), then **remove the CDN/module
   dependency** in the page's loader:
   - `<script type="module">` → `<script>`
   - delete the `import mermaid from 'https://cdn.jsdelivr.net/...'` line
   - delete the `mermaid.initialize({ ... });` call (keep `isDark`/`pageBg`)
   - replace `async function render() { ... }` with a version that reads the already-inlined SVG:
     ```js
     function render() {
       const svgNode = canvas.querySelector('svg');
       if (!svgNode) { label.textContent = 'Error: No diagram'; return; }
       const size = readSvgNaturalSize(svgNode);
       svgW = size.w; svgH = size.h;
       svgNode.removeAttribute('width'); svgNode.removeAttribute('height');
       svgNode.style.maxWidth = 'none'; svgNode.style.display = 'block';
       setAdaptiveHeight(); fitDiagram();
     }
     ```
   The zoom/pan helpers and event listeners stay unchanged — they now operate on the inline SVG.
   (For the slide deck, leave its own nav/zoom engine intact; only swap the Mermaid bits.)
4. **Verify** the whole folder: every page must have `grep -c cdn.jsdelivr` = 0,
   `grep -c 'type="module"'` = 0, and each diagram-bearing page must contain its inline `<svg>`.

> 🧠 **Why a post-step, not the default:** the Mermaid/Markdown sources stay the source of truth and
> render fine on GitHub; the inline-SVG pass only hardens the *self-contained HTML* so a fresher can
> open it anywhere — offline, double-clicked, in any browser — and the diagrams just appear.

Diagrams are pre-rendered in one theme (light/Blueprint). That's an accepted trade for "works
everywhere"; they stay legible in dark mode.

## Keeping it from rotting

> **Changed some code and need the step-by-step?** See
> [`maintaining-the-docs.md`](./maintaining-the-docs.md) — the playbook for a new joinee covering
> "I changed a wrapper / created a new wrapper / changed the tooling source → here's exactly what to
> update."

Docs rot when the code moves underneath them. Three defenses:

1. **Anchor on symbol names, not line numbers.** Walkthroughs reference `acquire_sources`, not
   "line 156" — functions survive edits; line numbers don't. Where a line span is shown, it's
   labelled "approx."
2. **Code is quoted, never edited inline.** Real code is pasted verbatim (trimmed with `...`) with
   annotations in a *separate* table. That keeps a `/fact-check` diff cheap and the code copy-pasteable.
3. **The drift checklist.** When you change a source file, [`drift-checklist.md`](./drift-checklist.md)
   tells you exactly which pages and diagrams to re-check. Run `visual-explainer`'s `/fact-check`
   over the affected pages and append the result to [`fact-check-log.md`](./fact-check-log.md).

## Folder map (what's where)

```
docs/
  README.md            landing + the onion
  ONBOARDING.md        the interactive tutor (ShareOnboardingGuide)
  GLOSSARY.md          every jargon term
  00-primer/           concepts, no code
  10-diagrams/         Mermaid source of truth (.mmd)
  20-walkthroughs/     line-by-line / annotated code (diff-native-api/ = 11 pages)
  30-runbook/          how to operate it
  40-troubleshooting/  symptom → cause → fix
  50-retention/        flashcards, exercises, capstone, graduation checklist
  90-meta/             this folder
  _generated/          (gitignored) visual-explainer HTML output
```

**Next:** [drift-checklist.md →](./drift-checklist.md)
