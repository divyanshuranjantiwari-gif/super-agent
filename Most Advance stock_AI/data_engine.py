import yfinance as yf
import pandas as pd
import os
import requests
from config import OHLCV_DIR, EXCHANGE_SUFFIX, LOOKBACK_YEARS
from tqdm import tqdm
import time

class DataEngine:
    def __init__(self):
        self.symbols = []

    def fetch_bse_symbols(self):
        """
        Fetches the list of active BSE symbols.
        For this implementation, we will use a hardcoded list of top BSE stocks 
        or fetch from a reliable source if available. 
        To be robust, we can try to fetch from a public GitHub list or BSE website.
        For now, we will simulate with a list of top 500 stocks to avoid massive API limits immediately,
        but the architecture supports all.
        """
        print("Fetching BSE Symbols...")
        # In a real full-scale scenario, we would scrape the BSE website or use a paid API.
        # For this agent, we will use a diverse list of sectors.
        # We can also use a library like 'nsetools' but for BSE specifically it's harder.
        # Let's use a small list for testing and a larger list capability.
        
        # Placeholder: In production, load from a CSV of all ~4000 BSE companies.
        # Here we define a mix of Large, Mid, and Small caps.
        self.symbols = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC",
            "KOTAKBANK", "LICI", "HINDUNILVR", "LT", "BAJFINANCE", "HCLTECH", "ASIANPAINT",
            "MARUTI", "TITAN", "SUNPHARMA", "ULTRACEMCO", "NTPC", "TATAMOTORS", "POWERGRID",
            "TATASTEEL", "JSWSTEEL", "ADANIENT", "ADANIPORTS", "M&M", "ONGC", "COALINDIA",
            "WIPRO", "BAJAJFINSV", "BPCL", "NESTLEIND", "TECHM", "HINDALCO", "GRASIM",
            "CIPLA", "EICHERMOT", "DRREDDY", "BRITANNIA", "TATACONSUM", "HEROMOTOCO",
            "APOLLOHOSP", "DIVISLAB", "SBILIFE", "BAJAJ-AUTO", "UPL"
        ]
        
        # Append suffix
        self.symbols = [f"{s}{EXCHANGE_SUFFIX}" for s in self.symbols]
        print(f"Loaded {len(self.symbols)} symbols.")
        return self.symbols

    def fetch_ohlcv(self, symbol, period="10y", interval="1d"):
        """
        Fetches OHLCV data for a given symbol.
        """
        file_path = os.path.join(OHLCV_DIR, f"{symbol}.csv")
        
        # Check if we have recent data (e.g., less than 1 day old)
        # For now, we force fetch to ensure freshness
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"No data found for {symbol}")
                return None
            
            # Save to CSV
            df.to_csv(file_path)
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    def update_all_data(self):
        """
        Updates data for all symbols.
        """
        if not self.symbols:
            self.fetch_bse_symbols()
            
        print(f"Updating data for {len(self.symbols)} symbols...")
        for symbol in tqdm(self.symbols):
            self.fetch_ohlcv(symbol)
            # Sleep to avoid rate limits
            time.sleep(0.5)
        print("Data update complete.")

if __name__ == "__main__":
    engine = DataEngine()
    engine.update_all_data()
