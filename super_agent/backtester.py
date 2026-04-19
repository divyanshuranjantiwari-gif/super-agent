"""
Super Agent 4.0 — Backtesting Framework
========================================
Tests each model's signals against actual forward returns.

Logic:
1. Fetch 1 year of daily OHLCV for a diversified sample of 30 stocks
2. Compute all indicators across the entire time series
3. For each day in the last 60 trading days, simulate what each model would've signaled
4. Check if the stock moved +3% within the next 5 trading days (swing target)
5. Output accuracy metrics per model and for the ensemble
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import ta
import yfinance as yf
from datetime import datetime

# --- INDICATOR CALCULATIONS (Mirrors what wrappers compute) ---

def compute_all_indicators(df):
    """Compute all indicators used by all 4 models on a full DataFrame."""
    if df.empty or len(df) < 200:
        return None
    
    df = df.copy()
    
    # Flatten MultiIndex if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Ensure correct types
    for col in ['Close', 'High', 'Low', 'Open', 'Volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # --- TREND ---
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
    df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # --- MOMENTUM ---
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    macd_ind = ta.trend.MACD(close=df['Close'])
    df['MACD'] = macd_ind.macd()
    df['MACD_SIGNAL'] = macd_ind.macd_signal()
    df['MACD_DIFF'] = macd_ind.macd_diff()
    
    # --- VOLATILITY ---
    atr_ind = ta.volatility.AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14)
    df['ATR'] = atr_ind.average_true_range()
    
    bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['BB_HIGH'] = bb.bollinger_hband()
    df['BB_LOW'] = bb.bollinger_lband()
    df['BB_MID'] = bb.bollinger_mavg()
    
    # --- TREND STRENGTH ---
    adx_ind = ta.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14)
    df['ADX'] = adx_ind.adx()
    
    # --- VOLUME ---
    df['VOL_AVG_20'] = df['Volume'].rolling(window=20).mean()
    df['RVOL'] = df['Volume'] / df['VOL_AVG_20'].replace(0, 1)
    
    # --- VWAP (Rolling 20-day) ---
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vp = typical_price * df['Volume']
    df['VWAP'] = vp.rolling(window=20).sum() / df['Volume'].rolling(window=20).sum()
    
    # --- FORWARD RETURNS (for labeling) ---
    df['Fwd_1D'] = df['Close'].shift(-1) / df['Close'] - 1
    df['Fwd_3D'] = df['Close'].shift(-3) / df['Close'] - 1
    df['Fwd_5D'] = df['Close'].shift(-5) / df['Close'] - 1
    df['Fwd_5D_Max'] = df['High'].rolling(window=5).max().shift(-5) / df['Close'] - 1
    
    return df


# --- MODEL SIGNAL SIMULATORS ---
# Each function takes a row of computed indicators and returns a signal + confidence

def simulate_apex(row):
    """Simulates Apex Logic model signal for a given day."""
    price = row['Close']
    ema_50 = row['EMA_50']
    ema_200 = row['EMA_200']
    rsi = row['RSI']
    macd = row['MACD']
    macd_sig = row['MACD_SIGNAL']
    vol = row['Volume']
    vol_avg = row['VOL_AVG_20']
    
    if pd.isna(ema_200) or pd.isna(rsi): return 'WAIT', 0
    
    trend_score = 0
    if price > ema_50 > ema_200: trend_score = 1
    elif price < ema_50 < ema_200: trend_score = -1
    
    mom_score = 0
    if rsi > 55 and macd > macd_sig: mom_score = 1
    elif rsi < 45 and macd < macd_sig: mom_score = -1
    
    base = (trend_score * 0.5) + (mom_score * 0.3)
    
    vol_boost = 0
    if vol > vol_avg:
        if base > 0: vol_boost = 0.2
        elif base < 0: vol_boost = -0.2
    
    score = base + vol_boost
    score = max(min(score, 1.0), -1.0)
    
    if score >= 0.6: return 'STRONG BUY', abs(score)
    if score > 0.2: return 'BUY', abs(score)
    if score <= -0.6: return 'STRONG SELL', abs(score)
    if score < -0.2: return 'SELL', abs(score)
    return 'WAIT', abs(score)


def simulate_hfm(row):
    """Simulates HFM model signal for a given day."""
    price = row['Close']
    vwap = row.get('VWAP', price)
    ema_20 = row.get('EMA_20', price)
    
    if pd.isna(vwap) or pd.isna(ema_20): return 'WAIT', 0
    
    # Simplified: no Alpha/Beta (requires benchmark), use VWAP + EMA + trend
    institutional_buying = price > vwap
    trend_up = price > ema_20
    above_sma_50 = price > row['SMA_50'] if not pd.isna(row.get('SMA_50')) else False
    
    if institutional_buying and trend_up and above_sma_50:
        vwap_dist = abs(price - vwap) / vwap * 100
        conf = min(50 + vwap_dist * 5 + 10 + 10, 100) / 100
        if conf > 0.8: return 'STRONG BUY', conf
        return 'BUY', conf
    elif not institutional_buying and not trend_up and not above_sma_50:
        conf = 0.7
        return 'SELL', conf
    
    return 'WAIT', 0.5


def simulate_stockai(row):
    """Simulates StockAI model signal for a given day."""
    rsi = row['RSI']
    macd_diff = row['MACD_DIFF']
    adx = row['ADX']
    rvol = row['RVOL']
    
    if pd.isna(rsi) or pd.isna(row.get('SMA_200')): return 'WAIT', 0
    
    score = 0
    
    # Trend (40 pts)
    if row['Close'] > row['SMA_200']: score += 20
    if row['Close'] > row['SMA_50']: score += 10
    if row['Close'] > row['EMA_20']: score += 10
    
    # Momentum (30 pts)
    if 40 <= rsi <= 65: score += 15
    elif 30 < rsi < 40: score += 10
    elif rsi <= 30: score += 5
    elif 65 < rsi <= 75: score += 8
    
    if not pd.isna(macd_diff) and macd_diff > 0: score += 10
    
    # ADX (15 pts)
    if not pd.isna(adx):
        if adx > 30: score += 15
        elif adx > 25: score += 10
        elif adx > 20: score += 5
    
    # Volume (15 pts)
    if not pd.isna(rvol):
        if rvol > 2.0: score += 15
        elif rvol > 1.5: score += 10
        elif rvol > 1.0: score += 5
    
    score = max(0, min(100, score))
    conf = score / 100
    
    if conf > 0.75: return 'BUY', conf
    if conf < 0.30: return 'SELL', conf
    return 'WAIT', conf


def simulate_quant(row):
    """Simulates Quant model signal for a given day."""
    score = 0
    
    if pd.isna(row.get('SMA_200')): return 'WAIT', 0
    
    # Technical (0-10, worth 50%)
    t_score = 0
    if row['SMA_50'] > row['SMA_200']: t_score += 2.5
    rsi = row['RSI']
    if 30 < rsi < 70: t_score += 2.5
    if row['Close'] > row['BB_MID']: t_score += 2.5
    if row['MACD_DIFF'] > 0: t_score += 2.5
    
    # Fundamental stub (0-10, worth 30%) — use 5 as neutral placeholder
    f_score = 5.0
    
    # Sentiment stub (0-10, worth 20%) — use 5 as neutral
    s_score = 5.0
    
    final = (t_score * 0.5) + (f_score * 0.3) + (s_score * 0.2)
    
    if final > 7: return 'BUY', final / 10
    if final < 3: return 'SELL', (10 - final) / 10
    return 'WAIT', final / 10


# --- ENSEMBLE ---

def simulate_ensemble(row):
    """Run all 4 models and compute Super Score."""
    signals = {
        'Apex': simulate_apex(row),
        'HFM': simulate_hfm(row),
        'StockAI': simulate_stockai(row),
        'Quant': simulate_quant(row)
    }
    
    def norm(sig):
        s = sig.upper()
        if 'STRONG BUY' in s: return 1.0
        if 'STRONG SELL' in s: return -1.0
        if 'BUY' in s: return 0.7
        if 'SELL' in s: return -0.7
        return 0.0
    
    def direction(sig):
        s = sig.upper()
        if 'BUY' in s: return 1
        if 'SELL' in s: return -1
        return 0
    
    total = 0
    count = 0
    directions = []
    
    for name, (sig, conf) in signals.items():
        val = norm(sig) * conf
        total += val
        count += 1
        d = direction(sig)
        if d != 0: directions.append(d)
    
    super_score = total / count if count > 0 else 0
    
    # Consensus gate
    has_buy = any(d > 0 for d in directions)
    has_sell = any(d < 0 for d in directions)
    if has_buy and has_sell:
        if abs(super_score) < 0.6:
            super_score *= 0.3
    
    # ADX filter
    adx = row.get('ADX', 0)
    if not pd.isna(adx):
        if adx < 20 and super_score > 0:
            super_score = 0
        elif adx < 25 and super_score > 0:
            super_score *= 0.5
    
    # Supreme check
    is_supreme = False
    if super_score >= 0.6 and not pd.isna(adx) and adx > 25:
        all_buy = all(direction(signals[m][0]) == 1 for m in signals)
        if all_buy:
            is_supreme = True
    
    if super_score >= 0.5: final_sig = 'STRONG BUY'
    elif super_score > 0.15: final_sig = 'BUY'
    elif super_score <= -0.5: final_sig = 'STRONG SELL'
    elif super_score < -0.15: final_sig = 'SELL'
    else: final_sig = 'WAIT'
    
    return final_sig, super_score, is_supreme, signals


# --- MAIN BACKTEST ENGINE ---

def run_backtest(tickers=None, lookback_days=60, target_pct=0.03, max_holding=5):
    """
    Run backtest across stocks and time.
    
    Args:
        tickers: list of ticker symbols
        lookback_days: number of trading days to test
        target_pct: what % gain counts as a "win" (default 3%)
        max_holding: holding period in days (default 5)
    """
    
    if tickers is None:
        # Diversified sample across sectors
        tickers = [
            # Large Cap
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "HINDUNILVR.NS", "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "BAJFINANCE.NS",
            # Mid Cap
            "COALINDIA.NS", "TATASTEEL.NS", "ADANIENT.NS", "M&M.NS", "SUNPHARMA.NS",
            "MARUTI.NS", "TITAN.NS", "WIPRO.NS", "HCLTECH.NS", "POWERGRID.NS",
            # Volatile / Sectoral
            "TATAMOTORS.NS", "ONGC.NS", "NTPC.NS", "BPCL.NS", "JSWSTEEL.NS",
            "AXISBANK.NS", "KOTAKBANK.NS", "LT.NS", "ULTRACEMCO.NS", "DRREDDY.NS",
        ]
    
    print(f"\n{'='*70}")
    print(f"  SUPER AGENT 4.0 — BACKTESTER")
    print(f"  Stocks: {len(tickers)} | Lookback: {lookback_days} days")
    print(f"  Target: +{target_pct*100:.0f}% in {max_holding} days")
    print(f"{'='*70}\n")
    
    # Per-model results
    model_results = {
        'Apex': {'correct': 0, 'wrong': 0, 'wait': 0},
        'HFM': {'correct': 0, 'wrong': 0, 'wait': 0},
        'StockAI': {'correct': 0, 'wrong': 0, 'wait': 0},
        'Quant': {'correct': 0, 'wrong': 0, 'wait': 0},
        'Ensemble': {'correct': 0, 'wrong': 0, 'wait': 0},
        'Supreme': {'correct': 0, 'wrong': 0, 'total': 0},
    }
    
    all_trades = []
    
    for i, ticker in enumerate(tickers):
        print(f"  [{i+1}/{len(tickers)}] {ticker}...", end=" ")
        
        try:
            df = yf.download(ticker, period="2y", interval="1d", progress=False)
            df = compute_all_indicators(df)
            
            if df is None:
                print("SKIP (insufficient data)")
                continue
            
            # Backtest window: last `lookback_days` rows (excluding last 5 for forward returns)
            test_start = max(200, len(df) - lookback_days - max_holding)
            test_end = len(df) - max_holding  # Need forward data
            
            if test_start >= test_end:
                print("SKIP (not enough test window)")
                continue
            
            stock_correct = 0
            stock_total = 0
            
            for idx in range(test_start, test_end):
                row = df.iloc[idx]
                
                # Skip if forward return is NaN
                fwd_5d_max = row.get('Fwd_5D_Max')
                fwd_5d = row.get('Fwd_5D')
                if pd.isna(fwd_5d) or pd.isna(fwd_5d_max):
                    continue
                
                # Did the stock hit target in the next 5 days?
                # We use max high in next 5 days vs close
                hit_target = fwd_5d_max >= target_pct
                # Did it go down instead?
                went_down = fwd_5d < -target_pct
                
                # Run ensemble
                final_sig, super_score, is_supreme, model_signals = simulate_ensemble(row)
                
                # Evaluate each model
                for model_name, (sig, conf) in model_signals.items():
                    d = 0
                    if 'BUY' in sig.upper(): d = 1
                    elif 'SELL' in sig.upper(): d = -1
                    
                    if d == 1:
                        if hit_target:
                            model_results[model_name]['correct'] += 1
                        else:
                            model_results[model_name]['wrong'] += 1
                    elif d == -1:
                        if went_down:
                            model_results[model_name]['correct'] += 1
                        else:
                            model_results[model_name]['wrong'] += 1
                    else:
                        model_results[model_name]['wait'] += 1
                
                # Evaluate ensemble
                d_ens = 0
                if 'BUY' in final_sig: d_ens = 1
                elif 'SELL' in final_sig: d_ens = -1
                
                if d_ens == 1:
                    if hit_target:
                        model_results['Ensemble']['correct'] += 1
                        stock_correct += 1
                    else:
                        model_results['Ensemble']['wrong'] += 1
                    stock_total += 1
                elif d_ens == -1:
                    if went_down:
                        model_results['Ensemble']['correct'] += 1
                        stock_correct += 1
                    else:
                        model_results['Ensemble']['wrong'] += 1
                    stock_total += 1
                else:
                    model_results['Ensemble']['wait'] += 1
                
                # Supreme tier
                if is_supreme:
                    model_results['Supreme']['total'] += 1
                    if hit_target:
                        model_results['Supreme']['correct'] += 1
                    else:
                        model_results['Supreme']['wrong'] += 1
                
                # Store trade data for meta-model training
                all_trades.append({
                    'ticker': ticker,
                    'date': str(df.index[idx]),
                    'close': row['Close'],
                    'rsi': row['RSI'],
                    'adx': row['ADX'],
                    'rvol': row['RVOL'],
                    'macd_diff': row['MACD_DIFF'],
                    'above_sma50': 1 if row['Close'] > row['SMA_50'] else 0,
                    'above_sma200': 1 if row['Close'] > row['SMA_200'] else 0,
                    'above_ema20': 1 if row['Close'] > row['EMA_20'] else 0,
                    'above_vwap': 1 if row['Close'] > row['VWAP'] else 0,
                    'apex_signal': model_signals['Apex'][0],
                    'apex_conf': model_signals['Apex'][1],
                    'hfm_signal': model_signals['HFM'][0],
                    'hfm_conf': model_signals['HFM'][1],
                    'stockai_signal': model_signals['StockAI'][0],
                    'stockai_conf': model_signals['StockAI'][1],
                    'quant_signal': model_signals['Quant'][0],
                    'quant_conf': model_signals['Quant'][1],
                    'ensemble_signal': final_sig,
                    'super_score': super_score,
                    'is_supreme': is_supreme,
                    'fwd_5d_return': fwd_5d,
                    'fwd_5d_max_return': fwd_5d_max,
                    'hit_target': hit_target,
                    'went_down': went_down,
                })
            
            acc = f"{stock_correct}/{stock_total} ({stock_correct/stock_total*100:.0f}%)" if stock_total > 0 else "No trades"
            print(f"OK — Ensemble: {acc}")
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    # --- RESULTS ---
    print(f"\n{'='*70}")
    print(f"  BACKTEST RESULTS")
    print(f"{'='*70}\n")
    
    for name in ['Apex', 'HFM', 'StockAI', 'Quant', 'Ensemble']:
        r = model_results[name]
        total_trades = r['correct'] + r['wrong']
        if total_trades > 0:
            accuracy = r['correct'] / total_trades * 100
            print(f"  {name:25s}  Accuracy: {accuracy:5.1f}%  ({r['correct']}/{total_trades} trades, {r['wait']} skipped)")
        else:
            print(f"  {name:25s}  No trades generated")
    
    # Supreme
    sr = model_results['Supreme']
    if sr['total'] > 0:
        s_acc = sr['correct'] / sr['total'] * 100
        print(f"\n  {'[SUPREME TIER]':25s}  Accuracy: {s_acc:5.1f}%  ({sr['correct']}/{sr['total']} trades)")
    else:
        print(f"\n  {'[SUPREME TIER]':25s}  No Supreme signals generated (expected — very strict)")
    
    print(f"\n{'='*70}\n")
    
    # Save trade data for meta-model training
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backtest_trades.csv')
        trades_df.to_csv(output_path, index=False)
        print(f"  Trade data saved to: {output_path}")
        print(f"  Total data points: {len(trades_df)}")
        print(f"  (This CSV feeds into the Meta-ML model)\n")
    
    return model_results, all_trades


if __name__ == "__main__":
    results, trades = run_backtest()
