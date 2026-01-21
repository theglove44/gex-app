import asyncio

from dotenv import load_dotenv

from gex_app.core.gex_core import calculate_gex_profile

load_dotenv()


async def main():
    print("Running reproduction script for Universe Scanner issue...")

    symbols = ["SPX", "TSLA"]
    max_dte = 30  # Verify fix

    print(f"Testing symbols: {symbols} with max_dte={max_dte}")

    for sym in symbols:
        print(f"\n--- Scanning {sym} ---")
        try:
            result = await calculate_gex_profile(
                symbol=sym,
                max_dte=max_dte,
                strike_count=100,  # Replaced strike_range_pct with a fixed count
                major_level_threshold=50.0,
                data_wait_seconds=2.0,
            )

            if result.error:
                print(f"FAILED: {sym} returned error: {result.error}")
            else:
                print(f"SUCCESS: {sym} - Net GEX: ${result.total_gex}M")
                print(f"  Spot: {result.spot_price}")
                print(f"  Call/Put Wall: {result.call_wall}/{result.put_wall}")

        except Exception as e:
            print(f"EXCEPTION processing {sym}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
