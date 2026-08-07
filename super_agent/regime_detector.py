import yfinance as yf
import pandas as pd
import numpy as np

def detect_market_regime():
    """
    Detects the current macro market regime based on NIFTY 50 trend and India VIX.
    
    Returns a dictionary:
    {
        'regime': 'BULL' | 'BEAR' | 'HIGH_VOL' | 'CHOPPY',
        'nifty_trend': 'UP' | 'DOWN',
        'vix_level': float,
        'vix_status': 'NORMAL' | 'ELEVATED' | 'EXTREME'
    }
    """
    try:
        # Fetch NIFTY 50 and India VIX data (last 60 days is enough for SMA50)
        tickers = ['^NSEI', '^INDIAVIX']
        data = yf.download(tickers, period="3mo", interval="1d", progress=False)['Close']
        
        # Handle cases where data might be missing
        if data.empty or '^NSEI' not in data.columns or '^INDIAVIX' not in data.columns:
            return _default_regime()
            
        nifty = data['^NSEI'].dropna()
        vix = data['^INDIAVIX'].dropna()
        
        if len(nifty) < 50 or len(vix) < 1:
            return _default_regime()
            
        # Calculate NIFTY 50 SMA
        nifty_sma50 = nifty.rolling(window=50).mean()
        
        current_nifty = nifty.iloc[-1]
        current_sma50 = nifty_sma50.iloc[-1]
        current_vix = vix.iloc[-1]
        
        # Determine NIFTY Trend
        nifty_trend = "UP" if current_nifty > current_sma50 else "DOWN"
        
        # Determine VIX Status
        if current_vix < 18:
            vix_status = "NORMAL"
        elif current_vix < 25:
            vix_status = "ELEVATED"
        else:
            vix_status = "EXTREME"
            
        # Classify Regime
        if vix_status == "EXTREME":
            regime = "HIGH_VOL" # Market is panicking, regardless of trend
        elif nifty_trend == "DOWN" and vix_status == "ELEVATED":
            regime = "BEAR"     # Downtrend with rising fear
        elif nifty_trend == "DOWN" and vix_status == "NORMAL":
            regime = "CHOPPY"   # Slow bleed / sideways
        elif nifty_trend == "UP" and vix_status != "EXTREME":
            regime = "BULL"     # Healthy uptrend
        else:
            regime = "CHOPPY"   # Fallback
            
        return {
            'regime': regime,
            'nifty_trend': nifty_trend,
            'vix_level': float(current_vix),
            'vix_status': vix_status
        }
        
    except Exception as e:
        print(f"[Regime Detector] Error: {e}")
        return _default_regime()

def _default_regime():
    return {
        'regime': 'UNKNOWN',
        'nifty_trend': 'UNKNOWN',
        'vix_level': 15.0,
        'vix_status': 'NORMAL'
    }

if __name__ == "__main__":
    regime_data = detect_market_regime()
    print("Market Regime Detection:")
    for k, v in regime_data.items():
        print(f"  {k.ljust(15)}: {v}")
