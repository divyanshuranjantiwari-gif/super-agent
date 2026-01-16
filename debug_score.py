
import sys
import os
import json

# Add super_agent to path
sys.path.append(os.path.join(os.getcwd(), 'super_agent'))

from main import analyze_stock

def test_score():
    ticker = "COALINDIA.NS"
    print(f"\n--- Checking Super Score for {ticker} ---\n")
    
    try:
        swing, intraday = analyze_stock(ticker)
        
        print("\n--- SWING RESULT ---")
        print(f"Final Signal: {swing['final_signal']}")
        print(f"Super Score : {swing['super_score']:.4f}")
        print(f"Entry       : {swing['entry']}")
        print(f"Stop Loss   : {swing['sl']}")
        print(f"Target      : {swing['target']}")
        
        print("\n--- MODEL BREAKDOWN ---")
        for model, data in swing['models'].items():
            print(f"{model}: {data.get('signal')} (Conf: {data.get('confidence')})")
            
        # Manually verify calculation from output
        # (This helps user verify the logic)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_score()
