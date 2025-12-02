import yfinance as yf
import pandas as pd

class FundamentalEngine:
    def __init__(self):
        pass

    def analyze(self, symbol):
        """
        Analyzes fundamental data for a given symbol.
        Returns a dictionary with metrics and a score.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract key metrics with defaults
            metrics = {
                "pe_ratio": info.get("trailingPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "roe": info.get("returnOnEquity", 0),
                "profit_margins": info.get("profitMargins", 0),
                "debt_to_equity": info.get("debtToEquity", 0),
                "market_cap": info.get("marketCap", 0),
                "revenue_growth": info.get("revenueGrowth", 0),
            }
            
            score = self.calculate_score(metrics)
            
            return {
                "metrics": metrics,
                "score": score
            }
        except Exception as e:
            print(f"Error in fundamental analysis for {symbol}: {e}")
            return {"metrics": {}, "score": 0}

    def calculate_score(self, metrics):
        """
        Calculates a fundamental score (0-100) based on weighted metrics.
        """
        score = 50 # Start with neutral
        
        # PE Ratio (Lower is better, but not negative)
        pe = metrics["pe_ratio"]
        if 0 < pe < 15:
            score += 10
        elif 15 <= pe < 30:
            score += 5
        elif pe > 50:
            score -= 10
            
        # ROE (Higher is better)
        roe = metrics["roe"]
        if roe > 0.20:
            score += 15
        elif roe > 0.15:
            score += 10
        elif roe < 0.05:
            score -= 10
            
        # Profit Margins
        pm = metrics["profit_margins"]
        if pm > 0.15:
            score += 10
        elif pm < 0.05:
            score -= 5
            
        # Debt to Equity (Lower is better)
        de = metrics["debt_to_equity"]
        if de < 50: # yfinance returns percentage sometimes, need to verify unit. Assuming % here or ratio * 100
            score += 10
        elif de > 200:
            score -= 10
            
        # Cap at 100 and floor at 0
        return max(0, min(100, score))

if __name__ == "__main__":
    engine = FundamentalEngine()
    # Test with a known stock
    print(engine.analyze("RELIANCE.BO"))
