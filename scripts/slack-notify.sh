#!/usr/bin/env bash
#
# slack-notify.sh — POST a failure message to a Slack webhook.
# Called from GitHub Actions when the sync workflow fails for non-recoverable
# reasons (self-heal exhausted, API quota, etc.).
#
# Environment:
#   SLACK_WEBHOOK_URL  - required
#   WRAPPER            - wrapper name (e.g. react-native)
#   BRANCH             - branch the workflow was trying to push
#   RUN_URL            - URL of the failing GitHub Actions run

set -uo pipefail

if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
    echo "::warning::SLACK_WEBHOOK_URL is empty — skipping Slack notification."
    exit 0
fi

payload=$(cat <<EOF
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "❌ wrapper-sync failure: ${WRAPPER:-<unknown>}",
        "emoji": true
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Wrapper:*\n${WRAPPER:-<unknown>}"},
        {"type": "mrkdwn", "text": "*Branch:*\n${BRANCH:-<unknown>}"}
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Self-heal exhausted or the workflow hit a non-recoverable error. Please inspect the run logs and take over manually.\n\n<${RUN_URL:-#}|View workflow run>"
      }
    }
  ]
}
EOF
)

curl -sS -X POST \
    -H 'Content-Type: application/json' \
    --data "$payload" \
    "$SLACK_WEBHOOK_URL" > /dev/null

echo "✅ Slack notified"
