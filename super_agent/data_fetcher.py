"""
Super Agent 4.0 — Centralized Data Fetcher with Liquidity Safeguards
=====================================================================
Downloads OHLCV data for all NSE active stocks in chunked batches,
and applies liquidity and tradability safeguards to filter out
illiquid penny stocks and circuit-locked traps before deep analysis.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

_cache = {}

def fetch_all_data(
    tickers,
    period="1y",
    chunk_size=400,
    apply_liquidity_filter=True,
    min_price=20.0,
    min_volume=50000,
    min_turnover=5000000  # ₹50 Lakhs daily average turnover
):
    """
    Download OHLCV for all tickers in chunked batches.
    Filters out illiquid penny stocks and circuit-locked stocks.
    """
    global _cache
    _cache = {}  # Clear previous cache
    
    total_tickers = len(tickers)
    chunks = [tickers[i:i + chunk_size] for i in range(0, total_tickers, chunk_size)]
    
    print(f"  Downloading data for {total_tickers} tickers across {len(chunks)} batch chunks...")
    
    total_raw_downloaded = 0
    passed_liquidity = 0
    skipped_penny_or_illiquid = 0
    
    for c_idx, chunk in enumerate(chunks):
        print(f"  --> Batch {c_idx + 1}/{len(chunks)} ({len(chunk)} tickers)...", flush=True)
        try:
            raw = yf.download(
                chunk,
                period=period,
                interval="1d",
                group_by='ticker',
                progress=False,
                threads=True
            )
            
            if raw is None or raw.empty:
                print(f"      Warning: No data returned for batch {c_idx + 1}")
                continue
                
            for ticker in chunk:
                try:
                    if isinstance(raw.columns, pd.MultiIndex) and len(chunk) > 1:
                        if ticker not in raw.columns.levels[0]:
                            continue
                        df = raw[ticker].dropna(how='all')
                    else:
                        df = raw.copy()
                    
                    # Flatten MultiIndex columns if present
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    # Ensure numeric columns
                    for col in ['Close', 'High', 'Low', 'Open', 'Volume']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            
                    df = df.dropna(subset=['Close', 'Volume'])
                    
                    if len(df) < 60:
                        continue
                    
                    total_raw_downloaded += 1
                    
                    # --- OPTION 1: LIQUIDITY & TRADABILITY SAFEGUARDS ---
                    if apply_liquidity_filter:
                        latest_close = float(df['Close'].iloc[-1])
                        
                        # 1. Price Floor: Exclude penny stocks (< ₹20)
                        if latest_close < min_price:
                            skipped_penny_or_illiquid += 1
                            continue
                        
                        # 2. Volume Floor: Exclude illiquid stocks (< 50,000 shares 20-day avg)
                        vol_tail = df['Volume'].tail(20)
                        avg_vol_20 = float(vol_tail.mean())
                        if avg_vol_20 < min_volume:
                            skipped_penny_or_illiquid += 1
                            continue
                        
                        # 3. Turnover Floor: Exclude low-turnover stocks (< ₹50 Lakhs/day)
                        close_tail = df['Close'].tail(20)
                        avg_turnover_20 = float((close_tail * vol_tail).mean())
                        if avg_turnover_20 < min_turnover:
                            skipped_penny_or_illiquid += 1
                            continue
                    
                    _cache[ticker] = df
                    passed_liquidity += 1
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"      Error downloading batch {c_idx + 1}: {e}")
            # Fallback to individual ticker download for this chunk
            for ticker in chunk:
                try:
                    df = yf.download(ticker, period=period, interval="1d", progress=False)
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    for col in ['Close', 'High', 'Low', 'Open', 'Volume']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    df = df.dropna(subset=['Close', 'Volume'])
                    if len(df) >= 60:
                        latest_close = float(df['Close'].iloc[-1])
                        if not apply_liquidity_filter or (
                            latest_close >= min_price and 
                            float(df['Volume'].tail(20).mean()) >= min_volume and
                            float((df['Close'].tail(20) * df['Volume'].tail(20)).mean()) >= min_turnover
                        ):
                            _cache[ticker] = df
                            passed_liquidity += 1
                except Exception:
                    continue
    
    print(f"\n  [Data Fetch Summary]")
    print(f"  - Total tickers scanned: {total_tickers}")
    print(f"  - Active tickers with data: {total_raw_downloaded}")
    if apply_liquidity_filter:
        print(f"  - Excluded by liquidity filter (Penny / Low Volume / Turnover < ₹50L): {skipped_penny_or_illiquid}")
        print(f"  - Tradable swing candidates approved: {passed_liquidity}")
    else:
        print(f"  - Total approved: {passed_liquidity}")
    print()
    
    return _cache

def get_stock_data(ticker):
    """Get cached data for a single ticker."""
    return _cache.get(ticker)

def clear_cache():
    """Clear all cached data."""
    global _cache
    _cache = {}
