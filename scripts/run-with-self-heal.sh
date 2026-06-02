#!/usr/bin/env bash
#
# run-with-self-heal.sh — Run a command. On failure, ask Claude to fix the
# code-level error and retry. Bail after MAX attempts.
#
# Usage:
#   run-with-self-heal.sh "<command>" <max_attempts>
#
# Environment:
#   ANTHROPIC_API_KEY  - required (for Claude CLI)
#   SELF_HEAL_PROMPT   - path to self-heal.md (templated)
#   MODEL              - Claude model (default: sonnet-4-6)
#   STEP_NAME          - human-readable step name (used in prompt)

set -uo pipefail

CMD="${1:?usage: $0 <command> <max_attempts>}"
MAX="${2:?usage: $0 <command> <max_attempts>}"
MODEL="${MODEL:-sonnet-4-6}"
STEP_NAME="${STEP_NAME:-unknown}"

attempt=1
while [ "$attempt" -le "$MAX" ]; do
    echo "::group::Attempt $attempt of $MAX: $CMD"

    # Run the command, capture stderr separately so we can feed it to Claude
    if eval "$CMD" 2> err.log; then
        echo "::endgroup::"
        echo "✅ Step '$STEP_NAME' passed on attempt $attempt"
        rm -f err.log
        exit 0
    fi
    rc=$?
    echo "::endgroup::"
    echo "❌ Attempt $attempt failed (exit $rc). Error tail:"
    tail -n 30 err.log || true

    if [ "$attempt" -eq "$MAX" ]; then
        echo "::error::Self-heal exhausted after $MAX attempts on step '$STEP_NAME'."
        exit "$rc"
    fi

    # Build the self-heal prompt with the captured error
    if [ ! -f "${SELF_HEAL_PROMPT:-}" ]; then
        echo "::error::SELF_HEAL_PROMPT not set or file missing: ${SELF_HEAL_PROMPT:-<unset>}"
        exit 1
    fi

    export PWD STEP_NAME CMD
    prompt="$(envsubst < "$SELF_HEAL_PROMPT")"

    echo "::group::Asking Claude to self-heal (attempt $((attempt + 1))/$MAX)"
    if ! claude -p "$prompt" --model "$MODEL"; then
        rc_heal=$?
        if [ "$rc_heal" -eq 2 ]; then
            echo "::warning::Claude declared the error not self-healable (exit 2). Aborting retry loop."
            echo "::endgroup::"
            exit "$rc"
        fi
        echo "::warning::Claude self-heal invocation itself errored ($rc_heal). Continuing to next attempt."
    fi
    echo "::endgroup::"

    attempt=$((attempt + 1))
done

# Should be unreachable
exit 1
