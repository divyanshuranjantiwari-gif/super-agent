import sys
import os
import json
import argparse
import contextlib

# Suppress stdout during imports and processing to keep JSON clean
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
    # Add model directory to path
    # Relative path: ../../Hedge Fund Manager
    WRAPPER_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(WRAPPER_DIR))
    MODEL_PATH = os.path.join(PROJECT_ROOT, "Hedge Fund Manager")
    
    if MODEL_PATH not in sys.path:
        sys.path.insert(0, MODEL_PATH)

    try:
        with suppress_stdout():
            from data_pipeline import get_historical_data, get_market_mood, get_option_chain_analysis, get_news_sentiment
            from features import add_technical_indicators, add_relative_strength, calculate_vwap, calculate_alpha_beta
            from model import train_predict_model
            from strategy import generate_signal
            import pandas as pd

            # Cache/Fetch Data
            market_mood = get_market_mood()
            option_data = get_option_chain_analysis("NIFTY")
            nifty_data = get_historical_data(["^NSEI"], period="2y")
            if not nifty_data.empty and isinstance(nifty_data.columns, pd.MultiIndex):
                 nifty_data = nifty_data["^NSEI"]

            # Analyze Ticker
            hist_data = get_historical_data([ticker], period="2y")
            
            if isinstance(hist_data.columns, pd.MultiIndex):
                if ticker not in hist_data.columns.levels[0]:
                    return {"error": "No data"}
                df = hist_data[ticker].copy()
            else:
                if hist_data.empty: return {"error": "No data"}
                df = hist_data.copy()
            
            if df.empty:
                return {"error": "Empty data"}

            # Feature Engineering
            df = add_technical_indicators(df)
            if not nifty_data.empty:
                df = add_relative_strength(df, nifty_data)
                
            # HFM 2.0 Calculations
            df = calculate_vwap(df)
            if not nifty_data.empty:
                df = calculate_alpha_beta(df, nifty_data)
            
            # AI Prediction
            predicted_price, model_score = train_predict_model(df)
            
            if predicted_price is None:
                predicted_price = df['Close'].iloc[-1]
                
            # Sentiment
            sentiment_score = get_news_sentiment(ticker)
            
            # Generate Signal
            current_row = df.iloc[-1]
            close_price = current_row['Close']
            atr = current_row.get('ATR', close_price * 0.02)
            
            signal_data = generate_signal(
                ticker, 
                current_row, 
                predicted_price, 
                market_mood, 
                option_data, 
                sentiment_score
            )
            
            base_signal = signal_data.get('Signal', 'WAIT')
            base_confidence = signal_data.get('Confidence', 0.5)
            if base_confidence > 1.0: base_confidence /= 100.0
            
            # --- SWING LOGIC ---
            swing_signal = base_signal
            swing_conf = base_confidence
            
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
            # HFM is daily, so we use base signal as trend bias
            intraday_signal = base_signal
            intraday_conf = base_confidence
            
            # Intraday allows Shorting, so we keep SELL signal
            
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
                "model_name": "Hedge Fund Manager",
                "swing": swing_data,
                "intraday": intraday_data,
                "details": {
                    "predicted_price": predicted_price,
                    "model_score": model_score,
                    "sentiment": sentiment_score
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
