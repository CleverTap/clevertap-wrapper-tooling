#!/usr/bin/env python3
"""Render the PR body for the update-ionic-typings workflow.

Reads the Claude CLI result envelope (argv[1]) and prints a Markdown PR body to
stdout. The structured summary the prompt emits lives inside the envelope's
`.result` text — usually wrapped in a ```json fenced block (and sometimes
preceded by prose), so we extract it tolerantly rather than json-parsing
`.result` directly. Cost / model / token metadata come from the envelope's
top-level fields (authoritative), the same source compute-cost.sh uses.

Env: CORDOVA_REPO, CORDOVA_REF, TYPINGS_REPO, BRANCH.
"""
import json
import os
import re
import sys


def load_envelope(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def extract_summary(result_text):
    """Pull the structured JSON object out of .result (fence > prose > raw)."""
    if not isinstance(result_text, str):
        return {}
    candidates = []
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", result_text, re.S)
    if fenced:
        candidates.append(fenced.group(1))
    # Fall back to the largest {...} span in the text.
    brace = re.search(r"(\{.*\})", result_text, re.S)
    if brace:
        candidates.append(brace.group(1))
    for c in candidates:
        try:
            return json.loads(c)
        except Exception:
            continue
    return {}


def bullet_list(items):
    return "\n".join(items) if items else "_none_"


def main():
    env = load_envelope(sys.argv[1] if len(sys.argv) > 1 else "")
    summary = extract_summary(env.get("result", ""))

    cordova_repo = os.environ.get("CORDOVA_REPO", "")
    cordova_ref = os.environ.get("CORDOVA_REF", "")
    typings_repo = os.environ.get("TYPINGS_REPO", "")
    branch = os.environ.get("BRANCH", "")

    added = [f"- `{m.get('name')}`" for m in summary.get("added", []) if m.get("name")]
    updated = [
        f"- `{m.get('name')}`: `{m.get('from')}` → `{m.get('to')}`"
        for m in summary.get("updated", []) if m.get("name")
    ]
    removed = [f"- `{m.get('name')}`" for m in summary.get("removed", []) if m.get("name")]
    flagged = [
        f"- `{m.get('name')}` — {m.get('reason', '')}"
        for m in summary.get("flagged_for_review", []) if m.get("name")
    ]

    # Run metadata (authoritative top-level envelope fields).
    cost = env.get("total_cost_usd")
    usage = env.get("usage", {}) or {}
    models = list((env.get("modelUsage", {}) or {}).keys())
    in_tok = usage.get("input_tokens", 0)
    out_tok = usage.get("output_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)

    cost_str = f"${cost:.2f}" if isinstance(cost, (int, float)) else "n/a"
    models_str = ", ".join(f"`{m}`" for m in models) if models else "n/a"

    body = f"""Updates the CleverTap typings in `awesome-cordova-plugins` to match the latest Cordova plugin API (synced from `{cordova_repo}@{cordova_ref}`).

**Added**
{bullet_list(added)}

**Updated (signature)**
{bullet_list(updated)}

**Removed**
{bullet_list(removed)}

**Flagged for review**
{bullet_list(flagged)}

Only `src/@awesome-cordova-plugins/plugins/clevertap/index.ts` is modified.

---
**Run metadata**
- Model(s): {models_str}
- Cost: {cost_str}
- Tokens: input {in_tok:,} / output {out_tok:,} (cache read {cache_read:,})

---
⚠️ **Next step (human):** after this merges, open the upstream PR from `{typings_repo}:{branch}` (or the base after merge) to `danielsogl/awesome-cordova-plugins` via "Contribute → Open pull request".

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
    sys.stdout.write(body)


if __name__ == "__main__":
    main()
