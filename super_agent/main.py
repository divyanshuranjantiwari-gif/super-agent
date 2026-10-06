import os
import sys
import json
from data_fetcher import fetch_all_data, get_stock_data
from wrappers import apex_wrapper, hfm_wrapper, stock_ai_wrapper, quant_wrapper
import concurrent.futures
from reporting import generate_dual_reports
from regime_detector import detect_market_regime
from sector_mapper import get_sector_trend
from risk_manager import calculate_position_size

import requests
import io
import pandas as pd

# Load Meta-ML model (trained on backtest data)
try:
    from meta_model import load_meta_model, predict_with_meta
    META_MODEL = load_meta_model()
    if META_MODEL:
        print(f"[Meta-ML] Loaded model (accuracy: {META_MODEL['metrics']['accuracy']*100:.1f}%)")
    else:
        print("[Meta-ML] No trained model found — running without ML filter")
except Exception as e:
    META_MODEL = None
    print(f"[Meta-ML] Could not load: {e}")

print("Detecting Macro Market Regime...")
GLOBAL_REGIME = detect_market_regime()
print(f"Regime: {GLOBAL_REGIME['regime']} (NIFTY: {GLOBAL_REGIME['nifty_trend']}, VIX: {GLOBAL_REGIME['vix_level']:.2f})")

def get_nifty500():
    try:
        print("Fetching NIFTY 500 list from NSE...")
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
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

def run_wrapper_direct(wrapper_module, ticker, stock_data=None):
    """Call wrapper analysis function directly (no subprocess)."""
    try:
        result = wrapper_module.analyze(ticker, stock_data)
        return result if result else {"error": "No result returned"}
    except Exception as e:
        return {"error": str(e), "details": {}}

def analyze_stock(ticker, stock_data=None):
    print(f"Analyzing {ticker}...", end="\r")
    
    # Run models in parallel for this stock (using direct imports, not subprocess)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_hfm = executor.submit(run_wrapper_direct, hfm_wrapper, ticker, stock_data)
        future_stock_ai = executor.submit(run_wrapper_direct, stock_ai_wrapper, ticker, stock_data)
        future_quant = executor.submit(run_wrapper_direct, quant_wrapper, ticker, stock_data)
        future_apex = executor.submit(run_wrapper_direct, apex_wrapper, ticker, stock_data)
        
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
    
    # === SUPER AGENT 4.0 AGGREGATION ===
    
    # --- FIX #1: Graduated Signal Normalization ---
    # BUY and STRONG BUY are no longer identical.
    def normalize_signal(signal):
        s = signal.upper().replace("_", " ")
        if "STRONG BUY" in s: return 1.0
        if "STRONG SELL" in s: return -1.0
        if "BUY" in s: return 0.7       # Weaker than STRONG BUY
        if "SELL" in s: return -0.7      # Weaker than STRONG SELL
        return 0.0  # WAIT / HOLD
    
    # Helper: Get direction only (+1, -1, 0) for consensus check
    def get_direction(signal):
        s = signal.upper().replace("_", " ")
        if "BUY" in s: return 1
        if "SELL" in s: return -1
        return 0
        
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
    
    # --- FIX #10: Model-Specific Persistence Weights ---
    MODEL_WEIGHTS = {
        "Hedge Fund Manager":       [0.40, 0.35, 0.25],   # Slow (institutional)
        "Most Advance stock_AI":    [0.50, 0.30, 0.20],   # Balanced
        "Quantitative Development": [0.50, 0.30, 0.20],   # Balanced
        "Apex Logic":               [0.60, 0.25, 0.15],   # Fast (price action)
    }
    
    def calculate_persistence_score(res, mode_key, model_name):
        if "error" in res: return 0
        
        history = res.get('history', [])
        
        # Fallback: no history available
        if not history:
            current = res.get(mode_key, {})
            sig = current.get('signal', 'WAIT')
            conf = current.get('confidence', 0)
            return normalize_signal(sig) * conf * 0.5
        
        weights = MODEL_WEIGHTS.get(model_name, [0.5, 0.3, 0.2])
        score = 0
        
        for i, h_item in enumerate(history):
            if i >= 3: break
            s_val = normalize_signal(h_item.get('signal', 'WAIT'))
            c_val = h_item.get('confidence', 0)
            score += (s_val * c_val * weights[i])
            
        return score

    # --- FIX #12: Model Consensus Gate ---
    def check_consensus(results, mode_key):
        """
        Returns True if models generally agree, False if there's a conflict.
        A conflict = one model says BUY and another says SELL.
        """
        directions = []
        for model_name, res in results.items():
            if "error" in res: continue
            current = res.get(mode_key, {})
            sig = current.get('signal', 'WAIT')
            d = get_direction(sig)
            if d != 0:  # Only count non-WAIT models
                directions.append(d)
        
        if not directions:
            return True  # All WAIT = no conflict
        
        has_buy = any(d > 0 for d in directions)
        has_sell = any(d < 0 for d in directions)
        
        # Conflict: at least one model says BUY and another says SELL
        return not (has_buy and has_sell)

    def calculate_super_score(results, mode_key):
        total_score = 0
        valid_models = 0
        
        for model_name, res in results.items():
            if "error" in res: continue
            
            p_score = calculate_persistence_score(res, mode_key, model_name)
            total_score += p_score
            valid_models += 1
            
        final_score = total_score / valid_models if valid_models > 0 else 0
        
        # --- FILTERS ---
        
        # FIX #9: Graduated ADX Filter (Not hard kill)
        # ADX < 20: Hard veto (truly choppy)
        # ADX 20-25: 50% penalty (borderline)
        # ADX > 25: No penalty (trending)
        if mode_key == 'swing':
            if avg_adx < 20:
                if final_score > 0: final_score = 0  # Hard veto
            elif avg_adx < 25:
                if final_score > 0: final_score *= 0.5  # 50% penalty
        
        # FIX #12: Consensus Gate
        # If models disagree on direction, force WAIT
        if not check_consensus(results, mode_key):
            if abs(final_score) < 0.6:  # Only override if not a very strong signal
                final_score *= 0.3  # Heavy penalty for disagreement
                
        return final_score

    super_score_swing = calculate_super_score(results, 'swing')
    super_score_intraday = calculate_super_score(results, 'intraday')
    
    # Determine Final Signals
    def get_final_signal(score):
        # Apply regime penalty
        req_buy_score = 0.15
        req_strong_buy = 0.50
        
        if GLOBAL_REGIME['regime'] in ['BEAR', 'HIGH_VOL']:
            req_buy_score = 0.35      # Stricter entry in bad markets
            req_strong_buy = 0.75
            
        if score >= req_strong_buy: return "STRONG BUY"
        if score > req_buy_score: return "BUY"
        if score <= -0.5: return "STRONG SELL"
        if score < -0.15: return "SELL"
        return "WAIT"
        
    final_signal_swing = get_final_signal(super_score_swing)
    final_signal_intraday = get_final_signal(super_score_intraday)
    
    # --- SUPREME TIER Classification ---
    # A stock gets "SUPREME" badge ONLY if ALL of:
    # 1. All 3 history days aligned as BUY for all working models
    # 2. All working models agree on BUY direction
    # 3. ADX > 25
    # 4. Super Score >= 0.6
    def check_supreme(results, mode_key, super_score):
        if super_score < 0.6: return False
        if avg_adx < 25: return False
        
        for model_name, res in results.items():
            if "error" in res: continue
            
            # Check current signal is BUY
            current = res.get(mode_key, {})
            if get_direction(current.get('signal', 'WAIT')) != 1:
                return False
            
            # Check all history days are BUY
            history = res.get('history', [])
            for h in history:
                if get_direction(h.get('signal', 'WAIT')) != 1:
                    return False
        
        return True
    
    is_supreme_swing = check_supreme(results, 'swing', super_score_swing)
    is_supreme_intraday = check_supreme(results, 'intraday', super_score_intraday)
    
    # Extract Trade Params
    def extract_params(model_results, mode_key, final_sig):
        params = {"entry": 0, "target": 0, "sl": 0}
        
        # Priority: Apex > Quant > StockAI > HFM for trade params
        priority = ["Apex Logic", "Quantitative Development", "Most Advance stock_AI", "Hedge Fund Manager"]
        
        # Normalize final_sig for comparison
        final_sig_norm = final_sig.upper().replace("_", " ")
        
        for name in priority:
            res = model_results.get(name, {})
            if "error" in res: continue
            
            mode_data = res.get(mode_key, {})
            model_sig = mode_data.get('signal', 'WAIT').upper().replace("_", " ")
            
            # Exact or loose match (BUY matches STRONG BUY direction)
            if final_sig_norm != "WAIT":
                final_dir = get_direction(final_sig_norm)
                model_dir = get_direction(model_sig)
                
                if final_dir == model_dir and final_dir != 0:
                    params['entry'] = mode_data.get('entry', 0)
                    params['target'] = mode_data.get('target', 0)
                    params['sl'] = mode_data.get('sl', 0)
                    return params
        
        # Fallback: take from Apex
        res = model_results.get("Apex Logic", {})
        if "error" not in res:
            mode_data = res.get(mode_key, {})
            params['entry'] = mode_data.get('entry', 0)
            params['target'] = mode_data.get('target', 0)
            params['sl'] = mode_data.get('sl', 0)
        # Dynamic trailing stop calculation
        if params.get('entry', 0) > 0 and params.get('sl', 0) > 0:
            risk = params['entry'] - params['sl']
            if risk > 0:
                # Adjust reward based on trend strength
                if avg_adx > 35 and avg_rvol > 2.0:
                    params['target'] = params['entry'] + (3.0 * risk)  # 1:3 RR
                elif avg_adx > 25:
                    params['target'] = params['entry'] + (2.0 * risk)  # 1:2 RR
                else:
                    params['target'] = params['entry'] + (1.5 * risk)  # 1:1.5 RR
                
                params['trailing_activation'] = params['entry'] + risk
                params['max_holding_days'] = 5
            
        return params

    params_swing = extract_params(results, 'swing', final_signal_swing)
    params_intraday = extract_params(results, 'intraday', final_signal_intraday)
    
    # --- META-ML MODEL PREDICTION ---
    # Use the trained meta-model to predict probability of hitting +3% in 5 days
    ml_confidence = None
    if META_MODEL is not None:
        try:
            # Build trade_data dict matching backtest format
            def get_model_signal(model_name, mode_key):
                res = results.get(model_name, {})
                if "error" in res: return 'WAIT', 0
                md = res.get(mode_key, {})
                return md.get('signal', 'WAIT'), md.get('confidence', 0)
            
            apex_sig, apex_conf = get_model_signal("Apex Logic", "swing")
            hfm_sig, hfm_conf = get_model_signal("Hedge Fund Manager", "swing")
            stockai_sig, stockai_conf = get_model_signal("Most Advance stock_AI", "swing")
            quant_sig, quant_conf = get_model_signal("Quantitative Development", "swing")
            
            # Get ADX/RSI/RVOL/MACD from Apex details (most reliable source)
            apex_details = results.get("Apex Logic", {}).get("details", {})
            
            trade_data = {
                'apex_signal': apex_sig, 'apex_conf': apex_conf,
                'hfm_signal': hfm_sig, 'hfm_conf': hfm_conf,
                'stockai_signal': stockai_sig, 'stockai_conf': stockai_conf,
                'quant_signal': quant_sig, 'quant_conf': quant_conf,
                'ensemble_signal': final_signal_swing,
                'super_score': super_score_swing,
                'rsi': 50, 'adx': avg_adx, 'rvol': avg_rvol, 'macd_diff': 0,
                'above_sma50': 1 if apex_details.get('trend_score', 0) >= 0 else 0,
                'above_sma200': 1 if apex_details.get('trend_score', 0) > 0 else 0,
                'above_ema20': 1 if apex_details.get('mom_score', 0) >= 0 else 0,
                'above_vwap': 1 if apex_details.get('vol_boost', 0) >= 0 else 0,
            }
            
            ml_confidence = predict_with_meta(META_MODEL, trade_data)
            
            # Use ML confidence to enhance/degrade signal
            if ml_confidence is not None:
                if ml_confidence > 0.7 and "BUY" in final_signal_swing:
                    # High ML confidence — upgrade signal text
                    if final_signal_swing == "BUY":
                        final_signal_swing = "STRONG BUY"
                elif ml_confidence < 0.3 and "BUY" in final_signal_swing:
                    # Low ML confidence — downgrade
                    final_signal_swing = "WAIT"
        except Exception as e:
            print(f"[Meta-ML] Prediction failed for {ticker}: {e}")
            ml_confidence = None
            
    # Calculate Risk Management (Position Sizing)
    pos_size_swing = calculate_position_size(ml_confidence, super_score_swing, GLOBAL_REGIME['regime'])
    pos_size_intraday = calculate_position_size(ml_confidence, super_score_intraday, GLOBAL_REGIME['regime'])
    
    # Get Sector Confluence
    sector_trend = get_sector_trend(ticker)
    
    # Construct Result Objects
    swing_res = {
        "ticker": ticker,
        "final_signal": ("[SUPREME] " + final_signal_swing) if is_supreme_swing else final_signal_swing,
        "super_score": super_score_swing,
        "ml_confidence": round(ml_confidence, 4) if ml_confidence is not None else None,
        "position_size_pct": pos_size_swing,
        "market_regime": GLOBAL_REGIME['regime'],
        "sector_trend": sector_trend,
        "entry": params_swing['entry'],
        "target": params_swing['target'],
        "sl": params_swing['sl'],
        "is_supreme": is_supreme_swing,
        "models": {k: v.get('swing', {}) for k, v in results.items() if "error" not in v}
    }
    
    intraday_res = {
        "ticker": ticker,
        "final_signal": ("[SUPREME] " + final_signal_intraday) if is_supreme_intraday else final_signal_intraday,
        "super_score": super_score_intraday,
        "ml_confidence": round(ml_confidence, 4) if ml_confidence is not None else None,
        "position_size_pct": pos_size_intraday,
        "market_regime": GLOBAL_REGIME['regime'],
        "sector_trend": sector_trend,
        "entry": params_intraday['entry'],
        "target": params_intraday['target'],
        "sl": params_intraday['sl'],
        "is_supreme": is_supreme_intraday,
        "models": {k: v.get('intraday', {}) for k, v in results.items() if "error" not in v}
    }
    
    # Add error info if any
    for k, v in results.items():
        if "error" in v:
            error_msg = v['error']
            short_err = f"ERR: {error_msg[:100]}" 
            swing_res['models'][k] = {"signal": short_err, "confidence": 0}
            intraday_res['models'][k] = {"signal": short_err, "confidence": 0}

    # Apply Sniper Filter for high-precision swing signals
    swing_res = apply_swing_sniper_filter(swing_res, results, avg_adx, avg_rvol)

    return swing_res, intraday_res

def apply_swing_sniper_filter(swing_res, results, avg_adx, avg_rvol):
    """Ultra-strict filter for swing trades. Sacrifice frequency for >90% precision.
    Only passes signals where ALL conditions align."""
    
    # Only filter BUY signals (let SELL/WAIT pass through)
    if 'BUY' not in swing_res.get('final_signal', ''):
        return swing_res
    
    reasons_to_reject = []
    
    # 1. ADX must show strong trend
    if avg_adx < 25:
        reasons_to_reject.append(f'ADX too low ({avg_adx:.1f} < 25)')
    
    # 2. Volume confirmation needed
    if avg_rvol < 1.3:
        reasons_to_reject.append(f'RVOL too low ({avg_rvol:.1f} < 1.3)')
    
    # 3. Sector must be bullish
    if swing_res.get('sector_trend') == 'DOWN':
        reasons_to_reject.append('Sector trend is DOWN')
    
    # 4. Market regime check
    if swing_res.get('market_regime') in ['BEAR', 'HIGH_VOL']:
        reasons_to_reject.append(f'Bad regime: {swing_res["market_regime"]}')
    
    # 5. Model consensus — count how many models say BUY
    buy_count = 0
    working_models = 0
    for model_name, res in results.items():
        if 'error' in res:
            continue
        working_models += 1
        swing_data = res.get('swing', {})
        sig = swing_data.get('signal', 'WAIT').upper()
        if 'BUY' in sig:
            buy_count += 1
    
    if working_models > 0 and buy_count < max(2, int(working_models * 0.6)):
        reasons_to_reject.append(f'Weak consensus ({buy_count}/{working_models} models agree)')
    
    # 6. ML confidence check (if available)
    ml_conf = swing_res.get('ml_confidence')
    if ml_conf is not None and ml_conf < 0.55:
        reasons_to_reject.append(f'Low ML confidence ({ml_conf:.2f} < 0.55)')
    
    # If ANY reason to reject, downgrade to WATCH
    if reasons_to_reject:
        swing_res['final_signal'] = 'WATCH'
        swing_res['sniper_filtered'] = True
        swing_res['filter_reasons'] = reasons_to_reject
    else:
        swing_res['sniper_filtered'] = False
        swing_res['sniper_approved'] = True
    
    return swing_res

def main():
    print("Initializing Super Agent 4.0...")
    print(f"Wrapper Directory: {WRAPPER_DIR}")
    
    # Fetch NIFTY 500
    tickers = get_nifty500()
    
    if not tickers:
        print("Fallback to hardcoded list (Critical Error)")
        tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
    
    print(f"Starting analysis for {len(tickers)} stocks...")
    
    # Centralized data fetch — download ALL tickers in one batch
    print("Fetching market data for all tickers (single batch)...")
    data_cache = fetch_all_data(tickers)
    print(f"Data available for {len(data_cache)} tickers")
    
    swing_results = []
    intraday_results = []
    
    for i, ticker in enumerate(tickers):
        print(f"[{i+1}/{len(tickers)}] ", end="")
        try:
            stock_data = get_stock_data(ticker)
            if stock_data is None:
                print(f"Skipping {ticker} (no data)")
                continue
            s_res, i_res = analyze_stock(ticker, stock_data)
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
