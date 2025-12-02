import sys
import os
import json
import argparse
import contextlib
import yfinance as yf
import pandas as pd
import numpy as np

@contextlib.contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

# --- INDICATOR HELPERS ---
def calculate_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = calculate_ema(series, fast)
    exp2 = calculate_ema(series, slow)
    macd = exp1 - exp2
    signal_line = calculate_ema(macd, signal)
    return macd, signal_line

def calculate_atr(high, low, close, period=14):
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def run_analysis(ticker):
    try:
        with suppress_stdout():
            # Fetch Data (1 Year for robust EMA 200)
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            
            if df is None or df.empty or len(df) < 200:
                return {"error": "Insufficient data"}
            
            # Ensure columns are flat (yfinance update)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            # --- INDICATORS ---
            # Trend
            df['EMA_50'] = calculate_ema(df['Close'], 50)
            df['EMA_200'] = calculate_ema(df['Close'], 200)
            
            # Momentum
            df['RSI'] = calculate_rsi(df['Close'], 14)
            df['MACD'], df['MACD_SIGNAL'] = calculate_macd(df['Close'])
            
            # Volume
            df['VOL_SMA_20'] = df['Volume'].rolling(window=20).mean()
            df['ATR'] = calculate_atr(df['High'], df['Low'], df['Close'], 14)
            
            # Get Latest Data
            latest = df.iloc[-1]
            price = latest['Close']
            ema_50 = latest['EMA_50']
            ema_200 = latest['EMA_200']
            rsi = latest['RSI']
            macd_line = latest['MACD']
            macd_signal = latest['MACD_SIGNAL']
            vol = latest['Volume']
            vol_avg = latest['VOL_SMA_20']
            atr = latest['ATR']
            
            # Handle NaN (e.g. if not enough data for indicators)
            if np.isnan(atr): atr = price * 0.02
            if np.isnan(rsi): rsi = 50
            
            # --- SCORING LOGIC ---
            
            # 1. Trend (40%)
            trend_score = 0
            if price > ema_50 > ema_200:
                trend_score = 1 # Bullish
            elif price < ema_50 < ema_200:
                trend_score = -1 # Bearish
                
            # 2. Momentum (30%)
            mom_score = 0
            if rsi > 55 and macd_line > macd_signal:
                mom_score = 1 # Bullish
            elif rsi < 45 and macd_line < macd_signal:
                mom_score = -1 # Bearish
                
            # 3. Volume Confirmation (30% Impact)
            base_score = (trend_score * 0.5) + (mom_score * 0.3)
            
            vol_boost = 0
            if vol > vol_avg:
                if base_score > 0: vol_boost = 0.2
                elif base_score < 0: vol_boost = -0.2
                
            final_score = base_score + vol_boost
            
            # Cap score
            final_score = max(min(final_score, 1.0), -1.0)
            
            # --- SIGNAL GENERATION ---
            signal = "WAIT"
            if final_score >= 0.6: signal = "STRONG BUY"
            elif final_score <= -0.6: signal = "STRONG SELL"
            elif final_score > 0.2: signal = "BUY"
            elif final_score < -0.2: signal = "SELL"
            
            # --- TRADE PARAMS ---
            
            # Swing
            swing_sl = 0
            swing_target = 0
            if "BUY" in signal:
                swing_sl = price - (2.0 * atr) 
                swing_target = price + (4.0 * atr) 
            elif "SELL" in signal:
                swing_sl = price + (2.0 * atr)
                swing_target = price - (4.0 * atr)
                
            swing_data = {
                "signal": signal,
                "confidence": abs(final_score),
                "entry": price,
                "target": swing_target,
                "sl": swing_sl
            }
            
            # Intraday
            intraday_sl = 0
            intraday_target = 0
            if "BUY" in signal:
                intraday_sl = price - (0.8 * atr)
                intraday_target = price + (1.5 * atr)
            elif "SELL" in signal:
                intraday_sl = price + (0.8 * atr)
                intraday_target = price - (1.5 * atr)
                
            intraday_data = {
                "signal": signal,
                "confidence": abs(final_score),
                "entry": price,
                "target": intraday_target,
                "sl": intraday_sl
            }
            
            return {
                "model_name": "Apex Logic",
                "swing": swing_data,
                "intraday": intraday_data,
                "details": {
                    "trend_score": trend_score,
                    "mom_score": mom_score,
                    "vol_boost": vol_boost
                }
            }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    args = parser.parse_args()
    
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, 'item'):
                return obj.item()
            if hasattr(obj, 'tolist'):
                return obj.tolist()
            return super().default(obj)

    result = run_analysis(args.ticker)
    print(json.dumps(result, cls=NumpyEncoder))
