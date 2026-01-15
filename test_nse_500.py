try:
    from nsepython import nse_get_index_stocks
    print("Attempting to fetch NIFTY 500...")
    # nse_get_index_stocks returns a list of dictionaries usually
    stocks = nse_get_index_stocks("NIFTY 500")
    print(f"Fetched {len(stocks)} stocks.")
    print(f"First 1: {stocks[:1]}")
    
    # Extract symbols
    symbols = [s['symbol'] + ".NS" for s in stocks]
    print(f"First 5 Symbols: {symbols[:5]}")
except Exception as e:
    print(f"Error: {e}")
