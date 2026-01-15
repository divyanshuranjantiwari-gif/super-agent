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

def calculate_adx(high, low, close, period=14):
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.rolling(period).mean()
    
    plus_di = 100 * (plus_dm.ewm(alpha = 1/period).mean() / atr)
    minus_di = abs(100 * (minus_dm.ewm(alpha = 1/period).mean() / atr))
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    adx = ((dx.shift(1) * (period - 1)) + dx) / period
    adx_smooth = adx.ewm(alpha = 1/period).mean()
    return adx_smooth

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
            df['ADX'] = calculate_adx(df['High'], df['Low'], df['Close'], 14)
            
            # Helper for analysis
            def analyze_slice(df_slice):
                if df_slice is None or df_slice.empty: return None
                latest = df_slice.iloc[-1]
                price = latest['Close']
                ema_50 = latest['EMA_50']
                ema_200 = latest['EMA_200']
                rsi = latest['RSI']
                macd_line = latest['MACD']
                macd_signal = latest['MACD_SIGNAL']
                vol = latest['Volume']
                vol_avg = latest['VOL_SMA_20']
                atr = latest['ATR']
                adx = latest['ADX']
                
                if np.isnan(atr): atr = price * 0.02
                if np.isnan(rsi): rsi = 50
                
                # Scoring
                trend_score = 0
                if price > ema_50 > ema_200: trend_score = 1
                elif price < ema_50 < ema_200: trend_score = -1
                
                mom_score = 0
                if rsi > 55 and macd_line > macd_signal: mom_score = 1
                elif rsi < 45 and macd_line < macd_signal: mom_score = -1
                
                base_score = (trend_score * 0.5) + (mom_score * 0.3)
                
                vol_boost = 0
                if vol > vol_avg:
                    if base_score > 0: vol_boost = 0.2
                    elif base_score < 0: vol_boost = -0.2
                
                final_score = base_score + vol_boost
                final_score = max(min(final_score, 1.0), -1.0)
                
                # Rvol
                rvol = vol / vol_avg if vol_avg > 0 else 1.0
                
                return {
                    "score": final_score,
                    "trend_score": trend_score,
                    "mom_score": mom_score,
                    "vol_boost": vol_boost,
                    "price": price,
                    "atr": atr,
                    "adx": adx,
                    "rvol": rvol
                }

            # Generate History
            history = []
            for i in range(3):
                if len(df) < 50 + i: break
                
                slice_df = df if i == 0 else df[:-i]
                res = analyze_slice(slice_df)
                if not res: continue
                
                signal = "WAIT"
                if res['score'] >= 0.6: signal = "STRONG BUY"
                elif res['score'] <= -0.6: signal = "STRONG SELL"
                elif res['score'] > 0.2: signal = "BUY"
                elif res['score'] < -0.2: signal = "SELL"
                
                history.append({
                    "date": str(slice_df.index[-1]) if hasattr(slice_df.index, 'date') else f"T-{i}",
                    "signal": signal,
                    "confidence": abs(res['score'])
                })

            # Current Analysis (T)
            current_res = analyze_slice(df)
            if not current_res: return {"error": "Analysis failed"}
            
            final_score = current_res['score']
            price = current_res['price']
            atr = current_res['atr']
            adx = current_res['adx']
            rvol = current_res['rvol']
            
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
                "history": history,
                "details": {
                    "trend_score": current_res['trend_score'],
                    "mom_score": current_res['mom_score'],
                    "vol_boost": current_res['vol_boost'],
                    "adx": round(float(adx), 2) if not np.isnan(adx) else 0.0,
                    "rvol": round(float(rvol), 2)
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
