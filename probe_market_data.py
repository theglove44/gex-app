import asyncio
import os
import logging
from dotenv import load_dotenv
from tastytrade import Session
from tastytrade.instruments import get_option_chain
from tastytrade.market_data import get_market_data_by_type

# Logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()
CLIENT_SECRET = os.getenv('TT_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('TT_REFRESH_TOKEN')

def main():
    session = Session(CLIENT_SECRET, REFRESH_TOKEN)
    
    # Get one option symbol
    chain = get_option_chain(session, 'SPY')
    first_exp = sorted(chain.keys())[0]
    options = chain[first_exp]
    target = options[0]
    symbol = target.symbol
    streamer_symbol = target.streamer_symbol
    
    print(f"Target Symbol: {symbol}")
    print(f"Streamer Symbol: {streamer_symbol}")
    
    # Fetch Market Data
    print("Fetching market data...")
    # market_data needs list of symbols. 
    # Use 'options' arg for equity-option
    data_list = get_market_data_by_type(session, options=[symbol])
    
    if data_list:
        md = data_list[0]
        print(f"Market Data Symbol: {md.symbol}") # Check if this matches symbol or streamer_symbol
        print(f"Open Interest: {md.open_interest}")
        print(f"Full Data: {md}")
    else:
        print("No market data returned.")

if __name__ == "__main__":
    main()
