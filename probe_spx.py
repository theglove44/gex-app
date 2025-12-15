import asyncio
import os
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Quote, Trade, Summary, Greeks

load_dotenv()

async def main():
    user = os.getenv('TT_CLIENT_SECRET')
    password = os.getenv('TT_REFRESH_TOKEN')
    
    print(f"Authenticating...")
    session = Session(user, password)
    
    async with DXLinkStreamer(session) as streamer:
        symbol = "SPX"
        print(f"Subscribing to {symbol} (Quote, Trade, Summary)...")
        
        await streamer.subscribe(Quote, [symbol])
        await streamer.subscribe(Trade, [symbol])
        await streamer.subscribe(Summary, [symbol])
        
        print("Listening for 5 seconds...")
        
        t_end = asyncio.get_event_loop().time() + 5.0
        while asyncio.get_event_loop().time() < t_end:
            try:
                # Poll for any event
                q = await asyncio.wait_for(streamer.get_event(Quote), timeout=0.1)
                print(f"QUOTE: {q}")
            except: pass
            
            try:
                t = await asyncio.wait_for(streamer.get_event(Trade), timeout=0.1)
                print(f"TRADE: {t}")
            except: pass

            try:
                s = await asyncio.wait_for(streamer.get_event(Summary), timeout=0.1)
                print(f"SUMMARY: {s}")
            except: pass

if __name__ == "__main__":
    asyncio.run(main())
