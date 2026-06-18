# 10-diagrams — the diagram source of truth

Every `.mmd` file in this folder is a **hand-edited Mermaid diagram** and the durable,
in-repo source of truth for that picture. Edit the `.mmd` (or the ```mermaid fenced
blocks embedded in the walkthrough/primer pages) — never edit generated artifacts.

## How these render

- **GitHub renders Mermaid automatically.** A ```mermaid fenced block in any `.md`, and a
  standalone `.mmd` file opened on github.com, both render to an SVG in the browser with no
  build step. So these diagrams stay live just by being committed.
- **Polished HTML** (for the onboarding kit's static site) is regenerated from these `.mmd`
  files via the **visual-explainer** plugin's `/generate-web-diagram` command, which writes
  into the **gitignored** `docs/_generated/` tree. That output is disposable: regenerate it,
  do not hand-edit it, and do not commit it. The `.mmd` here is always authoritative.

To regenerate the HTML layer:

```
/generate-web-diagram docs/10-diagrams/<name>.mmd   # → docs/_generated/<name>.html
```

## The diagrams

| File | What it shows | Related page(s) |
|---|---|---|
| `system-context.mmd` | Context view: native SDK release → maintainer trigger → wrapper dispatch → hub reusable workflow → Claude + diff tool → PR back to the wrapper. Shows the GitHub App minting a token and the Anthropic API. | `00-primer/01-what-is-wrapper-sync.md`, `00-primer/04-repos-and-where-things-live.md` |
| `end-to-end-sequence.mmd` | Sequence diagram: one click → one pull request, turn by turn across maintainer / trigger / conductor / diff tool / Claude / GitHub. | `00-primer/03-a-day-in-the-life.md` |
| `conductor-gating.mmd` | Flowchart of `sync.yml`'s decision flow: setup → pre-sync build GATE → sync android → sync ios → post-sync build → commit/push → open PR → cost/slack, with the key `if:` gates as decision diamonds. | `20-walkthroughs/` (sync.yml conductor walkthrough) |
| `claude-sync-dataflow.mmd` | Flowchart of the `claude-sync` action: prompt template + env vars → `envsubst` → rendered prompt → `claude -p --output-format stream-json` → `stream.jsonl` → `jq select(result)` → `output.json`; plus the diff tool invoked mid-run. | `20-walkthroughs/` (claude-sync action walkthrough) |
| `diff-tool-pipeline.mmd` | The 4 stages of `diff_native_api.py`: acquire → extract → diff → render. Standalone mirror of the overview. | `20-walkthroughs/diff-native-api/00-overview.md` |
| `diff-tool-callgraph.mmd` | Call graph of `diff_native_api.py` from `main()` through the acquire / extract / diff / build-manifest / changelog / render functions (real function names). | `20-walkthroughs/diff-native-api/10-main-orchestration.md` |
| `diff-json-shape.mmd` | Data-shape diagram of `diff.json` the LLM consumes: `meta`, `added[]`, `removed[]`, `changed[]`, `build{android/ios}`, `changelog{target_entry, intermediate_entries}`, `changelog_only_methods`. | `20-walkthroughs/diff-native-api/05-diffing.md`, `09-output-rendering.md` |
| `bridge-layers-cordova.mmd` | Flowchart: JS `cordova.exec("<action>", args)` fanning out to the Android 3-touch (enum + switch case + private method) and iOS 2-touch (`.h` selector decl + `.m` impl). The action string is the shared contract. | `.claude/skills/api-wrapper-patterns/SKILL.md` (in the wrapper repo) |

> Naming note: each `.mmd` opens with a leading `%%` comment naming the diagram and repeating
> the "hand-edited source of truth; render via visual-explainer; never hand-edit generated HTML"
> rule, so the rule travels with the file even when viewed standalone.
