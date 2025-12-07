"""
Core GEX (Gamma Exposure) calculation module.
Provides reusable functions for calculating GEX profiles using Tastytrade API.
"""

import asyncio
import os
from datetime import date
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Greeks, Quote, Summary
from tastytrade.instruments import get_option_chain
from tastytrade.market_data import a_get_market_data_by_type

# Load environment variables
load_dotenv()


@dataclass
class GEXResult:
    """Container for GEX calculation results."""
    symbol: str
    spot_price: float
    total_gex: float
    zero_gamma_level: Optional[float]
    max_dte: int
    strike_range: tuple[float, float]
    df: pd.DataFrame  # Full option-level data
    strike_gex: pd.DataFrame  # Aggregated by strike
    major_levels: pd.DataFrame  # Filtered major walls
    call_wall: Optional[float]  # Highest positive GEX strike
    put_wall: Optional[float]  # Lowest negative GEX strike
    error: Optional[str] = None


def get_credentials() -> tuple[Optional[str], Optional[str]]:
    """Get Tastytrade credentials from environment."""
    return os.getenv('TT_CLIENT_SECRET'), os.getenv('TT_REFRESH_TOKEN')


def create_session() -> Optional[Session]:
    """Create authenticated Tastytrade session."""
    client_secret, refresh_token = get_credentials()
    if not client_secret or not refresh_token:
        return None
    try:
        return Session(client_secret, refresh_token)
    except Exception:
        return None


async def get_spot_price(streamer, symbol: str) -> Optional[float]:
    """Fetch current spot price for a symbol."""
    await streamer.subscribe(Quote, [symbol])
    quote_event = await streamer.get_event(Quote)

    if quote_event:
        if hasattr(quote_event, 'last_price') and quote_event.last_price:
            return float(quote_event.last_price)
        if (hasattr(quote_event, 'ask_price') and hasattr(quote_event, 'bid_price')
            and quote_event.ask_price and quote_event.bid_price):
            return (float(quote_event.ask_price) + float(quote_event.bid_price)) / 2.0
    return None


def calculate_zero_gamma(strike_gex: pd.DataFrame, spot: float) -> Optional[float]:
    """
    Calculate the zero gamma level (where cumulative GEX crosses zero).
    This is where dealer hedging flips from supportive to resistive.
    """
    if strike_gex.empty:
        return None

    sorted_df = strike_gex.sort_values('Strike')

    # Find where GEX changes sign
    gex_values = sorted_df['Net GEX ($M)'].values
    strikes = sorted_df['Strike'].values

    for i in range(len(gex_values) - 1):
        if gex_values[i] * gex_values[i + 1] < 0:  # Sign change
            # Linear interpolation
            x1, x2 = strikes[i], strikes[i + 1]
            y1, y2 = gex_values[i], gex_values[i + 1]
            zero_cross = x1 - y1 * (x2 - x1) / (y2 - y1)
            return round(zero_cross, 2)

    return None


async def calculate_gex_profile(
    symbol: str = 'SPY',
    max_dte: int = 30,
    strike_range_pct: float = 0.20,
    major_level_threshold: float = 50.0,
    data_wait_seconds: float = 5.0,
    progress_callback=None
) -> GEXResult:
    """
    Calculate GEX profile for a given symbol.

    Args:
        symbol: Ticker symbol (e.g., 'SPY', 'QQQ')
        max_dte: Maximum days to expiration (0 to max_dte)
        strike_range_pct: Strike range as percentage of spot (0.20 = 80%-120%)
        major_level_threshold: Minimum absolute GEX ($M) for major levels
        data_wait_seconds: Time to wait for streaming data
        progress_callback: Optional callback(message) for progress updates

    Returns:
        GEXResult with all calculated data
    """
    def log(msg):
        if progress_callback:
            progress_callback(msg)

    # Check credentials
    client_secret, refresh_token = get_credentials()
    if not client_secret or not refresh_token:
        return GEXResult(
            symbol=symbol, spot_price=0, total_gex=0, zero_gamma_level=None,
            max_dte=max_dte, strike_range=(0, 0), df=pd.DataFrame(),
            strike_gex=pd.DataFrame(), major_levels=pd.DataFrame(),
            call_wall=None, put_wall=None,
            error="Missing API credentials. Please configure TT_CLIENT_SECRET and TT_REFRESH_TOKEN"
        )

    # Authenticate
    log("Authenticating with Tastytrade...")
    try:
        session = Session(client_secret, refresh_token)
    except Exception as e:
        return GEXResult(
            symbol=symbol, spot_price=0, total_gex=0, zero_gamma_level=None,
            max_dte=max_dte, strike_range=(0, 0), df=pd.DataFrame(),
            strike_gex=pd.DataFrame(), major_levels=pd.DataFrame(),
            call_wall=None, put_wall=None,
            error=f"Authentication failed: {e}"
        )

    log(f"Fetching data for {symbol}...")

    async with DXLinkStreamer(session) as streamer:
        # Get spot price
        log("Getting spot price...")
        spot = await get_spot_price(streamer, symbol)
        if spot is None:
            return GEXResult(
                symbol=symbol, spot_price=0, total_gex=0, zero_gamma_level=None,
                max_dte=max_dte, strike_range=(0, 0), df=pd.DataFrame(),
                strike_gex=pd.DataFrame(), major_levels=pd.DataFrame(),
                call_wall=None, put_wall=None,
                error="Could not fetch spot price"
            )

        # Get option chain
        log("Fetching option chain...")
        try:
            chain_result = get_option_chain(session, symbol)
        except Exception as e:
            return GEXResult(
                symbol=symbol, spot_price=spot, total_gex=0, zero_gamma_level=None,
                max_dte=max_dte, strike_range=(0, 0), df=pd.DataFrame(),
                strike_gex=pd.DataFrame(), major_levels=pd.DataFrame(),
                call_wall=None, put_wall=None,
                error=f"Failed to fetch option chain: {e}"
            )

        if not chain_result:
            return GEXResult(
                symbol=symbol, spot_price=spot, total_gex=0, zero_gamma_level=None,
                max_dte=max_dte, strike_range=(0, 0), df=pd.DataFrame(),
                strike_gex=pd.DataFrame(), major_levels=pd.DataFrame(),
                call_wall=None, put_wall=None,
                error="No chain data returned"
            )

        # Normalize chain to list
        all_options_raw = []
        if hasattr(chain_result, 'options'):
            all_options_raw = list(chain_result.options)
        elif isinstance(chain_result, dict):
            for opts in chain_result.values():
                all_options_raw.extend(opts)

        # Filter options
        today = date.today()
        lower_bound = spot * (1 - strike_range_pct)
        upper_bound = spot * (1 + strike_range_pct)

        log(f"Filtering options (strikes {lower_bound:.0f}-{upper_bound:.0f})...")

        all_options_to_monitor = []
        for opt in all_options_raw:
            days_to_exp = (opt.expiration_date - today).days
            if not (0 <= days_to_exp <= max_dte):
                continue
            if not (lower_bound <= float(opt.strike_price) <= upper_bound):
                continue
            all_options_to_monitor.append(opt)

        if not all_options_to_monitor:
            return GEXResult(
                symbol=symbol, spot_price=spot, total_gex=0, zero_gamma_level=None,
                max_dte=max_dte, strike_range=(lower_bound, upper_bound),
                df=pd.DataFrame(), strike_gex=pd.DataFrame(), major_levels=pd.DataFrame(),
                call_wall=None, put_wall=None,
                error="No options found after filtering"
            )

        log(f"Found {len(all_options_to_monitor)} options to analyze...")

        # Fetch initial OI snapshot (fallback)
        log("Fetching open interest data...")
        initial_oi_map = {}
        all_symbols = [opt.symbol for opt in all_options_to_monitor]

        for i in range(0, len(all_symbols), 100):
            chunk = all_symbols[i:i + 100]
            try:
                market_data = await a_get_market_data_by_type(session, options=chunk)
                for md in market_data:
                    if md.open_interest is not None:
                        initial_oi_map[md.symbol] = int(md.open_interest)
            except Exception:
                pass

        # Stream Greeks and Summary
        greeks_events = []
        summary_events = []

        async def listen_greeks():
            async for event in streamer.listen(Greeks):
                greeks_events.append(event)

        async def listen_summary():
            async for event in streamer.listen(Summary):
                summary_events.append(event)

        t_greeks = asyncio.create_task(listen_greeks())
        t_summary = asyncio.create_task(listen_summary())

        log("Subscribing to real-time data...")
        symbols_to_sub = [opt.streamer_symbol for opt in all_options_to_monitor]
        try:
            await streamer.subscribe(Greeks, symbols_to_sub)
            await streamer.subscribe(Summary, symbols_to_sub)
        except Exception:
            pass

        log(f"Collecting data ({data_wait_seconds}s)...")
        await asyncio.sleep(data_wait_seconds)

        t_greeks.cancel()
        t_summary.cancel()
        try:
            await t_greeks
            await t_summary
        except asyncio.CancelledError:
            pass

        greek_map = {g.event_symbol: g for g in greeks_events}
        summary_map = {s.event_symbol: s for s in summary_events}

        # Calculate GEX
        log("Calculating GEX...")
        data = []
        for opt in all_options_to_monitor:
            s_sym = opt.streamer_symbol
            matching_greek = greek_map.get(s_sym)
            matching_summary = summary_map.get(s_sym)

            gamma = float(matching_greek.gamma) if matching_greek and matching_greek.gamma else 0.0

            oi = 0
            if matching_summary and matching_summary.open_interest:
                oi = int(matching_summary.open_interest)
            elif opt.symbol in initial_oi_map:
                oi = initial_oi_map[opt.symbol]

            strike = float(opt.strike_price)
            raw_gex_m = (oi * gamma * 100 * (spot ** 2) * 0.01) / 1_000_000

            is_call = opt.option_type == 'C'
            net_gex = raw_gex_m if is_call else -raw_gex_m

            data.append({
                'Expiration': opt.expiration_date,
                'Strike': strike,
                'Type': 'Call' if is_call else 'Put',
                'OI': oi,
                'Gamma': gamma,
                'Net GEX ($M)': round(net_gex, 4)
            })

        if not data:
            return GEXResult(
                symbol=symbol, spot_price=spot, total_gex=0, zero_gamma_level=None,
                max_dte=max_dte, strike_range=(lower_bound, upper_bound),
                df=pd.DataFrame(), strike_gex=pd.DataFrame(), major_levels=pd.DataFrame(),
                call_wall=None, put_wall=None,
                error="No GEX data calculated"
            )

        df = pd.DataFrame(data)
        total_gex = df['Net GEX ($M)'].sum()

        # Aggregate by strike
        strike_gex = df.groupby('Strike')['Net GEX ($M)'].sum().reset_index()
        strike_gex = strike_gex.sort_values(by='Strike')

        # Major levels
        major_levels = strike_gex[strike_gex['Net GEX ($M)'].abs() > major_level_threshold].copy()
        major_levels['Net GEX ($M)'] = major_levels['Net GEX ($M)'].round(1)

        # Find call wall (highest positive GEX) and put wall (lowest negative GEX)
        positive_gex = strike_gex[strike_gex['Net GEX ($M)'] > 0]
        negative_gex = strike_gex[strike_gex['Net GEX ($M)'] < 0]

        call_wall = None
        put_wall = None

        if not positive_gex.empty:
            call_wall = positive_gex.loc[positive_gex['Net GEX ($M)'].idxmax(), 'Strike']
        if not negative_gex.empty:
            put_wall = negative_gex.loc[negative_gex['Net GEX ($M)'].idxmin(), 'Strike']

        # Calculate zero gamma
        zero_gamma = calculate_zero_gamma(strike_gex, spot)

        log("Done!")

        return GEXResult(
            symbol=symbol,
            spot_price=spot,
            total_gex=round(total_gex, 2),
            zero_gamma_level=zero_gamma,
            max_dte=max_dte,
            strike_range=(lower_bound, upper_bound),
            df=df,
            strike_gex=strike_gex,
            major_levels=major_levels,
            call_wall=call_wall,
            put_wall=put_wall,
            error=None
        )


def run_gex_calculation(
    symbol: str = 'SPY',
    max_dte: int = 30,
    strike_range_pct: float = 0.20,
    progress_callback=None
) -> GEXResult:
    """Synchronous wrapper for calculate_gex_profile."""
    return asyncio.run(calculate_gex_profile(
        symbol=symbol,
        max_dte=max_dte,
        strike_range_pct=strike_range_pct,
        progress_callback=progress_callback
    ))
