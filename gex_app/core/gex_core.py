"""
Core GEX (Gamma Exposure) calculation module.
Provides reusable functions for calculating GEX profiles using Tastytrade API.
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

import pandas as pd
from dotenv import load_dotenv

GEX_REVERSION_THRESHOLD = 1_000_000_000  # $1B Net GEX threshold

# The tastytrade SDK uses Python 3.10+ union type syntax (e.g., `date | None`).
# Provide a clear error before importing it on older interpreters to avoid
# cryptic TypeError messages during import.
if sys.version_info < (3, 10):
    raise RuntimeError(
        "Python 3.10 or later is required because the tastytrade SDK relies "
        "on 3.10+ typing features. Please upgrade your interpreter."
    )

from tastytrade import DXLinkStreamer, Session
from tastytrade.dxfeed import Greeks, Quote, Summary, Trade
from tastytrade.instruments import Option, get_option_chain
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
    strategy: Optional[dict[str, Any]] = None
    error: Optional[str] = None


def get_credentials() -> tuple[Optional[str], Optional[str]]:
    """Get Tastytrade credentials from environment."""
    return os.getenv("TT_CLIENT_SECRET"), os.getenv("TT_REFRESH_TOKEN")


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
    await streamer.subscribe(Trade, [symbol])

    try:
        # Race Quote and Trade events
        t_quote = asyncio.create_task(streamer.get_event(Quote))
        t_trade = asyncio.create_task(streamer.get_event(Trade))

        done, pending = await asyncio.wait(
            [t_quote, t_trade], return_when=asyncio.FIRST_COMPLETED, timeout=5.0
        )

        for p in pending:
            p.cancel()

        if not done:
            return None

        # Process the winner
        event = done.pop().result()

        # Priority 1: Trade Price (Last)
        if hasattr(event, "price") and event.price:
            return float(event.price)

        # Priority 2: Quote Last Price
        if hasattr(event, "last_price") and event.last_price:
            return float(event.last_price)

        # Priority 3: Quote Bid/Ask Mid
        if (
            hasattr(event, "ask_price")
            and hasattr(event, "bid_price")
            and event.ask_price
            and event.bid_price
        ):
            return (float(event.ask_price) + float(event.bid_price)) / 2.0

    except Exception:
        return None

    return None


def _fetch_option_chain_with_fallback(
    session: Session, symbol: str, log=None
) -> tuple[Optional[dict], Optional[str]]:
    """Fetch option chain, skipping entries missing expiration metadata.

    Returns (chain, error_message). The chain matches tastytrade.get_option_chain's
    structure: mapping expiration_date -> list[Option].
    """

    try:
        return get_option_chain(session, symbol), None
    except Exception as e:
        error_msg = str(e)
        # Specific issue: API occasionally omits expiration fields causing validation failure
        if "expires-at" not in error_msg and "expiration" not in error_msg:
            return None, f"Failed to fetch option chain: {e}"

        if log:
            log(
                "Option chain had incomplete rows; retrying after filtering invalid entries..."
            )

        try:
            raw = session._get(f"/option-chains/{symbol.replace('/', '%2F')}")
        except Exception as fallback_err:
            return (
                None,
                f"Failed to fetch option chain: {e} (fallback also failed: {fallback_err})",
            )

        chain: dict[date, list[Option]] = {}
        skipped_missing_exp = 0
        skipped_validation = 0

        for item in raw.get("items", []):
            exp_val = item.get("expiration-date") or item.get("expiration_date")
            expires_at_val = item.get("expires-at") or item.get("expires_at")
            if not exp_val or not expires_at_val:
                skipped_missing_exp += 1
                continue

            # Normalize keys for Option model if API used hyphenated names
            if "expiration_date" not in item and "expiration-date" in item:
                item = {**item, "expiration_date": item["expiration-date"]}
            if "expires_at" not in item and "expires-at" in item:
                item = {**item, "expires_at": item["expires-at"]}

            try:
                opt = Option(**item)
            except Exception:
                skipped_validation += 1
                continue

            chain.setdefault(opt.expiration_date, []).append(opt)

        if not chain:
            msg = "No valid options after filtering incomplete data"
            if log:
                log(msg)
            return None, msg

        if log and (skipped_missing_exp or skipped_validation):
            log(
                f"Filtered out {skipped_missing_exp} options missing expiration and {skipped_validation} invalid options"
            )

        return chain, None


def get_available_expirations(
    symbol: str, session: Optional[Session] = None
) -> tuple[list[date], Optional[str]]:
    """
    Fetch all available expiration dates for a symbol.
    """
    if not session:
        session = create_session()

    if not session:
        return [], "Failed to create session"

    chain, error = _fetch_option_chain_with_fallback(session, symbol)

    # We don't close the session here if it was passed in, but if we created it,
    # the SDK Session doesn't have a close/destroy method in some versions.
    # We'll just leave it to GC or user management.

    if error or not chain:
        return [], error or "No chain found"

    expirations = sorted(chain.keys())
    return expirations, None


def calculate_zero_gamma(strike_gex: pd.DataFrame, spot: float) -> Optional[float]:
    """
    Calculate the zero gamma level (where cumulative GEX crosses zero).
    This is where dealer hedging flips from supportive to resistive.
    """
    if strike_gex.empty:
        return None

    sorted_df = strike_gex.sort_values("Strike")

    # Find where GEX changes sign
    gex_values = sorted_df["Net GEX ($M)"].values
    strikes = sorted_df["Strike"].values

    for i in range(len(gex_values) - 1):
        if gex_values[i] * gex_values[i + 1] < 0:  # Sign change
            # Linear interpolation
            x1, x2 = strikes[i], strikes[i + 1]
            y1, y2 = gex_values[i], gex_values[i + 1]
            zero_cross = x1 - y1 * (x2 - x1) / (y2 - y1)
            return round(zero_cross, 2)

    return None


def analyze_strategy(
    total_gex: float,
    spot_price: float,
    call_wall: float,
    put_wall: float,
    zero_gamma: float,
) -> Optional[dict[str, Any]]:
    """
    Analyze GEX data to generate trading signals/strategies.
    Returns a dict with signal details or None if no clear signal.
    """
    if spot_price is None or call_wall is None or put_wall is None:
        return None

    current_hour = datetime.now().hour

    # 1. Mean Reversion Play (Positive GEX Regime)
    # Condition: High positive GEX, price between walls
    if total_gex > GEX_REVERSION_THRESHOLD:  # > $1B Net GEX (Configurable)
        if put_wall < spot_price < call_wall:
            return {
                "signal": "MEAN_REVERSION",
                "bias": "NEUTRAL",
                "message": "Market in Positive Gamma ($1B+). Volatility dampened. Fade moves to walls.",
                "validity": "High",
                "color": "emerald",  # UI hint
            }

    # 2. Acceleration Play (Negative GEX Regime)
    # Condition: Negative GEX OR Price below Zero Gamma (flip point)
    # This implies dealers are short gamma and must chase price (accelerant)
    is_neg_gamma = total_gex < 0
    price_below_flip = (zero_gamma is not None) and (spot_price < zero_gamma)

    if is_neg_gamma or price_below_flip:
        return {
            "signal": "ACCELERATION",
            "bias": "BEARISH_VOL",  # High Volatility Expectation
            "message": "Negative Gamma detected. Dealers chasing price. Expect range expansion.",
            "validity": "High",
            "color": "rose",
        }

    # 3. Magnet Pinning (Late Day)
    # Condition: After 2PM (14:00), price near a major wall (< 0.5% away)
    if current_hour >= 14:
        # Filter valid walls
        valid_walls = [w for w in [call_wall, put_wall] if w is not None]
        if not valid_walls:
            return None

        nearest_wall = min(valid_walls, key=lambda x: abs(x - spot_price))
        dist_pct = abs(spot_price - nearest_wall) / spot_price

        if dist_pct < 0.005:  # Within 0.5%
            return {
                "signal": "MAGNET_PIN",
                "bias": "NEUTRAL",
                "message": f"Price pinning to {nearest_wall} wall into close.",
                "validity": "Medium",
                "color": "amber",
            }

    return None


async def calculate_gex_profile(
    symbol: str = "SPY",
    max_dte: int = 30,
    expiration_dates: Optional[list[date]] = None,
    strike_count: int = 20,
    major_level_threshold: float = 50.0,
    data_wait_seconds: float = 5.0,
    progress_callback=None,
    session: Optional[Session] = None,
) -> GEXResult:
    """
    Calculate GEX profile for a given symbol.

    Args:
        symbol: Ticker symbol (e.g., 'SPY', 'QQQ')
        max_dte: Maximum days to expiration (0 to max_dte). Used if expiration_dates is None.
        expiration_dates: List of specific expiration dates to include. Overrides max_dte.
        strike_count: Number of strikes to include above/below spot (e.g. 20)
        major_level_threshold: Minimum absolute GEX ($M) for major levels
        data_wait_seconds: Time to wait for streaming data
        progress_callback: Optional callback(message) for progress updates

    Returns:
        GEXResult with all calculated data
    """

    def log(msg):
        if progress_callback:
            progress_callback(msg)

    # Authenticate (if no session provided)
    if session:
        log("Using existing session...")
    else:
        # Check credentials
        client_secret, refresh_token = get_credentials()
        if not client_secret or not refresh_token:
            return GEXResult(
                symbol=symbol,
                spot_price=0,
                total_gex=0,
                zero_gamma_level=None,
                max_dte=max_dte,
                strike_range=(0, 0),
                df=pd.DataFrame(),
                strike_gex=pd.DataFrame(),
                major_levels=pd.DataFrame(),
                call_wall=None,
                put_wall=None,
                error="Missing API credentials. Please configure TT_CLIENT_SECRET and TT_REFRESH_TOKEN",
            )

        log("Authenticating with Tastytrade...")
        try:
            session = Session(client_secret, refresh_token)
        except Exception as e:
            return GEXResult(
                symbol=symbol,
                spot_price=0,
                total_gex=0,
                zero_gamma_level=None,
                max_dte=max_dte,
                strike_range=(0, 0),
                df=pd.DataFrame(),
                strike_gex=pd.DataFrame(),
                major_levels=pd.DataFrame(),
                call_wall=None,
                put_wall=None,
                error=f"Authentication failed: {e}",
            )

    log(f"Fetching data for {symbol}...")

    async with DXLinkStreamer(session) as streamer:
        # Get spot price
        log("Getting spot price...")
        spot = await get_spot_price(streamer, symbol)
        if spot is None:
            return GEXResult(
                symbol=symbol,
                spot_price=0,
                total_gex=0,
                zero_gamma_level=None,
                max_dte=max_dte,
                strike_range=(0, 0),
                df=pd.DataFrame(),
                strike_gex=pd.DataFrame(),
                major_levels=pd.DataFrame(),
                call_wall=None,
                put_wall=None,
                error="Could not fetch spot price",
            )

        # Get option chain with fallback that skips malformed rows
        log("Fetching option chain...")
        chain_result, chain_error = _fetch_option_chain_with_fallback(
            session, symbol, log
        )

        if chain_error:
            return GEXResult(
                symbol=symbol,
                spot_price=spot,
                total_gex=0,
                zero_gamma_level=None,
                max_dte=max_dte,
                strike_range=(0, 0),
                df=pd.DataFrame(),
                strike_gex=pd.DataFrame(),
                major_levels=pd.DataFrame(),
                call_wall=None,
                put_wall=None,
                error=chain_error,
            )

        if not chain_result:
            return GEXResult(
                symbol=symbol,
                spot_price=spot,
                total_gex=0,
                zero_gamma_level=None,
                max_dte=max_dte,
                strike_range=(0, 0),
                df=pd.DataFrame(),
                strike_gex=pd.DataFrame(),
                major_levels=pd.DataFrame(),
                call_wall=None,
                put_wall=None,
                error="No chain data returned",
            )

        # Normalize chain to list
        all_options_raw = []
        try:
            if hasattr(chain_result, "options"):
                all_options_raw = list(chain_result.options)
            elif isinstance(chain_result, dict):
                for opts in chain_result.values():
                    if isinstance(opts, list):
                        all_options_raw.extend(opts)
                    # Single option or unexpected structure
                    elif opts:
                        all_options_raw.append(opts)
        except Exception as e:
            log(f"Warning: Error processing option chain structure: {e}")
            # Try to continue with what we have
            pass

        # Filter options
        today = date.today()

        log(f"Filtering options (closest {strike_count} strikes)...")

        # 1. First pass: Filter by Expiration and Validity
        valid_options = []
        for opt in all_options_raw:
            if not hasattr(opt, "expiration_date") or opt.expiration_date is None:
                continue
            if not hasattr(opt, "strike_price") or opt.strike_price is None:
                continue
            if not hasattr(opt, "symbol") or opt.symbol is None:
                continue
            if not hasattr(opt, "option_type") or opt.option_type is None:
                continue

            if expiration_dates is not None:
                # Use strict expiration date filtering
                if opt.expiration_date not in expiration_dates:
                    continue
            else:
                # Use max_dte filtering
                days_to_exp = (opt.expiration_date - today).days
                if not (0 <= days_to_exp <= max_dte):
                    continue
            valid_options.append(opt)

        # 2. Second pass: Group by expiration and select strikes
        all_options_to_monitor = []
        min_strike_seen = float("inf")
        max_strike_seen = float("-inf")

        # Group by expiration
        from collections import defaultdict

        options_by_exp = defaultdict(list)
        for opt in valid_options:
            options_by_exp[opt.expiration_date].append(opt)

        for _exp_date, opts in options_by_exp.items():
            # Group by strike price first
            opts_by_strike = defaultdict(list)
            for opt in opts:
                opts_by_strike[float(opt.strike_price)].append(opt)

            unique_strikes = sorted(opts_by_strike.keys())

            if not unique_strikes:
                continue

            # Find closest strike
            closest_strike = min(unique_strikes, key=lambda x: abs(x - spot))
            closest_idx = unique_strikes.index(closest_strike)

            # Select range of STRIKES
            start_idx = max(0, closest_idx - strike_count)
            end_idx = min(len(unique_strikes), closest_idx + strike_count + 1)

            selected_strikes = unique_strikes[start_idx:end_idx]

            # Collect all options for these strikes
            for strike in selected_strikes:
                selected_opts = opts_by_strike[strike]
                all_options_to_monitor.extend(selected_opts)

                min_strike_seen = min(min_strike_seen, strike)
                max_strike_seen = max(max_strike_seen, strike)

        if not all_options_to_monitor:
            return GEXResult(
                symbol=symbol,
                spot_price=spot,
                total_gex=0,
                zero_gamma_level=None,
                max_dte=max_dte,
                strike_range=(0, 0),
                df=pd.DataFrame(),
                strike_gex=pd.DataFrame(),
                major_levels=pd.DataFrame(),
                call_wall=None,
                put_wall=None,
                error="No options found after filtering",
            )

        lower_bound = min_strike_seen if min_strike_seen != float("inf") else 0
        upper_bound = max_strike_seen if max_strike_seen != float("-inf") else 0

        log(f"Found {len(all_options_to_monitor)} options to analyze...")

        # Fetch initial market data snapshot (OI and Volume)
        log("Fetching market data (OI, Volume)...")
        market_data_map = {}
        all_symbols = [opt.symbol for opt in all_options_to_monitor]

        for i in range(0, len(all_symbols), 100):
            chunk = all_symbols[i : i + 100]
            try:
                market_data = await a_get_market_data_by_type(session, options=chunk)
                for md in market_data:
                    entry = {}
                    if md.open_interest is not None:
                        entry["oi"] = int(md.open_interest)
                    if hasattr(md, "volume") and md.volume is not None:
                        entry["volume"] = int(md.volume)

                    if entry:
                        market_data_map[md.symbol] = entry
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

            gamma = (
                float(matching_greek.gamma)
                if matching_greek and matching_greek.gamma
                else 0.0
            )

            # Initial baselines from snapshot
            md_entry = market_data_map.get(opt.symbol, {})
            oi = md_entry.get("oi", 0)
            volume = md_entry.get("volume", 0)

            if matching_summary:
                if matching_summary.open_interest:
                    oi = int(matching_summary.open_interest)
                # Safely access day_volume as it might be missing from the event
                vol_val = getattr(matching_summary, "day_volume", 0)
                if vol_val:
                    volume = int(vol_val)

            strike = float(opt.strike_price)
            raw_gex_m = (oi * gamma * 100 * (spot**2) * 0.01) / 1_000_000

            is_call = opt.option_type == "C"
            net_gex = raw_gex_m if is_call else -raw_gex_m

            data.append(
                {
                    "Expiration": opt.expiration_date,
                    "Strike": strike,
                    "Type": "Call" if is_call else "Put",
                    "OI": oi,
                    "Volume": volume,
                    "Gamma": gamma,
                    "Net GEX ($M)": round(net_gex, 4),
                    "Call GEX ($M)": round(raw_gex_m if is_call else 0.0, 4),
                    "Put GEX ($M)": round(-raw_gex_m if not is_call else 0.0, 4),
                }
            )

        if not data:
            return GEXResult(
                symbol=symbol,
                spot_price=spot,
                total_gex=0,
                zero_gamma_level=None,
                max_dte=max_dte,
                strike_range=(lower_bound, upper_bound),
                df=pd.DataFrame(),
                strike_gex=pd.DataFrame(),
                major_levels=pd.DataFrame(),
                call_wall=None,
                put_wall=None,
                error="No GEX data calculated",
            )

        df = pd.DataFrame(data)
        total_gex = df["Net GEX ($M)"].sum()

        # Add helper columns for separate aggregations
        df["Call OI"] = df.apply(
            lambda x: x["OI"] if x["Type"] == "Call" else 0, axis=1
        )
        df["Put OI"] = df.apply(lambda x: x["OI"] if x["Type"] == "Put" else 0, axis=1)
        df["Call Volume"] = df.apply(
            lambda x: x["Volume"] if x["Type"] == "Call" else 0, axis=1
        )
        df["Put Volume"] = df.apply(
            lambda x: x["Volume"] if x["Type"] == "Put" else 0, axis=1
        )

        # Aggregate by strike
        strike_gex = (
            df.groupby("Strike")[
                [
                    "Net GEX ($M)",
                    "Call GEX ($M)",
                    "Put GEX ($M)",
                    "OI",
                    "Volume",
                    "Call OI",
                    "Put OI",
                    "Call Volume",
                    "Put Volume",
                ]
            ]
            .sum()
            .reset_index()
        )
        strike_gex.rename(
            columns={"OI": "Total OI", "Volume": "Total Volume"}, inplace=True
        )
        strike_gex = strike_gex.sort_values(by="Strike")

        # Calculate Volume-Weighted GEX
        total_vol_all_strikes = strike_gex["Total Volume"].sum()

        if total_vol_all_strikes > 0:
            strike_gex["VolWeightedGEX"] = strike_gex["Net GEX ($M)"] * (
                strike_gex["Total Volume"] / total_vol_all_strikes
            )
        else:
            strike_gex["VolWeightedGEX"] = 0.0

        strike_gex["VolWeightedGEX"] = strike_gex["VolWeightedGEX"].round(6)

        # Major levels
        major_levels = strike_gex[
            strike_gex["Net GEX ($M)"].abs() > major_level_threshold
        ].copy()
        major_levels["Net GEX ($M)"] = major_levels["Net GEX ($M)"].round(1)
        major_levels["Type"] = major_levels["Net GEX ($M)"].apply(
            lambda x: "Call" if x > 0 else "Put"
        )

        # Find call wall (highest positive GEX) and put wall (lowest negative GEX)
        positive_gex = strike_gex[strike_gex["Net GEX ($M)"] > 0]
        negative_gex = strike_gex[strike_gex["Net GEX ($M)"] < 0]

        call_wall = None
        put_wall = None

        if not positive_gex.empty:
            call_wall = positive_gex.loc[
                positive_gex["Net GEX ($M)"].idxmax(), "Strike"
            ]
        if not negative_gex.empty:
            put_wall = negative_gex.loc[negative_gex["Net GEX ($M)"].idxmin(), "Strike"]

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
            strategy=analyze_strategy(total_gex, spot, call_wall, put_wall, zero_gamma),
            error=None,
        )


def run_gex_calculation(
    symbol: str = "SPY",
    max_dte: int = 30,
    expiration_dates: Optional[list[date]] = None,
    strike_count: int = 20,
    major_level_threshold: float = 50.0,
    data_wait_seconds: float = 5.0,
    progress_callback=None,
    session: Optional[Session] = None,
) -> GEXResult:
    """Synchronous wrapper for calculate_gex_profile."""
    return asyncio.run(
        calculate_gex_profile(
            symbol=symbol,
            max_dte=max_dte,
            expiration_dates=expiration_dates,
            strike_count=strike_count,
            major_level_threshold=major_level_threshold,
            data_wait_seconds=data_wait_seconds,
            progress_callback=progress_callback,
            session=session,
        )
    )
