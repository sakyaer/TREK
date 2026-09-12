#!/usr/bin/env bash
# Thin authenticated curl wrapper for TREK's HTTP API.
#
#   export TREK_EMAIL=you@example.com TREK_PASSWORD=...   # logs in on first use
#   # or: export TREK_JWT=<jwt>
#   trek-api.sh GET  /api/trips
#   trek-api.sh POST /api/trips '{"title":"Iceland","start_date":"2026-10-01","end_date":"2026-10-07"}'
#
# The status line goes to stderr and the response body to stdout, so command
# substitution captures just the body:
#   body=$(trek-api.sh GET /api/trips)
#
# These are internal /api routes: they accept a session JWT only. The static
# `trek_...` tokens are rejected here (they are for /api/v1, which is read-only).
set -euo pipefail

TREK_URL="${TREK_URL:-http://localhost:9999}"
CACHE="${TREK_TOKEN_CACHE:-${TMPDIR:-/tmp}/trek-jwt.$(id -u)}"
MARKER='__TREK_STATUS__'

die() { printf 'trek-api: %s\n' "$*" >&2; exit 1; }

# Minimal JSON string escaping: backslash and double quote. Passwords with
# control characters are not supported; use TREK_JWT for those.
json_str() {
  local s=$1
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  printf '"%s"' "$s"
}

jwt() {
  if [ -n "${TREK_JWT:-}" ]; then printf '%s' "$TREK_JWT"; return; fi
  if [ -s "$CACHE" ]; then cat "$CACHE"; return; fi
  if [ -z "${TREK_EMAIL:-}" ] || [ -z "${TREK_PASSWORD:-}" ]; then
    die "set TREK_JWT, or both TREK_EMAIL and TREK_PASSWORD"
  fi

  local payload body token
  payload=$(printf '{"email":%s,"password":%s}' \
    "$(json_str "$TREK_EMAIL")" "$(json_str "$TREK_PASSWORD")")

  body=$(curl -sS -X POST "$TREK_URL/api/auth/login" \
    -H 'Content-Type: application/json' \
    --data "$payload") || die "login request failed"

  token=$(printf '%s' "$body" |
    sed -n 's/.*"token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
  if [ -z "$token" ]; then
    die "no token in login response (bad credentials, or MFA is required): $body"
  fi

  (umask 077; printf '%s' "$token" > "$CACHE")
  printf '%s' "$token"
}

METHOD="${1:?usage: trek-api.sh METHOD PATH [JSON_BODY]}"
REQ_PATH="${2:?usage: trek-api.sh METHOD PATH [JSON_BODY]}"
BODY="${3:-}"

args=(-sS -X "$METHOD" "$TREK_URL$REQ_PATH"
  -H "Authorization: Bearer $(jwt)"
  -H 'Accept: application/json')
if [ -n "$BODY" ]; then
  args+=(-H 'Content-Type: application/json' --data "$BODY")
fi

out=$(curl "${args[@]}" -w "${MARKER}%{http_code}") || die "request failed"

code="${out##*$MARKER}"
body="${out%"$MARKER"*}"

# A 401 means the cached JWT is stale (password rotated, password_version bumped).
# Drop it so the next run logs in again instead of failing forever.
if [ "$code" = "401" ]; then rm -f "$CACHE"; fi

printf 'trek-api: %s %s -> %s\n' "$METHOD" "$REQ_PATH" "$code" >&2
printf '%s\n' "${body%$'\n'}"
