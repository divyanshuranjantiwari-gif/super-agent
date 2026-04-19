
import sys
import os
import json

# Add super_agent to path using script's own location
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'super_agent'))

from main import analyze_stock

def test_score():
    tickers = ["COALINDIA.NS", "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "TATAMOTORS.NS"]
    
    for ticker in tickers:
        print(f"\n{'='*60}")
        print(f"  TESTING: {ticker}")
        print(f"{'='*60}")
        
        try:
            swing, intraday = analyze_stock(ticker)
            
            print(f"\n  SWING RESULT:")
            print(f"  Final Signal : {swing['final_signal']}")
            print(f"  Super Score  : {swing['super_score']:.4f}")
            print(f"  ML Confidence: {swing.get('ml_confidence', 'N/A')}")
            print(f"  Supreme Tier : {'YES' if swing.get('is_supreme') else 'No'}")
            print(f"  Entry        : {swing['entry']}")
            print(f"  Stop Loss    : {swing['sl']}")
            print(f"  Target       : {swing['target']}")
            
            print(f"\n  MODEL BREAKDOWN:")
            for model, data in swing['models'].items():
                sig = data.get('signal', 'N/A')
                conf = data.get('confidence', 0)
                print(f"    {model}: {sig} (Conf: {conf})")
                
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"  ALL TESTS COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_score()
