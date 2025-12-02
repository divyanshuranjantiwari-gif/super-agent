class StrategyEngine:
    def __init__(self):
        pass

    def generate_signals(self, stock_data):
        """
        Decides BUY/SELL/HOLD based on scores and specific conditions.
        """
        symbol = stock_data['symbol']
        tech_score = stock_data.get('technical_score', 0)
        fund_score = stock_data.get('fundamental_score', 0)
        confidence = stock_data.get('confidence_score', 0)
        latest_price = stock_data.get('latest_price', 0)
        atr = stock_data.get('technical_signals', {}).get('atr', latest_price * 0.02) # Default 2% if no ATR
        
        recommendation = "HOLD"
        time_horizon = "N/A"
        
        # Logic
        if confidence > 75:
            recommendation = "BUY"
            if tech_score > 80:
                time_horizon = "swing"
            else:
                time_horizon = "positional"
        elif confidence < 30:
            recommendation = "SELL" # or Avoid
        
        # Risk Management
        sl = 0.0
        targets = []
        
        if recommendation == "BUY":
            # Stop Loss: 2 * ATR below price
            sl = latest_price - (2 * atr)
            
            # Targets: 1:2 and 1:3 Risk:Reward
            risk = latest_price - sl
            t1 = latest_price + (2 * risk)
            t2 = latest_price + (3 * risk)
            
            targets = [
                {"price": round(t1, 2), "probability": 0.7},
                {"price": round(t2, 2), "probability": 0.5}
            ]
            
        return {
            "symbol": symbol,
            "recommendation": recommendation,
            "time_horizon": time_horizon,
            "entry": {"price": round(latest_price, 2), "range": [round(latest_price * 0.995, 2), round(latest_price * 1.005, 2)]},
            "stop_loss": round(sl, 2),
            "targets": targets,
            "confidence_score": round(confidence, 2),
            "risk_grade": "Medium" if fund_score > 50 else "High"
        }

if __name__ == "__main__":
    pass
