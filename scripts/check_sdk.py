try:
    from tastytrade.instruments import get_option_expirations

    print("get_option_expirations: FOUND")
except ImportError:
    print("get_option_expirations: NOT_FOUND")

try:
    from tastytrade.instruments import get_option_chain

    print("get_option_chain: FOUND")
except ImportError:
    print("get_option_chain: NOT_FOUND")
