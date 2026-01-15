import sys
import os
import json
import argparse
import contextlib
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

def run_analysis(ticker):
    # Relative path: ../../Quantitative Development
    WRAPPER_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(WRAPPER_DIR))
    MODEL_PATH = os.path.join(PROJECT_ROOT, "Quantitative Development")
    
    if MODEL_PATH not in sys.path:
        sys.path.insert(0, MODEL_PATH)

    try:
        with suppress_stdout():
            from fundamental import get_fundamental_score
            from technical import get_technical_indicators, check_intraday_vwap
            from sentiment import get_sentiment_score

            # Fetch Data Manually Once
            import yfinance as yf
            df_full = yf.download(ticker, period="1y", interval="1d", progress=False)
            
            # Helper for analysis
            def analyze_slice(df_slice):
                f_score, _ = get_fundamental_score(ticker) # Fund score static
                t_score, t_signals = get_technical_indicators(ticker, df=df_slice)
                s_score, _ = get_sentiment_score(ticker) # Sent score static (hard to get history easily without API cost/complexity)
                
                s_score_norm = (s_score + 1) * 5
                
                fin_score = (f_score * 0.3) + (t_score * 0.5) + (s_score_norm * 0.2)
                
                # Signal logic
                action = "WAIT"
                if fin_score > 7: action = "BUY"
                elif fin_score < 3: action = "SELL"
                
                return {
                    "score": fin_score,
                    "signal": action,
                    "tech_signals": t_signals, # Contains ADX/RVOL
                    "fund_score": f_score,
                    "tech_score": t_score,
                    "sent_score": s_score
                }

            # Generate History
            history = []
            for i in range(3):
                if len(df_full) < 200 + i: break # Ensure enough data
                
                slice_df = df_full if i == 0 else df_full[:-i]
                res = analyze_slice(slice_df)
                
                # Confidence scaling
                conf = res['score'] / 10.0
                if res['score'] < 3: conf = (3 - res['score']) / 3.0
                
                history.append({
                    "date": str(slice_df.index[-1]) if hasattr(slice_df.index, 'date') else f"T-{i}",
                    "signal": res['signal'],
                    "confidence": conf,
                    "score": res['score']
                })
            
            # Current Analysis (T)
            current_res = analyze_slice(df_full)
            tech_s = current_res['tech_signals']
            final_score = current_res['score']
            
            # ... (Rest of logic using current_res) ...
            
            intraday_signal_check = False
            if final_score > 6:
                intraday_signal_check = check_intraday_vwap(ticker)
                
            base_action = current_res['signal']
            base_conf = final_score / 10.0
            
            if final_score > 7:
                if intraday_signal_check:
                    base_conf = min(base_conf + 0.1, 1.0)
            elif final_score > 5:
                base_action = "WAIT"
            
            if final_score < 3:
                base_action = "SELL"
                base_conf = (3 - final_score) / 3.0
            
            close_price = tech_s.get('Close', 0)
            atr = tech_s.get('ATR', close_price * 0.02)
            adx = tech_s.get('ADX', 0)
            rvol = tech_s.get('RVOL', 0)
            
            # --- SWING LOGIC ---
            swing_signal = base_action
            swing_conf = base_conf
            
            swing_sl = 0
            swing_target = 0
            
            if swing_signal == "BUY":
                swing_sl = close_price - (1.5 * atr)
                swing_target = close_price + (3.0 * atr)
            elif swing_signal == "SELL":
                swing_sl = close_price + (1.5 * atr)
                swing_target = close_price - (3.0 * atr)
            
            swing_data = {
                "signal": swing_signal,
                "confidence": swing_conf,
                "entry": close_price,
                "target": swing_target,
                "sl": swing_sl
            }
            
            # --- INTRADAY LOGIC ---
            intraday_signal = base_action
            intraday_conf = base_conf
            
            if intraday_signal == "BUY" and not intraday_signal_check:
                intraday_signal = "WAIT"
                intraday_conf = 0.0
            
            intraday_sl = 0
            intraday_target = 0
            
            if intraday_signal == "BUY":
                intraday_sl = close_price - (0.5 * atr)
                intraday_target = close_price + (1.0 * atr)
            elif intraday_signal == "SELL":
                intraday_sl = close_price + (0.5 * atr)
                intraday_target = close_price - (1.0 * atr)
                
            intraday_data = {
                "signal": intraday_signal,
                "confidence": intraday_conf,
                "entry": close_price,
                "target": intraday_target,
                "sl": intraday_sl
            }
            
            return {
                "model_name": "Quantitative Development",
                "swing": swing_data,
                "intraday": intraday_data,
                "history": history,
                "details": {
                    "final_score": final_score,
                    "fund_score": current_res['fund_score'],
                    "tech_score": current_res['tech_score'],
                    "sent_score": current_res['sent_score'],
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
