
try:
    import tastytrade.instruments as instruments
    print("Attributes in tastytrade.instruments:")
    print(dir(instruments))
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
