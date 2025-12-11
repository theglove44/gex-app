# GEX Tool - Full Stack (v2.0)

This is the new commercial-grade architecture for the GEX Tool, featuring a **FastAPI** backend and a **Next.js** frontend.

## Architecture

- **Backend** (`/backend`): Python/FastAPI. Handles Tastytrade connection, data streaming, and GEX calculations.
- **Frontend** (`/frontend`): TypeScript/Next.js/Shadcn UI. professional, responsive user interface.

## Quick Start

The easiest way to run the app is using the helper script:

```bash
./start_app.sh
```

This will:
1. Start the FastAPI backend on port `8000`.
2. Start the Next.js frontend dev server on port `3000`.
3. Open http://localhost:3000 in your browser.

## Manual Startup

If you prefer to run services individually:

### 1. Backend
```bash
source .venv/bin/activate
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend
```bash
cd frontend
npm run dev
```

## Features

- **Institutional Dashboard**: High-fidelity dark mode UI.
- **Universe Scanner**: Analyze multiple symbols at once support.
- **Live Market Status**: Real-time indicator.
- **Resilient**: Separate backend/frontend allows for better error handling and performance.

## Rollback

To use the legacy Streamlit version:
```bash
streamlit run streamlit_app.py
```
