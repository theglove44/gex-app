import asyncio
import os
import logging
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.instruments import get_option_chain
from tastytrade.dxfeed import Summary

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
        options = chain[first_exp]
        target = options[0]
        
        symbol = target.streamer_symbol 
        print(f"Testing Streamer Symbol: {symbol}")

        print(f"Subscribing to Summary for {symbol}...")
        await streamer.subscribe(Summary, [symbol])

        print("Listening for 10 seconds...")
        
        async def monitor(label, event_type):
            try:
                async for event in streamer.listen(event_type):
                    print(f"[{label}] {event}")
            except Exception as e:
                print(f"[{label}] Error: {e}")

        t1 = asyncio.create_task(monitor("SUMMARY", Summary))
        
        await asyncio.sleep(10)
        t1.cancel()

if __name__ == "__main__":
    asyncio.run(main())
