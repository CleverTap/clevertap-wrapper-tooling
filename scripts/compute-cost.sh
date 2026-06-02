#!/usr/bin/env bash
#
# compute-cost.sh — Sum token usage across the two claude-output JSONs and
# post a PR comment if the soft cap is exceeded.
#
# Environment:
#   ANDROID_OUTPUT     - path to claude-output-android.json (may not exist)
#   IOS_OUTPUT         - path to claude-output-ios.json (may not exist)
#   BRANCH             - PR branch
#   REPO               - <owner>/<repo> of the wrapper repo
#   GH_TOKEN           - GitHub token (from App)
#   SOFT_CAP_USD       - threshold (default 10)

set -uo pipefail

SOFT_CAP="${SOFT_CAP_USD:-10}"

total_tokens=0
total_cost=0.0

for f in "${ANDROID_OUTPUT:-}" "${IOS_OUTPUT:-}"; do
    [ -z "$f" ] && continue
    [ -f "$f" ] || continue
    tokens=$(jq -r '.tokens_used // 0' "$f")
    cost=$(jq -r '.cost_usd_estimate // 0' "$f")
    total_tokens=$(python3 -c "print(int(${total_tokens}) + int(${tokens}))")
    total_cost=$(python3 -c "print(float(${total_cost}) + float(${cost}))")
done

printf "Total tokens used: %s\n" "$total_tokens"
printf "Approx cost: \$%.2f\n" "$total_cost"

# Find the PR number for our branch and comment if over cap
exceeded=$(python3 -c "print(1 if float($total_cost) > float($SOFT_CAP) else 0)")

if [ "$exceeded" = "1" ]; then
    printf "::warning::Run cost $%.2f exceeded soft cap $%.2f\n" "$total_cost" "$SOFT_CAP"

    if [ -n "${REPO:-}" ] && [ -n "${BRANCH:-}" ] && [ -n "${GH_TOKEN:-}" ]; then
        pr_number=$(gh pr list --repo "$REPO" --head "$BRANCH" --state open --json number --jq '.[0].number' 2>/dev/null || echo "")
        if [ -n "$pr_number" ]; then
            body=$(printf "⚠️ **Run cost: \$%.2f — exceeded soft cap of \$%s**\n\nTotal tokens: %s.\nNo action required — soft cap is informational. Review this run if costs are consistently high." \
                "$total_cost" "$SOFT_CAP" "$total_tokens")
            gh pr comment "$pr_number" --repo "$REPO" --body "$body" || true
        fi
    fi
fi
