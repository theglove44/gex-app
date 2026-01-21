import asyncio
import os

from dotenv import load_dotenv
from tastytrade import Session
from tastytrade.instruments import get_option_chain

load_dotenv()
CLIENT_SECRET = os.getenv("TT_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("TT_REFRESH_TOKEN")


async def main():
    session = Session(CLIENT_SECRET, REFRESH_TOKEN)
    chain = get_option_chain(session, "SPY")
    first_exp = sorted(chain.keys())[0]
    options = chain[first_exp]
    target = options[0]
    print(f"Target Symbol: {target.symbol}")
    print(f"Target Type: {type(target)}")
    print("Properties:")
    for d in dir(target):
        if not d.startswith("_"):
            val = getattr(target, d)
            print(f"{d}: {val}")


if __name__ == "__main__":
    asyncio.run(main())
