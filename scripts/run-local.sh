#!/usr/bin/env bash
# Local (non-Docker) run of TREK.
#
#   ./scripts/run-local.sh [PORT]     # default 9999
#
# Builds whatever is missing, syncs the client bundle into server/public, then
# starts the production server in the foreground (Ctrl-C stops it). Configuration
# comes from server/.env, which the server entrypoint loads from its own cwd.
set -euo pipefail

PORT="${1:-9999}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -f server/.env ]; then
  echo "server/.env is missing. Copy server/.env.example and set NODE_ENV=production," >&2
  echo "otherwise the built SPA is not served (server/src/nest/platform/platform.routes.ts)." >&2
  exit 1
fi

if [ ! -d shared/dist ] || [ ! -d server/dist ] || [ ! -d client/dist ]; then
  echo '[run-local] building shared -> server -> client'
  npm run build
fi

# The server serves the SPA out of server/public; the Dockerfile performs the same
# copy from the client build. .gitkeep keeps the gitignored directory present.
echo '[run-local] syncing client/dist -> server/public'
rm -rf server/public
mkdir -p server/public
cp -R client/dist/. server/public/
touch server/public/.gitkeep

mkdir -p server/data server/uploads

cd server
echo "[run-local] starting TREK on http://localhost:${PORT}"
exec env PORT="$PORT" node --require tsconfig-paths/register dist/index.js
