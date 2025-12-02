import sys
import os
import json
import argparse
import contextlib

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

            # Phase 2: Fundamental
            fund_score, fund_details = get_fundamental_score(ticker)
            
            # Phase 3: Technical
            tech_score, tech_signals = get_technical_indicators(ticker)
            
            # Phase 4: Sentiment
            sent_score, headlines = get_sentiment_score(ticker)
            
            sent_score_normalized = (sent_score + 1) * 5
            
            final_score = (fund_score * 0.3) + (tech_score * 0.5) + (sent_score_normalized * 0.2)
            
            intraday_signal_check = False
            if final_score > 6:
                intraday_signal_check = check_intraday_vwap(ticker)
                
            base_action = "WAIT"
            base_conf = final_score / 10.0
            
            if final_score > 7:
                base_action = "BUY"
                if intraday_signal_check:
                    base_conf = min(base_conf + 0.1, 1.0)
            elif final_score > 5:
                base_action = "WAIT"
            
            # Quant model logic is heavily biased towards BUY (Score > 7).
            # It doesn't seem to have explicit SELL logic in main.py, but let's assume low score could be SELL if we wanted.
            # For now, we stick to BUY/WAIT as per original code, but we can infer SELL if score is very low (e.g. < 3)
            if final_score < 3:
                base_action = "SELL"
                base_conf = (3 - final_score) / 3.0 # Simple confidence scaling
            
            close_price = tech_signals.get('Close', 0)
            atr = tech_signals.get('ATR', close_price * 0.02)
            
            # --- SWING LOGIC ---
            swing_signal = base_action
            swing_conf = base_conf
            
            # Enforce Long Only - REMOVED
            # if swing_signal == "SELL":
            #     swing_signal = "WAIT"
            #     swing_conf = 0.0
                
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
            
            # If intraday check (VWAP) failed, downgrade BUY to WAIT for intraday
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
                "details": {
                    "final_score": final_score,
                    "fund_score": fund_score,
                    "tech_score": tech_score,
                    "sent_score": sent_score
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
