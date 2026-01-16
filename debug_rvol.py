
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

def check_rvol(ticker):
    print(f"Fetching data for {ticker}...")
    df = yf.download(ticker, period="1mo", interval="1d", progress=False)
    
    if df.empty:
        print("No data.")
        return

    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(ticker, level=1, axis=1) # Or simple column access
    
    # Recalculate if it was multiindex
    # Just grab ticker col if it exists
    # If not multi-index (e.g. single ticker download sometimes), it works.
    
    # Actually yf.download for single ticker in new version might still be multiindex or not depending on auto_adjust.
    # Let's clean it.
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df = df.xs(ticker, axis=1, level=1)
        except:
             # Fallback if level is 0
             df.columns = df.columns.droplevel(1)
             
    df['vol_avg'] = df['Volume'].rolling(window=20).mean()
    df['rvol'] = df['Volume'] / df['vol_avg']
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    print("\n--- DATA CHECK ---")
    print(f"Timestamp (Last): {last.name}")
    print(f"Timestamp (Prev): {prev.name}")
    
    print(f"\nLast Volume: {last['Volume']}")
    print(f"Avg Volume : {last['vol_avg']}")
    print(f"RVOL       : {last['rvol']:.4f}")
    
    print(f"\nPrev Volume: {prev['Volume']}")
    print(f"Prev RVOL  : {prev['rvol']:.4f}")
    
    # Time check
    now = datetime.datetime.now()
    print(f"\nCurrent System Time: {now}")

if __name__ == "__main__":
    check_rvol("COALINDIA.NS")
