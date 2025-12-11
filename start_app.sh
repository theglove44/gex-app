#!/bin/bash

# Trap to kill all subprocesses when script exits
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

echo "🚀 Starting GEX Tool (Full Stack)..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Please create one with your Tastytrade credentials."
    exit 1
fi

# detailed output for backend
echo "📦 Starting Backend (FastAPI) on :8000..."
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend..."
sleep 2

# detailed output for frontend
echo "🖥️  Starting Frontend (Next.js) on :3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ App running at http://localhost:3000"
echo "Press Ctrl+C to stop."

wait
