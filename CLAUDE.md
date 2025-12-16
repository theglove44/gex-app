# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GEX Tool is a full-stack application for calculating and visualizing Gamma Exposure (GEX) profiles using the Tastytrade API and dxFeed real-time data streaming. It helps traders identify gamma walls and zero gamma levels for market analysis.

### What is GEX?

Gamma Exposure (GEX) measures the aggregate gamma from options market makers at each strike price. It indicates:
- **Positive GEX (calls)**: Market makers hedge by selling into rallies, dampening volatility
- **Negative GEX (puts)**: Market makers hedge by selling into dips, amplifying volatility
- **Zero Gamma Level**: The price where net GEX flips sign - a key support/resistance level
- **Gamma Walls**: Strikes with extreme GEX that act as magnetic price targets

## Tech Stack

### Backend (Python)
- **Python 3.10+** - Required by tastytrade SDK (uses union type syntax)
- **FastAPI** - REST API framework
- **tastytrade SDK** - API authentication and dxLink streaming
- **pandas** - Data manipulation and GEX aggregation
- **uvicorn** - ASGI server

### Frontend (TypeScript)
- **Next.js 16** - React framework with App Router
- **React 19** - UI library
- **Tailwind CSS 4** - Styling
- **Shadcn/UI** - Component library (Radix primitives)
- **Recharts** - Charting library
- **TanStack Table** - Data tables

### Legacy (Streamlit)
- **Streamlit 1.40+** - Alternative dashboard (still functional)
- **Plotly** - Interactive charts

## Project Structure

```
gex-tool/
├── backend/                 # FastAPI backend
│   ├── main.py             # App entry, CORS, router mounting
│   ├── dependencies.py     # Tastytrade session dependency injection
│   └── routers/
│       └── gex.py          # /api/v1/gex/* endpoints
├── frontend/               # Next.js frontend
│   └── src/
│       ├── app/            # App Router pages
│       │   ├── page.tsx    # Home (dashboard)
│       │   └── scanner/    # Universe scanner page
│       ├── components/     # React components
│       │   ├── dashboard/  # GEX dashboard components
│       │   ├── scanner/    # Multi-symbol scanner
│       │   ├── layout/     # Header, navigation
│       │   └── ui/         # Shadcn components
│       ├── hooks/          # Custom React hooks
│       └── lib/            # Utilities
├── gex_app/                # Shared Python modules
│   ├── core/
│   │   └── gex_core.py     # Core GEX calculation engine
│   ├── config.py           # App configuration
│   ├── layouts.py          # Streamlit layout helpers
│   └── ui/                 # Streamlit UI components
├── pages/                  # Streamlit multi-page app (legacy)
│   ├── 01_GEX_Dashboard.py
│   ├── 02_Universe_Scanner.py
│   └── ...
├── gex.py                  # Standalone CLI GEX calculator
├── streamlit_app.py        # Streamlit entry point
├── start_app.sh            # Full-stack launcher script
└── probe_*.py              # Debug/test utilities
```

## Quick Start

### Option 1: Full-Stack App (Recommended)

```bash
# One command to start both services
./start_app.sh
```

This starts:
- FastAPI backend on http://localhost:8000
- Next.js frontend on http://localhost:3000

### Option 2: Manual Startup

**Backend:**
```bash
source .venv/bin/activate
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Option 3: Legacy Streamlit Dashboard

```bash
streamlit run streamlit_app.py
```

### Option 4: CLI-only GEX Calculation

```bash
python gex.py  # Defaults to SPY, 30 DTE
```

## Environment Setup

1. Copy `.env.example` to `.env`
2. Add your Tastytrade credentials:
```
TT_CLIENT_SECRET=your_client_secret_here
TT_REFRESH_TOKEN=your_refresh_token_here
```

## API Endpoints

### Backend API (http://localhost:8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/gex/calculate` | POST | Calculate GEX for a single symbol |
| `/api/v1/gex/scan` | POST | Calculate GEX for multiple symbols |

**Request body for `/calculate`:**
```json
{
  "symbol": "SPX",
  "max_dte": 30,
  "strike_range_pct": 0.20,
  "major_threshold": 50.0,
  "data_wait": 5.0
}
```

**Response includes:**
- `spot_price`: Current underlying price
- `total_gex`: Net gamma exposure ($M)
- `zero_gamma_level`: Price where GEX = 0
- `call_wall` / `put_wall`: Highest impact gamma strikes
- `major_levels`: Significant gamma levels
- `strike_gex`: GEX by strike (includes volume-weighted GEX)
- `strategy`: Trading signal based on GEX regime

## Key Implementation Details

### GEX Calculation Flow (gex_app/core/gex_core.py)

1. Authenticate with Tastytrade API using refresh token
2. Connect to DXLinkStreamer for real-time data
3. Fetch spot price via Quote/Trade events (with 5s timeout)
4. Get option chain, filter by:
   - DTE: 0 to `max_dte` days (default 30)
   - Strike range: `(1 - strike_range_pct)` to `(1 + strike_range_pct)` of spot
5. Subscribe to Greeks and Summary events for gamma and open interest
6. Calculate Net GEX per contract:
   ```
   GEX = (OI * gamma * 100 * spot^2 * 0.01) / 1,000,000  (in $M)
   ```
7. Calls contribute positive GEX, puts contribute negative
8. Aggregate by strike, identify walls and zero-gamma level

### Data Sources

- **Greeks events**: Gamma values via dxFeed streaming
- **Summary events**: Open interest (streaming with API fallback)
- **Quote/Trade events**: Spot price (bid/ask midpoint or last trade)

### GEX Reversion Threshold

The system uses a $1B Net GEX threshold (`GEX_REVERSION_THRESHOLD`) to determine market regime:
- Above threshold: Expect mean reversion, suppressed volatility
- Below threshold: Expect trend continuation, elevated volatility

## Common Development Tasks

### Running Tests
```bash
pytest tests/
```

### Type Checking
```bash
# Frontend
cd frontend && npm run lint
```

### Building Frontend for Production
```bash
cd frontend && npm run build
```

## Important Notes

- **Never commit `.env`** or expose credentials
- **API rate limits**: Market data requests are batched in 100-symbol chunks
- **Session management**: The streamer uses async context manager pattern
- **Symbol mapping**: Use `streamer_symbol` for subscriptions, `symbol` for API lookups
- **Python version**: 3.10+ required (tastytrade SDK uses `X | None` union syntax)

## Debugging

- Check `backend.log` for FastAPI server logs
- Check `debug_*.log` files for streaming/calculation issues
- Use `probe_*.py` scripts to test individual API/streaming components
- `check_sdk.py` validates environment and API connectivity

## Browser Compatibility

Frontend uses modern CSS (backdrop-filter for glassmorphism):
- Chrome/Edge 76+, Firefox 103+, Safari 9+ (full support)
- Older browsers fall back to solid backgrounds
