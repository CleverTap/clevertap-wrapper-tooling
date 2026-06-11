#!/usr/bin/env python3
"""
trace-claude-actions.py — render a readable step trace from a Claude CLI
`--output-format stream-json` transcript (.jsonl).

Prints, into the workflow log: the ordered tool calls (Read/Edit/Write/Bash/...),
a files-read and files-edited summary, any tool errors / permission denials, and
a quick signal line (were skills read? was the example app touched?). This is how
omissions like "never read .claude/skills/..." or "no Example/app edit" become
visible. Pure parsing — no model calls, no token cost. Never fails the build.

Usage: trace-claude-actions.py <stream.jsonl>
"""
import json
import sys


def uniq(xs):
    seen = []
    for x in xs:
        if x not in seen:
            seen.append(x)
    return seen


def short(s, n=140):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n] + "..."


def main():
    if len(sys.argv) < 2:
        print("usage: trace-claude-actions.py <stream.jsonl>")
        return 0
    try:
        lines = open(sys.argv[1], "r", encoding="utf-8", errors="replace").read().splitlines()
    except Exception as e:
        print("(could not read stream: %s)" % e)
        return 0

    calls = []          # ordered (name, detail)
    reads, edits, bashes, errors, denials = [], [], [], [], []

    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            ev = json.loads(ln)
        except Exception:
            continue
        t = ev.get("type")
        if t == "assistant":
            for b in (ev.get("message", {}).get("content") or []):
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    name = b.get("name", "?")
                    inp = b.get("input", {}) or {}
                    detail = inp.get("file_path") or inp.get("command") \
                        or inp.get("pattern") or inp.get("path") or ""
                    calls.append((name, short(detail)))
                    fp = inp.get("file_path")
                    if name == "Read" and fp:
                        reads.append(fp)
                    elif name in ("Edit", "MultiEdit", "Write") and fp:
                        edits.append(fp)
                    elif name == "Bash" and inp.get("command"):
                        bashes.append(short(inp["command"]))
        elif t == "user":
            for b in (ev.get("message", {}).get("content") or []):
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"):
                    c = b.get("content")
                    if isinstance(c, list):
                        c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
                    errors.append(short(c, 160))
        elif t == "result":
            for d in (ev.get("permission_denials") or []):
                denials.append(short(d if isinstance(d, str) else json.dumps(d), 160))

    print("Tool calls (%d):" % len(calls))
    for name, detail in calls:
        print(("  - %s: %s" % (name, detail)) if detail else ("  - %s" % name))

    r = uniq(reads)
    w = uniq(edits)
    print("\nFiles read (%d):" % len(r))
    for f in r:
        print("  R %s" % f)
    print("Files edited/written (%d):" % len(w))
    for f in w:
        print("  W %s" % f)

    if errors:
        print("\nTool errors (%d):" % len(errors))
        for e in errors:
            print("  ! %s" % e)
    if denials:
        print("\nPermission denials (%d):" % len(denials))
        for d in denials:
            print("  DENIED: %s" % d)

    skills_read = [f for f in r if ".claude/skills" in f]
    example_edited = [f for f in w if "example/" in f.lower() or "/Example/" in f]
    print("\nSignal: skills read = %d, example-app files edited = %d"
          % (len(skills_read), len(example_edited)))
    if not skills_read:
        print("  WARNING: no .claude/skills file was read this run.")
    if not example_edited:
        print("  WARNING: no example-app file was edited this run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
