import sys
import os

# Add super_agent to path
sys.path.append(r"e:\Project Alpha\super_agent")

try:
    from wrappers.hfm_wrapper import HFMWrapper
    from wrappers.stock_ai_wrapper import StockAIWrapper
    from wrappers.quant_wrapper import QuantWrapper
    print("Imports successful.")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_wrappers():
    ticker = "RELIANCE.NS"
    print(f"Testing on {ticker}...")
    
    try:
        print("Initializing HFM...")
        hfm = HFMWrapper()
        res = hfm.analyze_ticker(ticker)
        print(f"HFM Result: {res['signal']} (Conf: {res['confidence']})")
    except Exception as e:
        print(f"HFM Error: {e}")

    try:
        print("Initializing StockAI...")
        stock_ai = StockAIWrapper()
        res = stock_ai.analyze_ticker(ticker)
        print(f"StockAI Result: {res['signal']} (Conf: {res['confidence']})")
    except Exception as e:
        print(f"StockAI Error: {e}")

    try:
        print("Initializing Quant...")
        quant = QuantWrapper()
        res = quant.analyze_ticker(ticker)
        print(f"Quant Result: {res['signal']} (Conf: {res['confidence']})")
    except Exception as e:
        print(f"Quant Error: {e}")

if __name__ == "__main__":
    test_wrappers()
