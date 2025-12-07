import asyncio
import os
import logging
from typing import Optional
from decimal import Decimal
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed.event import IndexedEvent
from tastytrade.instruments import get_option_chain
from tastytrade.dxfeed import Quote

# Logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()
CLIENT_SECRET = os.getenv('TT_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('TT_REFRESH_TOKEN')

# Define MinimalGreeks
# We must match the class name expected by Pydantic likely, 
# but DXLinkStreamer uses the class to determine subscription type.
# It usually uses `_event_label` if present, or class name?
# The `tastytrade` SDK usually uses `__name__` or `_event_tag`?
# Checking `Greeks` inheritance: it inherits IndexedEvent.
# Let's try to set `_schema` or whatever if needed. 
# But usually `Event` classes in tastytrade are Pydantic models.

class MinimalGreeks(IndexedEvent):
    # Depending on SDK version, might need Config or similar.
    # Assuming Pydantic V2 or V1.
    eventSymbol: Optional[str] = None
    eventTime: Optional[int] = None
    delta: Optional[Decimal] = None
    gamma: Optional[Decimal] = None
    
    # Override event label if SDK uses it
    # note: we don't know the internal logic for label, but usually it's class name or mapped.
    # We will assume class name 'MinimalGreeks' might be WRONG on wire.
    # We need to force it to "Greeks".
    # Pydantic models don't easily allow aliasing the class name for the registry unless we trick it.
    # But `subscribe` sends a string.
    
    # Wait, `DXLinkStreamer.subscribe` takes `event_type`.
    # It constructs `FEED_SETUP` with `event_type.__name__` usually?
    # Or calls `get_event_name(event_type)`?
    
    # If I rename the class to Greeks, I can shadow the import.
    pass

# Redefine class name to match wire protocol "Greeks"
Greeks = MinimalGreeks
Greeks.__name__ = "Greeks"

async def main():
    session = Session(CLIENT_SECRET, REFRESH_TOKEN)
    async with DXLinkStreamer(session) as streamer:
        chain = get_option_chain(session, 'SPY')
        first_exp = sorted(chain.keys())[0]
        options = chain[first_exp]
        target_option = options[0]
        symbol = target_option.symbol
        print(f"Testing Symbol: {symbol}")

        # Subscribe to Quote (Control)
        print("Subscribing to Quote...")
        await streamer.subscribe(Quote, ['SPY'])
        
        # Subscribe to MinimalGreeks
        print("Subscribing to MinimalGreeks (as Greeks)...")
        # Subscription uses the class name or introspection?
        # If it uses `Event` introspection, it might look at internal registry.
        # But let's try.
        await streamer.subscribe(Greeks, [symbol])

        print("Listening for 10 seconds...")
        
        async def monitor(label):
            try:
                # listen(Greeks) might check isinstance.
                async for event in streamer.listen(Greeks):
                    print(f"[{label}] {event}")
            except Exception as e:
                print(f"Error: {e}")

        t = asyncio.create_task(monitor("GREEKS"))
        await asyncio.sleep(10)
        t.cancel()

if __name__ == "__main__":
    asyncio.run(main())
