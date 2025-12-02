def generate_signal(ticker, current_data, predicted_price, market_mood, option_data, sentiment_score):
    """
    Generates trading signal based on HFM 2.0 Logic (Alpha + Institutional Flow).
    """
    current_price = current_data['Close']
    atr = current_data.get('ATR', current_price * 0.02)
    
    # HFM 2.0 Inputs
    alpha = current_data.get('Alpha', 0)
    beta = current_data.get('Beta', 1)
    vwap = current_data.get('VWAP', current_price)
    ema_20 = current_data.get('EMA_20', current_price) # Need to ensure EMA_20 is calculated in features/main
    
    # 1. Alpha Check (Are we beating the market?)
    has_alpha = alpha > 0
    
    # 2. Institutional Flow (VWAP)
    # Price > VWAP means institutions are likely net buyers
    institutional_buying = current_price > vwap
    
    # 3. Trend (EMA 20)
    short_term_trend_up = current_price > ema_20
    
    # 4. Market Bias (FII/DII)
    is_market_bearish = market_mood.get('Market_Bias') == 'BEARISH'
    
    # Signal Logic
    signal = "WAIT"
    confidence = 0
    
    # BUY Logic:
    # - Positive Alpha (Outperformer)
    # - Price > VWAP (Institutional Support)
    # - Price > EMA 20 (Trend Up)
    # - Market Not Bearish
    if has_alpha and institutional_buying and short_term_trend_up and not is_market_bearish:
        signal = "BUY"
        confidence = 80
        if alpha > 0.2: # High Alpha
            signal = "STRONG_BUY"
            confidence = 90
            
    # SELL Logic:
    # - Negative Alpha (Underperformer)
    # - Price < VWAP (Institutional Resistance)
    # - Price < EMA 20 (Trend Down)
    elif not has_alpha and not institutional_buying and not short_term_trend_up:
        signal = "SELL"
        confidence = 80
        if alpha < -0.2:
            signal = "STRONG_SELL"
            confidence = 90
            
    # Stop Loss & Target
    # Swing: SL = 1.5 ATR, Target = 3 ATR
    if "BUY" in signal:
        stop_loss = current_price - (1.5 * atr)
        target = current_price + (3.0 * atr)
    elif "SELL" in signal:
        stop_loss = current_price + (1.5 * atr)
        target = current_price - (3.0 * atr)
    else:
        stop_loss = 0
        target = 0
    
    return {
        "Ticker": ticker,
        "Signal": signal,
        "Current_Price": round(current_price, 2),
        "Predicted_Price": round(predicted_price, 2), # Kept for reference
        "Alpha": round(alpha, 4),
        "Beta": round(beta, 2),
        "VWAP": round(vwap, 2),
        "Confidence": confidence,
        "Stop_Loss": round(stop_loss, 2),
        "Target": round(target, 2),
        "Market_Bias": market_mood.get('Market_Bias')
    }
