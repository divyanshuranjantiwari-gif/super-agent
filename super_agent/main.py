import os
import sys
import json
import subprocess
import concurrent.futures
from reporting import generate_dual_reports

import requests
import io
import pandas as pd

def get_nifty500():
    try:
        print("Fetching NIFTY 500 list from NSE...")
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            csv_content = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_content))
            symbols = df['Symbol'].tolist()
            return [s + ".NS" for s in symbols]
        else:
            print(f"Failed to fetch NIFTY 500: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching NIFTY 500: {e}")
        return []

WRAPPER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wrappers")

def run_wrapper(wrapper_name, ticker):
    wrapper_path = os.path.join(WRAPPER_DIR, wrapper_name)
    try:
        result = subprocess.run(
            [sys.executable, wrapper_path, "--ticker", ticker],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        # Find the last line which should be the JSON
        lines = output.split('\n')
        json_line = lines[-1]
        return json.loads(json_line)
    except subprocess.CalledProcessError as e:
        # Capture stderr for debugging
        return {"error": f"Subprocess Error: {e.stderr}", "details": {"raw_output": e.stdout}}
    except Exception as e:
        return {"error": str(e), "details": {"raw_output": ""}}

def analyze_stock(ticker):
    print(f"Analyzing {ticker}...", end="\r")
    
    # Run models in parallel for this stock
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_hfm = executor.submit(run_wrapper, "hfm_wrapper.py", ticker)
        future_stock_ai = executor.submit(run_wrapper, "stock_ai_wrapper.py", ticker)
        future_quant = executor.submit(run_wrapper, "quant_wrapper.py", ticker)
        future_apex = executor.submit(run_wrapper, "apex_wrapper.py", ticker)
        
        res_hfm = future_hfm.result()
        res_stock_ai = future_stock_ai.result()
        res_quant = future_quant.result()
        res_apex = future_apex.result()
    
    # Process Results
    results = {
        "Hedge Fund Manager": res_hfm,
        "Most Advance stock_AI": res_stock_ai,
        "Quantitative Development": res_quant,
        "Apex Logic": res_apex
    }
    
    # --- AGGREGATION LOGIC ---
    
    # --- AGGREGATION LOGIC (Super Agent 3.0) ---
    
    def normalize_signal(signal):
        s = signal.upper()
        if "STRONG BUY" in s or "STRONG_BUY" in s: return 1.0
        if "STRONG SELL" in s or "STRONG_SELL" in s: return -1.0
        if "BUY" in s: return 1.0
        if "SELL" in s: return -1.0
        return 0.0
        
    # 1. Global Metrics (ADX, RVOL)
    adx_vals = []
    rvol_vals = []
    for res in results.values():
        if "error" in res: continue
        d = res.get('details', {})
        if 'adx' in d and d['adx'] > 0: adx_vals.append(d['adx'])
        if 'rvol' in d and d['rvol'] > 0: rvol_vals.append(d['rvol'])
    
    avg_adx = sum(adx_vals) / len(adx_vals) if adx_vals else 0
    avg_rvol = sum(rvol_vals) / len(rvol_vals) if rvol_vals else 0
    
    def calculate_persistence_score(res, mode_key):
        if "error" in res: return 0
        
        # New History-Based Logic
        history = res.get('history', [])
        
        # If no history (fallback), use current signal with penalty
        if not history:
            current = res.get(mode_key, {})
            sig = current.get('signal', 'WAIT')
            conf = current.get('confidence', 0)
            return normalize_signal(sig) * conf * 0.5
            
        # Weights: T=0.5, T-1=0.3, T-2=0.2
        weights = [0.5, 0.3, 0.2]
        score = 0
        
        # History is ordered [T, T-1, T-2] (as appended in loop 0..2)
        # Wait, wrapper loop was: for i in 0..2: history.append(T-i)
        # So history[0] is T, history[1] is T-1...
        # Let's verify wrapper logic. 
        # "history.append({date: T-i...})"
        # Yes, index 0 is T.
        
        # However, for MODE specific signals (Swing vs Intraday), wrappers might calculate generic signal history?
        # Wrappers return generic 'signal' in history. This maps to Swing usually.
        # Intraday might differ, but for persistence we track the core Trend.
        
        for i, h_item in enumerate(history):
            if i >= 3: break
            s_val = normalize_signal(h_item.get('signal', 'WAIT'))
            c_val = h_item.get('confidence', 0)
            score += (s_val * c_val * weights[i])
            
        return score

    def calculate_super_score(results, mode_key):
        total_score = 0
        valid_models = 0
        
        for model_name, res in results.items():
            if "error" in res: continue
            
            # INCLUDE Apex in 3.0
            # previous: if model_name == "Apex Logic": continue 
            
            p_score = calculate_persistence_score(res, mode_key)
            total_score += p_score
            valid_models += 1
            
        final_score = total_score / valid_models if valid_models > 0 else 0
        
        # --- FILTERS (The "Iron-Clad" Logic) ---
        
        # 1. ADX Filter (Trend Strength)
        # If ADX < 25, Market is Choppy. Kill "Trends".
        # Only applies to Swing. Intraday might scalp chop.
        if mode_key == 'swing' and avg_adx < 25:
             # Veto Buy Signals in Chop
             if final_score > 0: final_score = 0
             
        # 2. RVOL Filter REMOVED (User Request)
        # We rely on ADX and Price Action Persistence only.
        pass
                
        return final_score

    super_score_swing = calculate_super_score(results, 'swing')
    super_score_intraday = calculate_super_score(results, 'intraday')
    
    # Determine Final Signals
    def get_final_signal(score):
        if score >= 0.5: return "STRONG BUY" # High Persistence
        if score > 0.15: return "BUY"
        if score <= -0.5: return "STRONG SELL"
        if score < -0.15: return "SELL"
        return "WAIT"
        
    final_signal_swing = get_final_signal(super_score_swing)
    final_signal_intraday = get_final_signal(super_score_intraday)
    
    # Extract Trade Params (Prioritize Quant > StockAI > HFM)
    def extract_params(model_results, mode_key, final_sig):
        # Default
        params = {"entry": 0, "target": 0, "sl": 0}
        
        # Priority list
        priority = ["Apex Logic", "Quantitative Development", "Most Advance stock_AI", "Hedge Fund Manager"]
        
        # Try to find a model that agrees with the final signal
        for name in priority:
            res = model_results.get(name, {})
            if "error" in res: continue
            
            mode_data = res.get(mode_key, {})
            if mode_data.get('signal') == final_sig and final_sig != "WAIT":
                params['entry'] = mode_data.get('entry', 0)
                params['target'] = mode_data.get('target', 0)
                params['sl'] = mode_data.get('sl', 0)
                return params
            # Loose match (BUY matches STRONG BUY)
            if final_sig in mode_data.get('signal', '') and final_sig != "WAIT":
                 params['entry'] = mode_data.get('entry', 0)
                 params['target'] = mode_data.get('target', 0)
                 params['sl'] = mode_data.get('sl', 0)
                 return params
        
        # Fallback: Just take from Quant or Apex if available
        res = model_results.get("Apex Logic", {})
        if "error" not in res:
            mode_data = res.get(mode_key, {})
            params['entry'] = mode_data.get('entry', 0)
            params['target'] = mode_data.get('target', 0)
            params['sl'] = mode_data.get('sl', 0)
            
        return params

    params_swing = extract_params(results, 'swing', final_signal_swing)
    params_intraday = extract_params(results, 'intraday', final_signal_intraday)
    
    # Construct Result Objects
    swing_res = {
        "ticker": ticker,
        "final_signal": final_signal_swing,
        "super_score": super_score_swing,
        "entry": params_swing['entry'],
        "target": params_swing['target'],
        "sl": params_swing['sl'],
        "models": {k: v.get('swing', {}) for k, v in results.items() if "error" not in v}
    }
    
    intraday_res = {
        "ticker": ticker,
        "final_signal": final_signal_intraday,
        "super_score": super_score_intraday,
        "entry": params_intraday['entry'],
        "target": params_intraday['target'],
        "sl": params_intraday['sl'],
        "models": {k: v.get('intraday', {}) for k, v in results.items() if "error" not in v}
    }
    
    # Add error info if any
    for k, v in results.items():
        if "error" in v:
            error_msg = v['error']
            # Truncate to keep UI sane but show key info
            short_err = f"ERR: {error_msg[:100]}" 
            swing_res['models'][k] = {"signal": short_err, "confidence": 0}
            intraday_res['models'][k] = {"signal": short_err, "confidence": 0}

    return swing_res, intraday_res

def main():
    print("Initializing Super Agent...")
    print(f"Wrapper Directory: {WRAPPER_DIR}")
    
    # Limit for testing
    # tickers = ["RELIANCE.NS", "TCS.NS"] 
    
    # Fetch NIFTY 500
    tickers = get_nifty500()
    
    if not tickers:
        print("Fallback to hardcoded list (Critical Error)")
        tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"] # Minimal fallback
    
    print(f"Starting analysis for {len(tickers)} stocks...")
    
    swing_results = []
    intraday_results = []
    
    # Sequential processing to avoid overloading system/API limits
    for i, ticker in enumerate(tickers):
        print(f"[{i+1}/{len(tickers)}] ", end="")
        try:
            s_res, i_res = analyze_stock(ticker)
            swing_results.append(s_res)
            intraday_results.append(i_res)
        except Exception as e:
            print(f"Failed to analyze {ticker}: {e}")
            
    print("\nAnalysis Complete. Generating Reports...")
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    swing_path, intraday_path = generate_dual_reports(swing_results, intraday_results, output_dir)
    
    print(f"Swing Report: {swing_path}")
    print(f"Intraday Report: {intraday_path}")

if __name__ == "__main__":
    main()
