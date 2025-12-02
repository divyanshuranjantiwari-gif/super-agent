import os
import sys
import json
import subprocess
import concurrent.futures
from reporting import generate_dual_reports

# NIFTY 50 Universe
NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS",
    "LICI.NS", "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "HCLTECH.NS",
    "MARUTI.NS", "TITAN.NS", "BAJFINANCE.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS",
    "TATAMOTORS.NS", "NTPC.NS", "POWERGRID.NS", "M&M.NS", "ONGC.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "BAJAJFINSV.NS", "COALINDIA.NS", "JSWSTEEL.NS",
    "TATASTEEL.NS", "HINDALCO.NS", "GRASIM.NS", "CIPLA.NS", "TECHM.NS",
    "WIPRO.NS", "DRREDDY.NS", "SBILIFE.NS", "BRITANNIA.NS", "INDUSINDBK.NS",
    "TATACONSUM.NS", "DIVISLAB.NS", "EICHERMOT.NS", "NESTLEIND.NS", "BPCL.NS",
    "HEROMOTOCO.NS", "APOLLOHOSP.NS", "UPL.NS"
]

SENSEX_30 = [
    "RELIANCE.BO", "TCS.BO", "HDFCBANK.BO", "INFY.BO", "ICICIBANK.BO",
    "HINDUNILVR.BO", "SBIN.BO", "BHARTIARTL.BO", "ITC.BO", "KOTAKBANK.BO",
    "LT.BO", "AXISBANK.BO", "ASIANPAINT.BO", "HCLTECH.BO", "MARUTI.BO",
    "TITAN.BO", "BAJFINANCE.BO", "SUNPHARMA.BO", "ULTRACEMCO.BO", "TATAMOTORS.BO",
    "NTPC.BO", "POWERGRID.BO", "M&M.BO", "TATASTEEL.BO", "JSWSTEEL.BO",
    "BAJAJFINSV.BO", "INDUSINDBK.BO", "TECHM.BO", "WIPRO.BO", "NESTLEIND.BO"
]

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
    except Exception as e:
        return {"error": str(e), "details": {"raw_output": result.stdout if 'result' in locals() else ""}}

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
    
    def normalize_signal(signal):
        if "STRONG_BUY" in signal: return 1.0
        if "STRONG_SELL" in signal: return -1.0
        if "BUY" in signal: return 1.0
        if "SELL" in signal: return -1.0
        return 0
        
    def calculate_super_score(model_results, mode_key):
        total_score = 0
        valid_models = 0
        
        for model_name, res in model_results.items():
            if "error" in res: continue
            if model_name == "Apex Logic": continue # Exclude Apex from Super Score
            
            # Extract specific mode data (swing/intraday)
            mode_data = res.get(mode_key, {})
            signal = mode_data.get('signal', 'WAIT')
            confidence = mode_data.get('confidence', 0)
            
            norm_signal = normalize_signal(signal)
            total_score += (norm_signal * confidence)
            valid_models += 1
            
        if valid_models == 0: return 0
        return total_score / valid_models
        
    super_score_swing = calculate_super_score(results, 'swing')
    super_score_intraday = calculate_super_score(results, 'intraday')
    
    # Determine Final Signals
    def get_final_signal(score):
        if score > 0.2: return "BUY"
        if score < -0.2: return "SELL"
        return "WAIT"
        
    final_signal_swing = get_final_signal(super_score_swing)
    final_signal_intraday = get_final_signal(super_score_intraday)
    
    # Extract Trade Params (Prioritize Quant > StockAI > HFM)
    def extract_params(model_results, mode_key, final_sig):
        # Default
        params = {"entry": 0, "target": 0, "sl": 0}
        
        # Priority list
        priority = ["Quantitative Development", "Most Advance stock_AI", "Hedge Fund Manager"]
        
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
        
        # Fallback: Just take from Quant if available
        res = model_results.get("Quantitative Development", {})
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
    # tickers = NIFTY_50[:3] 
    # Combine Universes (Set to remove duplicates if any, though suffixes differ)
    tickers = list(set(NIFTY_50 + SENSEX_30))
    # tickers = ["RELIANCE.NS", "TCS.BO", "EICHERMOT.NS"] # Mixed subset for testing
    
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
