import asyncio
import os
from datetime import date, timedelta
from decimal import Decimal
import pandas as pd
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Greeks, Quote
from tastytrade.instruments import get_option_chain, get_option_expirations

# Load environment variables
load_dotenv()

CLIENT_SECRET = os.getenv('TT_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('TT_REFRESH_TOKEN')

async def get_spot_price(streamer, symbol):
    """Fetches the current spot price for the symbol."""
    await streamer.subscribe(Quote, [symbol])
    quote_event = await streamer.get_event(Quote, symbol)
    # Return last price or reasonable default/ask/bid average
    if quote_event and quote_event.last:
        return float(quote_event.last)
    return None

async def calculate_gex_profile(symbol='SPY', max_dte=30):
    if not CLIENT_SECRET or not REFRESH_TOKEN:
        print("Error: TT_CLIENT_SECRET and TT_REFRESH_TOKEN must be set in .env file")
        return

    # Step 1: Auth
    try:
        session = Session(CLIENT_SECRET, REFRESH_TOKEN)
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    print(f"Authenticated. Fetching data for {symbol} (0-{max_dte} DTE)...")

    # Step 2: Connect Streamer & Get Spot
    async with DXLinkStreamer(session) as streamer:
        print("Fetching spot price...")
        spot = await get_spot_price(streamer, symbol)
        if spot is None:
            print("Could not fetch spot price. Aborting.")
            return
        
        print(f"Spot Price: {spot}")

        # Step 3: Get Valid Expirations (0-30 DTE)
        print("Fetching expirations...")
        try:
            all_exps = get_option_expirations(session, symbol)
        except Exception as e:
            print(f"Failed to fetch expirations: {e}")
            return

        today = date.today()
        valid_exps = [
            d for d in all_exps 
            if 0 <= (d - today).days <= max_dte
        ]
        
        if not valid_exps:
            print(f"No expirations found within {max_dte} days.")
            return

        print(f"Found {len(valid_exps)} Expirations: {valid_exps[0]} to {valid_exps[-1]}")

        # Step 4: Fetch Chains & Filter Strikes
        # "Batching": Collect all subscriptions first to do one big subscribe (or subscribe per expiry if memory constrained, but list is better for streamer)
        
        all_options_to_monitor = [] # List of Option objects
        # Define filter bounds (ATM +/- 20%)
        lower_bound = spot * 0.80
        upper_bound = spot * 1.20
        
        print(f"Filtering Strikes: {lower_bound:.2f} - {upper_bound:.2f}")

        for exp_date in valid_exps:
            try:
                # Fetch chain for date
                # Optimize: get_option_chain is a REST call
                chain = get_option_chain(session, symbol, expiration_date=exp_date)
                
                # Filter Options
                filtered_options = [
                    opt for opt in chain.options
                    if lower_bound <= float(opt.strike_price) <= upper_bound
                ]
                all_options_to_monitor.extend(filtered_options)
                
            except Exception as e:
                print(f"Error fetching chain for {exp_date}: {e}")
                continue
        
        if not all_options_to_monitor:
            print("No options found after filtering.")
            return

        total_subs = len(all_options_to_monitor)
        print(f"Subscribing to Greeks for {total_subs} filtered options...")

        # Step 5: Subscribe to Greeks (Batch)
        # Tastytrade API handles batching internally, but we pass full list
        # Extract symbols
        symbols_to_sub = [opt.symbol for opt in all_options_to_monitor]
        
        # Subscribe
        await streamer.subscribe(Greeks, symbols_to_sub)
        
        # Fetch Events (using get_events with timeout)
        # We need to wait enough time for the stream to populate.
        # Ideally, we would loop until we have X% coverage, but specific timeout is safer for a script.
        print("Waiting for Greeks data...")
        greeks_events = await streamer.get_events(Greeks, timeout=5) # 5s timeout
        
        # Map for O(1) lookup
        greek_map = {g.event_symbol: g for g in greeks_events}
        print(f"Received Greeks for {len(greek_map)}/{total_subs} options.")

        # Step 6: Calcs
        data = []
        for opt in all_options_to_monitor:
            matching_greek = greek_map.get(opt.symbol)
            if not matching_greek:
                continue

            gamma = float(matching_greek.gamma) if matching_greek.gamma else 0.0
            oi = int(opt.open_interest) if opt.open_interest else 0
            strike = float(opt.strike_price)
            
            # GEX Formula
            # Gamma * OI * 100 * Spot^2 * 0.01 / 1B or 1M?
            # User used: oi * gamma * 100 * (spot**2) * 0.01 / 1_000_000 (Millions)
            raw_gex_m = (oi * gamma * 100 * (spot**2) * 0.01) / 1_000_000
            
            # Sign Convention: Call Wall = Positive, Put Wall = Negative
            is_call = opt.option_type == 'C'
            
            if is_call:
                net_gex = raw_gex_m # Positive
            else:
                net_gex = -raw_gex_m # Negative for Puts
            
            data.append({
                'Expiration': opt.expiration_date,
                'Strike': strike,
                'Type': 'Call' if is_call else 'Put',
                'OI': oi,
                'Gamma': gamma,
                'Net GEX ($M)': round(net_gex, 4)
            })

        if not data:
            print("No GEX calculated.")
            return

        df = pd.DataFrame(data)
        
        # Aggregation: Group by Strike to see "Gamma Walls" across all dates
        # Or Group by Strike for Summary
        total_gex = df['Net GEX ($M)'].sum()
        
        print(f"\n=== GEX Profile (SPY, 0-{max_dte} DTE) ===")
        print(f"Total Net GEX: ${total_gex:,.2f}M")
        
        # Pivot or Group by Strike
        strike_gex = df.groupby('Strike')['Net GEX ($M)'].sum().reset_index()
        strike_gex = strike_gex.sort_values(by='Strike')
        
        # Output Top Levels (Walls)
        # Filter: > 50M abs
        walls = strike_gex[strike_gex['Net GEX ($M)'].abs() > 50].copy()
        walls['Net GEX ($M)'] = walls['Net GEX ($M)'].round(1)
        
        if not walls.empty:
            print("\nMajor Gamma Levels (>$50M):")
            print(walls.to_string(index=False))
        else:
            print("\nNo major gamma walls (>$50M) found.")

        # Optional: Save to CSV
        # df.to_csv('gex_profile.csv', index=False)
        # print("\nFull data saved to gex_profile.csv")

if __name__ == "__main__":
    asyncio.run(calculate_gex_profile('SPY', max_dte=30))