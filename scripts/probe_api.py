import os
import sys

from dotenv import load_dotenv
from tastytrade import Session
from tastytrade.instruments import get_option_chain

load_dotenv()

CLIENT_SECRET = os.getenv("TT_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("TT_REFRESH_TOKEN")

if not CLIENT_SECRET or not REFRESH_TOKEN:
    print("Error: TT_CLIENT_SECRET and TT_REFRESH_TOKEN must be set")
    sys.exit(1)

session = Session(CLIENT_SECRET, REFRESH_TOKEN)

try:
    print("Calling get_option_chain('SPY')...")
    chain = get_option_chain(session, "SPY")
    print(f"Type of chain: {type(chain)}")
    print(f"Attributes: {dir(chain)}")

    if hasattr(chain, "expirations"):
        print(f"Expirations found: {len(chain.expirations)}")
        print(f"Sample: {chain.expirations[0]}")
    elif isinstance(chain, dict):
        print(f"Chain keys: {chain.keys()}")

except Exception as e:
    print(f"Error calling get_option_chain: {e}")
