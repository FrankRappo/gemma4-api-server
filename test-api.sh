#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://127.0.0.1:18081"
KEY="$GEMMA_API_KEY"
ENV_FILE="/etc/gemma4-api-server.env"
if [ -z "$KEY" ] && [ -r "$ENV_FILE" ]; then
  KEY="$(sed -n 's/^GEMMA_API_KEY=//p' "$ENV_FILE")"
fi
test -n "$KEY"

curl -fsS "$BASE_URL/health"
curl -fsS -H "Authorization: Bearer $KEY" "$BASE_URL/v1/models" >/dev/null
curl -fsS -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"model":"gemma-4-31b-orba","messages":[{"role":"user","content":"READY"}],"max_tokens":8}' \
  "$BASE_URL/v1/chat/completions" >/dev/null
echo API_TEST_OK
