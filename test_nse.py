try:
    from nsepython import nse_eq_symbols
    print("Attempting to fetch symbols...")
    # nse_eq_symbols() usually returns a list of all symbols
    symbols = nse_eq_symbols()
    print(f"Fetched {len(symbols)} symbols.")
    print(f"First 5: {symbols[:5]}")
except Exception as e:
    print(f"Error: {e}")
