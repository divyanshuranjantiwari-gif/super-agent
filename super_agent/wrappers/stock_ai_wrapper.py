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
            
            # Fundamental Analysis
            fund_data = fund_engine.analyze(ticker)
            
            # Technical Analysis
            tech_data = tech_engine.analyze(ticker, df)
            
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
            
            base_signal = signal_data.get('recommendation', 'WAIT')
            if 'BUY' in base_signal.upper(): base_signal = 'BUY'
            elif 'SELL' in base_signal.upper(): base_signal = 'SELL'
            else: base_signal = 'WAIT'
            
            base_conf = signal_data.get('confidence_score', 0.0)
            if base_conf > 1.0: base_conf /= 100.0
            
            entry_price = signal_data.get('entry', {}).get('price', 0)
            atr = stock_data['technical_signals'].get('atr', entry_price * 0.02)
            
            # --- SWING LOGIC ---
            swing_signal = base_signal
            swing_conf = base_conf
            
            # Enforce Long Only - REMOVED
            # if swing_signal == "SELL":
            #     swing_signal = "WAIT"
            #     swing_conf = 0.0
                
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
                "details": {
                    "tech_score": stock_data['technical_score'],
                    "fund_score": stock_data['fundamental_score']
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
