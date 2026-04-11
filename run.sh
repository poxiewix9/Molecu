#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo ""
  echo "Shutting down servers..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
  echo "Done."
}
trap cleanup EXIT INT TERM

echo "========================================="
echo "  PharmaSynapse — Starting services"
echo "========================================="

# Backend
echo "[1/2] Starting FastAPI backend on http://localhost:8000"
cd "$ROOT_DIR"
python3.11 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Frontend
echo "[2/2] Starting Next.js frontend on http://localhost:3000"
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend  → http://localhost:8000/health"
echo "Frontend → http://localhost:3000"
echo "Press Ctrl+C to stop both servers."
echo ""

wait
