import pandas as pd
import ta
import numpy as np

def add_technical_indicators(df):
    """
    Adds technical indicators to the dataframe.
    Expects a DataFrame with 'Open', 'High', 'Low', 'Close', 'Volume'.
    """
    if df.empty:
        return df
    
    # Ensure columns are correct type
    df['Close'] = df['Close'].astype(float)
    df['High'] = df['High'].astype(float)
    df['Low'] = df['Low'].astype(float)
    df['Volume'] = df['Volume'].astype(float)
    
    # 1. RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # 2. MACD
    # ta.trend.MACD returns a class, we need to get the values
    macd = ta.trend.MACD(close=df['Close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD_12_26_9'] = macd.macd()
    df['MACDh_12_26_9'] = macd.macd_diff()
    df['MACDs_12_26_9'] = macd.macd_signal()
    
    # 3. Normalized ATR (Volatility)
    # ta.volatility.AverageTrueRange
    atr = ta.volatility.AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14)
    df['ATR'] = atr.average_true_range()
    df['ATR_Normalized'] = df['ATR'] / df['Close']
    
    # 4. Volume Profile / Volume Shock
    # We'll use Volume vs 20-day MA
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Shock'] = np.where(df['Volume'] > 1.5 * df['Vol_MA20'], 1, 0)
    
    # 5. RSI Divergence (Simplified)
    # Bullish Divergence: Price Lower Low, RSI Higher Low
    # We compare current low vs low 5 days ago (window)
    
    # Calculate local lows (rolling min)
    df['Price_Low_5'] = df['Low'].rolling(window=5).min()
    df['RSI_Low_5'] = df['RSI'].rolling(window=5).min()
    
    # Logic:
    # If Current Low == Price_Low_5 (we are at a local low)
    # AND Current Low < Previous Local Low (Lower Low)
    # AND Current RSI > Previous Local RSI (Higher Low)
    
    # This is hard to vectorize perfectly without complex logic.
    # We will use a simpler proxy for the AI model:
    # Just feed the raw RSI and Price trends.
    # But for the "Signal" layer, we can try to flag it.
    
    df['RSI_Divergence'] = 0
    
    # 6. Day of Week
    df['Day_of_Week'] = df.index.dayofweek
    
    # 7. EMA 20 for Trend
    df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
    
    return df

def add_relative_strength(df, benchmark_df):
    """
    Adds Relative Strength compared to a benchmark (e.g., Nifty 50).
    """
    if df.empty or benchmark_df.empty:
        return df
        
    # Align dates
    # We assume df and benchmark_df have the same index (Datetime)
    
    # Calculate returns
    df['Returns'] = df['Close'].pct_change()
    benchmark_df['Bnch_Returns'] = benchmark_df['Close'].pct_change()
    
    # Relative Strength: Stock Return - Benchmark Return
    # Or Ratio: Stock / Benchmark
    
    # We'll use the Ratio for the trend
    # We need to map benchmark close to df
    
    # Join benchmark close
    df = df.join(benchmark_df['Close'].rename('Benchmark_Close'), how='left')
    
    df['RS_Ratio'] = df['Close'] / df['Benchmark_Close']
    df['RS_Momentum'] = df['RS_Ratio'].pct_change(periods=20) # 1 month RS momentum
    
    return df

def calculate_vwap(df):
    """
    Calculates Volume Weighted Average Price (VWAP).
    """
    if 'Close' not in df.columns or 'Volume' not in df.columns:
        return df
        
    # Standard VWAP (Cumulative)
    # For daily data, we might want a rolling VWAP or just a cumulative one from start of data
    # Here we use a rolling 20-day VWAP as a proxy for monthly institutional average
    
    v = df['Volume']
    p = df['Close']
    
    # Cumulative VWAP from start (Standard definition for intraday, but for daily we use rolling)
    # df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
    
    # Rolling 20-Day VWAP (Institutional Monthly Average)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vp = typical_price * v
    
    df['VWAP'] = vp.rolling(window=20).sum() / v.rolling(window=20).sum()
    
    return df

def calculate_alpha_beta(df, benchmark_df, window=60):
    """
    Calculates Alpha and Beta relative to benchmark over a rolling window.
    """
    if df.empty or benchmark_df.empty:
        df['Alpha'] = 0
        df['Beta'] = 1
        return df
        
    # Align data
    # Assuming daily data
    
    # Calculate daily returns
    stock_ret = df['Close'].pct_change()
    
    # Benchmark returns (ensure aligned index)
    # We reindex benchmark to match stock df
    bench_ret = benchmark_df['Close'].pct_change().reindex(df.index).fillna(0)
    
    # Rolling Covariance and Variance
    covariance = stock_ret.rolling(window=window).cov(bench_ret)
    variance = bench_ret.rolling(window=window).var()
    
    # Beta = Cov / Var
    df['Beta'] = covariance / variance
    
    # Alpha = Stock_Ret - (Beta * Bench_Ret)  (Jensen's Alpha proxy for daily)
    # Or simpler: Average Excess Return
    # We'll use the CAPM-style Alpha summed over the window
    
    # Expected Return = Beta * Bench_Ret
    expected_ret = df['Beta'] * bench_ret
    excess_ret = stock_ret - expected_ret
    
    # Annualized Alpha (approx)
    df['Alpha'] = excess_ret.rolling(window=window).mean() * 252
    
    return df
