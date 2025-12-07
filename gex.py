import asyncio
import os
from datetime import date, timedelta
from decimal import Decimal
import pandas as pd
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Greeks, Quote
from tastytrade.instruments import get_option_chain

# Load environment variables
load_dotenv()

CLIENT_SECRET = os.getenv('TT_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('TT_REFRESH_TOKEN')

async def get_spot_price(streamer, symbol):
    """Fetches the current spot price for the symbol."""
    await streamer.subscribe(Quote, [symbol])
    # Fix: get_event takes only the event type class, not the symbol in standard usage for single event wait
    # wrapper. But let's check if we can wait for specific event.
    # The SDK get_event(EventType) returns the next event of that type.
    # Since we only subscribed to one, it should be fine.
    quote_event = await streamer.get_event(Quote)
    
    # Debug: inspect fields
    if quote_event:
        print(f"Quote fields: {quote_event}")
        # Depending on SDK, it might be bidPrice/askPrice/lastPrice
        # In dxfeed, it is often just 'askPrice', 'bidPrice'. 'last' might not be standard.
        # Let's try to infer or fallback.
        
    # Return last price or reasonable default/ask/bid average
    if quote_event:
        if hasattr(quote_event, 'last_price') and quote_event.last_price:
             return float(quote_event.last_price)
             
        # Fallback to mid
        if hasattr(quote_event, 'ask_price') and hasattr(quote_event, 'bid_price') and quote_event.ask_price and quote_event.bid_price:
             return (float(quote_event.ask_price) + float(quote_event.bid_price)) / 2.0
             
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
        # Step 3: Get Valid Expirations (0-30 DTE)
        print("Fetching expirations and chain...")
        try:
            # Returns dict: {date: [Option, ...]} OR OptionChain object with .options list
            chain_result = get_option_chain(session, symbol)
        except Exception as e:
            print(f"Failed to fetch option chain: {e}")
            return

        if not chain_result:
            print("No chain data returned.")
            return

        # Normalize to list of options
        all_options_raw = []
        if hasattr(chain_result, 'options'):
            # Handling object return (as per PR feedback)
            all_options_raw = list(chain_result.options)
        elif isinstance(chain_result, dict):
            # Handling dict return (current local SDK)
            for opts in chain_result.values():
                all_options_raw.extend(opts)
        else:
            print(f"Unknown chain result type: {type(chain_result)}")
            return

        today = date.today()
        
        # Step 4: Filter Strings and Collect Options
        all_options_to_monitor = [] # List of Option objects
        # Define filter bounds (ATM +/- 20%)
        lower_bound = spot * 0.80
        upper_bound = spot * 1.20
        
        print(f"Filtering Strikes: {lower_bound:.2f} - {upper_bound:.2f}")

        # Unique expirations for reporting
        valid_exps = set()

        for opt in all_options_raw:
            # Check DTE
            days_to_exp = (opt.expiration_date - today).days
            if not (0 <= days_to_exp <= max_dte):
                continue
                
            # Check Strike
            if not (lower_bound <= float(opt.strike_price) <= upper_bound):
                 continue
            
            all_options_to_monitor.append(opt)
            valid_exps.add(opt.expiration_date)

        sorted_exps = sorted(list(valid_exps))
        
        if not sorted_exps:
            print(f"No expirations found within {max_dte} days with filtered strikes.")
            return

        print(f"Found {len(sorted_exps)} Expirations: {sorted_exps[0]} to {sorted_exps[-1]}")
        print(f"Monitoring {len(all_options_to_monitor)} options.")
        
        if not all_options_to_monitor:
            print("No options found after filtering.")
            return

        # Prepare background listener
        greeks_events = []
        
        async def listen_greeks():
            async for event in streamer.listen(Greeks):
                greeks_events.append(event)

        # Start listening BEFORE subscribing to ensure we catch the initial distinct messages
        listener_task = asyncio.create_task(listen_greeks())

        # Step 5: Subscribe to Greeks (Batch)
        total_subs = len(all_options_to_monitor)
        print(f"Subscribing to Greeks for {total_subs} filtered options...")
        symbols_to_sub = [opt.symbol for opt in all_options_to_monitor]
        await streamer.subscribe(Greeks, symbols_to_sub)
        
        # Wait for data
        print("Waiting for Greeks data (5s)...")
        await asyncio.sleep(5)
        
        # Stop listener
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        
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