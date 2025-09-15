#!/usr/bin/env bash
# Simple smoke test for EdutainmentForge
# Usage: ./scripts/smoke_test.sh [BASE_URL]
# Defaults to http://localhost:5000

set -euo pipefail
BASE_URL=${1:-http://localhost:5000}

echo "[SMOKE] Base URL: $BASE_URL"

fail() { echo "[SMOKE][FAIL] $1" >&2; exit 1; }

check_json_field() {
  local json="$1" field="$2"
  echo "$json" | grep -q '"'$field'"' || fail "Missing field '$field' in response: $json"
}

# 1. Liveness
resp=$(curl -sS "$BASE_URL/healthz" || true)
[ -n "$resp" ] || fail "/healthz no response"
check_json_field "$resp" status
status=$(echo "$resp" | grep -o '"status":"[^"]*"' | head -n1 | cut -d':' -f2 | tr -d '"')
[ "$status" = "ok" ] || echo "[SMOKE][WARN] /healthz status=$status"

echo "[SMOKE] /healthz passed"

# 2. Deep health (expect 200/206/503 acceptable but capture)
code=$(curl -sS -w '%{http_code}' -o /tmp/deep.json "$BASE_URL/healthz/deep" || true)
body=$(cat /tmp/deep.json)
check_json_field "$body" status
if [[ "$code" != "200" && "$code" != "206" ]]; then
  echo "[SMOKE][WARN] Deep health returned HTTP $code"
fi
echo "[SMOKE] /healthz/deep status=$(echo "$body" | grep -o '"status":"[^"]*"' | head -n1 | cut -d'"' -f4)"

# 3. Voices (public)
voices=$(curl -sS "$BASE_URL/api/voices" || true)
check_json_field "$voices" en-US-EmmaNeural

echo "[SMOKE] voices endpoint OK"

# 4. (Optional) if auth disabled for testing, attempt a dummy process call
if [[ "${DISABLE_AUTH_FOR_TESTING:-}" == "true" ]]; then
  echo "[SMOKE] Auth disabled; issuing sample /api/process request"
  process_resp=$(curl -sS -H 'Content-Type: application/json' -d '{"url":"https://learn.microsoft.com/en-us/training/modules/intro-to-azure-fundamentals/"}' "$BASE_URL/api/process" || true)
  check_json_field "$process_resp" task_id || echo "[SMOKE][WARN] process response: $process_resp"
  echo "[SMOKE] process initiation response: $process_resp"
fi

echo "[SMOKE] Completed"
