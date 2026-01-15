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
    # Relative path: ../../Most Advance stock_AI
    WRAPPER_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(WRAPPER_DIR))
    MODEL_PATH = os.path.join(PROJECT_ROOT, "Most Advance stock_AI")
    
    if MODEL_PATH not in sys.path:
        sys.path.insert(0, MODEL_PATH)

    try:
        with suppress_stdout():
            from data_engine import DataEngine
            from fundamental_engine import FundamentalEngine
            from technical_engine import TechnicalEngine
            from ml_engine import MLEngine
            from strategy_engine import StrategyEngine

            data_engine = DataEngine()
            fund_engine = FundamentalEngine()
            tech_engine = TechnicalEngine()
            strat_engine = StrategyEngine()

            # Fetch Data
            df = data_engine.fetch_ohlcv(ticker)
            if df is None or df.empty:
                return {"error": "No data"}
            
            # Helper for analysis
            def analyze_slice(df_slice):
                # Data check
                if df_slice is None or df_slice.empty: return None
                
                # Fundamental Analysis (Static)
                fund_data = fund_engine.analyze(ticker)
                
                # Technical Analysis (Dynamic)
                tech_data = tech_engine.analyze(ticker, df_slice)
                
                stock_data = {
                    "symbol": ticker,
                    "technical_score": tech_data.get('score', 0),
                    "fundamental_score": fund_data.get('score', 0),
                    "technical_signals": tech_data.get('signals', {}),
                    "fundamental_metrics": fund_data.get('metrics', {}),
                    "latest_price": tech_data.get('latest_price', 0)
                }
                
                # Calculate Confidence Score
                tech_score = stock_data['technical_score']
                fund_score = stock_data['fundamental_score']
                confidence_score = (tech_score * 0.6) + (fund_score * 0.4)
                stock_data['confidence_score'] = confidence_score
                
                # Generate Signal
                signal_data = strat_engine.generate_signals(stock_data)
                
                return {
                    "stock_data": stock_data,
                    "signal_data": signal_data
                }

            # Generate History
            history = []
            for i in range(3):
                if len(df) < 50 + i: break # Ensure enough data
                
                slice_df = df if i == 0 else df[:-i]
                res = analyze_slice(slice_df)
                if not res: continue
                
                sig_d = res['signal_data']
                stk_d = res['stock_data']
                
                base_signal = sig_d.get('recommendation', 'WAIT')
                if 'BUY' in base_signal.upper(): base_signal = 'BUY'
                elif 'SELL' in base_signal.upper(): base_signal = 'SELL'
                else: base_signal = 'WAIT'
                
                conf = sig_d.get('confidence_score', 0.0)
                if conf > 1.0: conf /= 100.0
                
                history.append({
                    "date": str(slice_df.index[-1]) if hasattr(slice_df.index, 'date') else f"T-{i}",
                    "signal": base_signal,
                    "confidence": conf
                })

            # Current Analysis (T)
            current_res = analyze_slice(df)
            if not current_res: return {"error": "Analysis failed"}
            
            stock_data = current_res['stock_data']
            signal_data = current_res['signal_data']
            tech_s = stock_data['technical_signals']
            
            base_signal = signal_data.get('recommendation', 'WAIT')
            if 'BUY' in base_signal.upper(): base_signal = 'BUY'
            elif 'SELL' in base_signal.upper(): base_signal = 'SELL'
            else: base_signal = 'WAIT'
            
            base_conf = signal_data.get('confidence_score', 0.0)
            if base_conf > 1.0: base_conf /= 100.0
            
            entry_price = signal_data.get('entry', {}).get('price', 0)
            atr = tech_s.get('atr', entry_price * 0.02)
            adx = tech_s.get('adx', 0)
            rvol = tech_s.get('rvol', 0)
            
            # --- SWING LOGIC ---
            swing_signal = base_signal
            swing_conf = base_conf
            
            swing_sl = 0
            swing_target = 0
            
            if swing_signal == "BUY":
                swing_sl = entry_price - (1.5 * atr)
                swing_target = entry_price + (3.0 * atr)
            elif swing_signal == "SELL":
                swing_sl = entry_price + (1.5 * atr)
                swing_target = entry_price - (3.0 * atr)
            
            swing_data = {
                "signal": swing_signal,
                "confidence": swing_conf,
                "entry": entry_price,
                "target": swing_target,
                "sl": swing_sl
            }
            
            # --- INTRADAY LOGIC ---
            intraday_signal = base_signal
            intraday_conf = base_conf
            
            intraday_sl = 0
            intraday_target = 0
            
            if intraday_signal == "BUY":
                intraday_sl = entry_price - (0.5 * atr)
                intraday_target = entry_price + (1.0 * atr)
            elif intraday_signal == "SELL":
                intraday_sl = entry_price + (0.5 * atr)
                intraday_target = entry_price - (1.0 * atr)
                
            intraday_data = {
                "signal": intraday_signal,
                "confidence": intraday_conf,
                "entry": entry_price,
                "target": intraday_target,
                "sl": intraday_sl
            }
            
            return {
                "model_name": "Most Advance stock_AI",
                "swing": swing_data,
                "intraday": intraday_data,
                "history": history,
                "details": {
                    "tech_score": stock_data['technical_score'],
                    "fund_score": stock_data['fundamental_score'],
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
