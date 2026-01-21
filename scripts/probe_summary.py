import asyncio
import os
import sys

from dotenv import load_dotenv
from tastytrade import DXLinkStreamer, Session
from tastytrade.dxfeed import Summary
from tastytrade.instruments import get_option_chain

# Ensure we can import from project root
sys.path.append(os.getcwd())

load_dotenv()


async def probe():
    os.getenv("TT_USERNAME")
    client_secret = os.getenv("TT_CLIENT_SECRET")
    refresh_token = os.getenv("TT_REFRESH_TOKEN")

    if not client_secret or not refresh_token:
        print("Missing credentials")
        return

    session = Session(client_secret, refresh_token)

    # Get an option symbol
    chain = get_option_chain(session, "SPX")
    dates = sorted(chain.keys())
    exp_date = dates[0]
    strikes = chain[exp_date]
    mid_strike = strikes[len(strikes) // 2]
    # Chain returns list of Option objects.
    option = mid_strike  # mid_strike is already an Option object
    stream_symbol = option.symbol

    print(f"Probing Option: {stream_symbol}")

    async with DXLinkStreamer(session) as streamer:
        # Subscribe to Option Summary (not Quote)
        await streamer.subscribe(Summary, [stream_symbol])

        print("Waiting for Summary event...")
        acc_event = await streamer.get_event(Summary)

        if acc_event:
            print("\n--- Summary Object Attributes ---")
            for attr in dir(acc_event):
                if not attr.startswith("_"):
                    try:
                        val = getattr(acc_event, attr)
                        if not callable(val):
                            print(f"{attr}: {val}")
                    except:
                        pass
        else:
            print("No event received")


if __name__ == "__main__":
    asyncio.run(probe())
