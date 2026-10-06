"""
Super Agent 4.0 — Centralized Data Fetcher
============================================
Downloads all OHLCV data once in a single batch call,
eliminating redundant per-stock API requests.
"""
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

_cache = {}

def fetch_all_data(tickers, period="1y"):
    """Download OHLCV for all tickers in one batch call."""
    global _cache
    _cache = {}  # Clear previous cache
    
    print(f"  Downloading data for {len(tickers)} tickers (single batch)...")
    
    try:
        raw = yf.download(tickers, period=period, interval="1d",
                          group_by='ticker', progress=True, threads=True)
        
        if raw.empty:
            print("  WARNING: No data returned from yfinance")
            return _cache
        
        for ticker in tickers:
            try:
                if isinstance(raw.columns, pd.MultiIndex) and len(tickers) > 1:
                    df = raw[ticker].dropna(how='all')
                else:
                    df = raw.copy()
                
                # Flatten MultiIndex columns if needed
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                if not df.empty and len(df) >= 50:
                    _cache[ticker] = df
            except Exception:
                continue
    except Exception as e:
        print(f"  ERROR in batch download: {e}")
        print("  Falling back to individual downloads...")
        for ticker in tickers:
            try:
                df = yf.download(ticker, period=period, interval="1d", progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                if not df.empty and len(df) >= 50:
                    _cache[ticker] = df
            except Exception:
                continue
    
    print(f"  Successfully cached data for {len(_cache)}/{len(tickers)} tickers")
    return _cache

def get_stock_data(ticker):
    """Get cached data for a single ticker."""
    return _cache.get(ticker)

def clear_cache():
    """Clear all cached data."""
    global _cache
    _cache = {}
