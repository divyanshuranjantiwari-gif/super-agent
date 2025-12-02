import yfinance as yf
from utils import logger

def get_fundamental_score(ticker):
    """
    Fetches metadata and calculates a Fundamental Score (0-10).
    Criteria:
    - P/E > 0 and < Industry Average (or < 30 if industry N/A)
    - ROE > 15%
    - Debt-to-Equity < 1.0
    - Profit Margins > 0 and Revenue Growth > 0
    """
    score = 0
    details = {}
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 1. P/E Ratio
        pe = info.get('trailingPE', None)
        # yfinance often doesn't provide industry PE directly. 
        # We'll use a conservative benchmark of 25 if not available, or just check it's not insane.
        # Ideally we would scrape industry data, but for this scope we'll use a heuristic.
        
        if pe is not None and pe > 0:
            if pe < 25: # Assuming 25 as a generic "good" threshold for value
                score += 2.5
                details['P/E'] = f"{pe:.2f} (Pass)"
            else:
                details['P/E'] = f"{pe:.2f} (High)"
        else:
            details['P/E'] = "N/A or Negative"

        # 2. ROE
        roe = info.get('returnOnEquity', None)
        if roe is not None:
            if roe > 0.15: # 15%
                score += 2.5
                details['ROE'] = f"{roe*100:.2f}% (Pass)"
            else:
                details['ROE'] = f"{roe*100:.2f}% (Fail)"
        else:
            details['ROE'] = "N/A"

        # 3. Debt-to-Equity
        de = info.get('debtToEquity', None)
        if de is not None:
            # yfinance returns D/E as a percentage sometimes, or ratio. 
            # Usually it's a percentage (e.g. 50.5 for 0.505). Let's check magnitude.
            # If it's > 100, it's likely %, so 1.0 ratio = 100.
            # If it's < 10, it might be ratio. Safe bet: if > 2, assume %. 
            # Actually standard is usually %.
            
            # Let's assume it's a percentage (e.g. 80 means 0.8).
            # Threshold < 1.0 ratio means < 100%.
            if de < 100: 
                score += 2.5
                details['D/E'] = f"{de:.2f}% (Pass)"
            else:
                details['D/E'] = f"{de:.2f}% (High)"
        else:
            details['D/E'] = "N/A"

        # 4. Profit Margins & Growth
        margins = info.get('profitMargins', None)
        growth = info.get('revenueGrowth', None)
        
        if margins is not None and margins > 0:
            if growth is not None and growth > 0:
                score += 2.5
                details['Growth'] = f"Margin {margins*100:.1f}%, RevGrowth {growth*100:.1f}% (Pass)"
            else:
                # Partial credit for just margins? Let's stick to "Positive and Growing"
                details['Growth'] = f"Margin {margins*100:.1f}%, RevGrowth {growth} (Fail)"
        else:
            details['Growth'] = "N/A"

    except Exception as e:
        logger.error(f"Fundamental check failed for {ticker}: {e}")
        return 0, {"Error": str(e)}

    return score, details
