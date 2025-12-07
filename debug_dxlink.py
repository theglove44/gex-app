import asyncio
import os
import logging
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.instruments import get_option_chain
from tastytrade.dxfeed import Greeks
import datetime

# Setup logging to capture WebSocket messages
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

CLIENT_SECRET = os.getenv('TT_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('TT_REFRESH_TOKEN')

async def main():
    if not CLIENT_SECRET or not REFRESH_TOKEN:
        print("Error: TT_CLIENT_SECRET and TT_REFRESH_TOKEN must be set")
        return

    print("Authenticating...")
    session = Session(CLIENT_SECRET, REFRESH_TOKEN)
    
    print("Connecting to DXLink...")
    async with DXLinkStreamer(session) as streamer:
        try:
            # Correct way to get expirations is via get_option_chain which returns a dict/structure
            
            chain = get_option_chain(session, 'SPY')
            # chain keys are dates
            if not chain:
                print("No options found.")
                return
            
            # Get first expiration date
            first_exp = sorted(chain.keys())[0]
            print(f"Targeting Expiration: {first_exp}")
            
            options_for_exp = chain[first_exp]
            
            if isinstance(options_for_exp, list) and options_for_exp:
                example_option = options_for_exp[0]
            else:
                 print(f"Unexpected structure for exp: {type(options_for_exp)}")
                 return

            op_symbol = example_option.symbol
            print(f"Testing subscription for Option: {op_symbol}")
            
            print(f"Subscribing to Greeks for {op_symbol}...")
            await streamer.subscribe(Greeks, [op_symbol])
            
            print("Waiting for data...")
            # Validating get_event signature fix
            event = await streamer.get_event(Greeks)
            print(f"Received Greeks event: {event}")
            
        except Exception as e:
            print(f"Error during option setup: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
