# Fact-check log

A running record of when the docs were verified against the real source. Append a row whenever you
run `visual-explainer`'s `/fact-check` (or manually verify) after a code or doc change. This is how
we prove the kit hasn't drifted.

## How to add an entry

After running `/fact-check` over the affected pages (see [`drift-checklist.md`](./drift-checklist.md)):

```
| YYYY-MM-DD | who | what changed / why checked | pages checked | result |
```

`result` = `clean` (no mismatches), or a short note on what was fixed.

## Log

| Date | Who | Trigger | Pages checked | Result |
|------|-----|---------|---------------|--------|
| 2026-06-16 | initial author | Kit created | All walkthroughs vs `tools/diff_native_api.py`, `.github/workflows/sync.yml`, `.github/actions/claude-sync` + `build/cordova`, `prompts/sync-orchestrator-cordova.md`, wrapper `native-release-sync.yml` | clean — every symbol/regex/step name verified against source; all 22 Mermaid diagrams validate `true`; PR labels (`auto-generated`, `new-api`, `bug-fix-only`, `breaking-change`, `build-failed`, `incomplete-sync`) confirmed in `scripts/open-combined-pr.sh`; cordova `base_ref` default confirmed `develop` |

> Keep newest entries at the bottom (append-only), so the history reads top-to-bottom.
