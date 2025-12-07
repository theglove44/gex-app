# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GEX Tool is a Python application for calculating Gamma Exposure (GEX) profiles using the Tastytrade API and dxFeed real-time data streaming. It analyzes option chain data to identify gamma walls and zero gamma levels for market analysis.

## Tech Stack

- **Python 3.10+** - Core language (required by tastytrade SDK)
- **tastytrade SDK** - API authentication and dxLink streaming
- **pandas** - Data manipulation and aggregation
- **matplotlib** - Chart generation
- **python-dotenv** - Environment variable management

## Project Structure

- `gex.py` - Main GEX calculation script (entry point)
- `check_sdk.py` - Verify environment and API connectivity
- `probe_*.py` - Utility scripts for testing API endpoints and data streaming
- `requirements.txt` - Python dependencies

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run main GEX calculation (defaults to SPY, 30 DTE)
python gex.py

# Test API connectivity
python check_sdk.py
```

## Environment Setup

Requires a `.env` file with Tastytrade credentials:
```
TT_CLIENT_SECRET=your_client_secret_here
TT_REFRESH_TOKEN=your_refresh_token_here
```

Copy from `.env.example` to create your `.env` file.

## Key Implementation Details

### GEX Calculation Flow (gex.py)
1. Authenticate with Tastytrade API using refresh token
2. Connect to DXLinkStreamer for real-time data
3. Fetch spot price via Quote events
4. Get option chain and filter by DTE (0-30 days) and strike range (80%-120% of spot)
5. Subscribe to Greeks and Summary events for gamma and open interest data
6. Calculate Net GEX: `(OI * gamma * 100 * spot^2 * 0.01) / 1,000,000`
7. Calls contribute positive GEX, puts contribute negative GEX
8. Generate visualization saved to `gex_profile.png`

### Data Sources
- **Greeks events** - Provide gamma values via dxFeed streaming
- **Summary events** - Provide open interest via streaming (with API snapshot fallback)
- **Quote events** - Provide spot price (bid/ask midpoint)

## Important Notes

- Never commit `.env` file or expose credentials
- API rate limits: Market data requests are batched in chunks of 100 symbols
- The streamer uses async context manager pattern
- Option symbols use `streamer_symbol` for subscriptions but standard `symbol` for API lookups
