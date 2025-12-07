# GEX Tool

A Python-based tool for calculating Gamma Exposure (GEX) using the Tastytrade API and dxFeed.

## Overview

This project provides scripts to fetch option chain data, calculate GEX profiles (including Zero Gamma levels), and analyze market gamma exposure. It uses dxLink for real-time data streaming.

## Prerequisites

- Python 3.8+
- A Tastytrade account (for API access).
- A valid Tastytrade refresh token and client secret.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd gex-tool
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    *(Note: Ensure you have `dxlink`, `tastytrade-sdk` or equivalent libraries installed. If a requirements.txt exists, use that.)*
    ```bash
    pip install pandas python-dotenv requests websockets
    # Add other actual dependencies here based on your environment
    ```

## Configuration

1.  Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```

2.  Edit `.env` and add your Tastytrade credentials:
    ```
    TT_CLIENT_SECRET=your_client_secret_here
    TT_REFRESH_TOKEN=your_refresh_token_here
    ```

## Usage

### Main GEX Calculation
Run the main script to calculate GEX for a symbol (defaulting to SPX or as configured in the script):

```bash
python gex.py
```

### Utilities

-   **Check SDK/Connection:**
    Use `check_sdk.py` to verify your environment and API connectivity.
    ```bash
    python check_sdk.py
    ```

-   **Probe Instruments:**
    Use `probe_instruments.py` to look up instrument details or symbols.
    ```bash
    python probe_instruments.py
    ```

## Disclaimer

This software is for educational purposes only. Do not use it as the sole basis for investment decisions.
