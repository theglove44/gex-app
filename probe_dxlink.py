import asyncio
import os
import logging
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.instruments import get_option_chain
from tastytrade.dxfeed import Greeks, Quote, Trade

# Logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()
CLIENT_SECRET = os.getenv('TT_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('TT_REFRESH_TOKEN')

async def main():
    session = Session(CLIENT_SECRET, REFRESH_TOKEN)
    async with DXLinkStreamer(session) as streamer:
        chain = get_option_chain(session, 'SPY')
        first_exp = sorted(chain.keys())[0]
        # Get a near-the-money option if possible, or just the first one
        # chain[exp] is a list of Option objects
        options = chain[first_exp]
        # Pick one
        target_option = options[0]
        symbol = target_option.symbol
        print(f"Testing Symbol: {symbol}")

        # Subscribe to SPY (equity) as control
        print("Subscribing to SPY (equity) Quote...")
        await streamer.subscribe(Quote, ['SPY'])

        # Subscribe to Quote, Trade, Greeks
        print(f"Subscribing to Quote, Trade, Greeks for {symbol}...")
        await streamer.subscribe(Quote, [symbol])
        await streamer.subscribe(Trade, [symbol])
        await streamer.subscribe(Greeks, [symbol])

        print("Listening for 10 seconds...")
        
        async def listener():
            async for event in streamer.listen(Quote):
                print(f"RECEIVED QUOTE: {event}")
            async for event in streamer.listen(Trade):
                print(f"RECEIVED TRADE: {event}")
            async for event in streamer.listen(Greeks):
                print(f"RECEIVED GREEKS: {event}")

        # Listen in background (but listen() is an iterator, so we need to handle multiple event types)
        # Actually streamer.listen(EventType) filters. We can just iterate usually?
        # No, streamer.listen() is a method that returns an async generator for specific events.
        # We need to run multiple listeners or use a general listener if available.
        # DXLinkStreamer doesn't seem to have a 'listen_all'.
        
        # We'll launch distinct tasks
        t1 = asyncio.create_task(monitor(streamer, Quote, "QUOTE"))
        t2 = asyncio.create_task(monitor(streamer, Trade, "TRADE"))
        t3 = asyncio.create_task(monitor(streamer, Greeks, "GREEKS"))
        
        await asyncio.sleep(10)
        t1.cancel()
        t2.cancel()
        t3.cancel()

async def monitor(streamer, event_type, label):
    try:
        async for event in streamer.listen(event_type):
            print(f"[{label}] {event}")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[{label}] Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
