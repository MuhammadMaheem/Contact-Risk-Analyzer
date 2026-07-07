#!/usr/bin/env bash
# Run backend (FastAPI/uvicorn) and frontend (Next.js) in parallel.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

cleanup() {
  echo "Stopping..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd "$BACKEND_DIR"
  source .venv/bin/activate
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

(
  cd "$FRONTEND_DIR"
  npm run dev
) &
FRONTEND_PID=$!

echo "Backend  PID $BACKEND_PID  -> http://localhost:8000"
echo "Frontend PID $FRONTEND_PID -> http://localhost:3000"

if [[ -f "$BACKEND_DIR/.env" ]]; then
  ADMIN_EMAIL=$(grep -E '^ADMIN_EMAIL=' "$BACKEND_DIR/.env" | cut -d= -f2-)
  ADMIN_PASSWORD=$(grep -E '^ADMIN_PASSWORD=' "$BACKEND_DIR/.env" | cut -d= -f2-)
  echo "Admin login -> email: $ADMIN_EMAIL  password: $ADMIN_PASSWORD"
fi
echo "No default regular user exists — sign up a new one at POST /register (or via the frontend signup page)."

wait "$BACKEND_PID" "$FRONTEND_PID"
