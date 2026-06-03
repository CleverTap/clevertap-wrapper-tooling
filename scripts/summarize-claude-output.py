#!/usr/bin/env python3
"""
summarize-claude-output.py — print a one-line summary of a claude-output JSON.

The CLI's --output-format json envelope wraps Claude's response. The
structured triage log Claude was instructed to emit lives INSIDE the
envelope's `.result` field as a Markdown ```json``` block.

This script extracts that inner JSON and prints counts (surfaced / skipped /
deferred), plus the envelope's own cost + token totals. Exits 0 even if
parsing fails — this is for human display only, not a gate.

Usage:
    summarize-claude-output.py <path-to-claude-output.json>
"""

import json
import re
import sys
from pathlib import Path


def extract_inner(result_text):
    # Look for the first ```json ... ``` fence in the result.
    m = re.search(r"```json\s*(\{.*?\})\s*```", result_text, re.DOTALL)
    if not m:
        # Fallback: maybe Claude emitted bare JSON
        m = re.search(r"(\{.*\})", result_text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def main():
    if len(sys.argv) != 2:
        print("usage: summarize-claude-output.py <claude-output.json>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"(file not present: {path})")
        return 0

    try:
        envelope = json.loads(path.read_text())
    except Exception as e:
        print(f"(could not parse envelope: {e})")
        return 0

    # Envelope-level metadata (cost, tokens) is always reliable
    cost = envelope.get("total_cost_usd", 0)
    usage = envelope.get("usage", {}) or {}
    in_tok = usage.get("input_tokens", 0)
    out_tok = usage.get("output_tokens", 0)
    total_tok = in_tok + out_tok

    result_text = envelope.get("result", "")
    inner = extract_inner(result_text) if isinstance(result_text, str) else None

    if inner is None:
        print("(could not extract structured triage log from result text)")
        print(f"  cost: ${cost:.4f}  tokens: {total_tok}")
        return 0

    surfaced = inner.get("surfaced", []) or []
    skipped = inner.get("skipped", []) or []
    deferred = inner.get("deferred", []) or []

    print(f"  surfaced: {len(surfaced)}")
    print(f"  skipped:  {len(skipped)}")
    print(f"  deferred: {len(deferred)}")
    print(f"  cost:     ${cost:.4f}")
    print(f"  tokens:   {total_tok}  (in: {in_tok}, out: {out_tok})")

    if surfaced:
        print("\n  Surfaced:")
        for s in surfaced:
            name = s.get("name", "<unknown>")
            files = s.get("files_touched", [])
            print(f"    - {name}  ({len(files)} files)")

    if deferred:
        print("\n  Deferred:")
        for d in deferred:
            name = d.get("name", "<unknown>")
            rat = d.get("rationale", "")[:80]
            print(f"    - {name}: {rat}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
