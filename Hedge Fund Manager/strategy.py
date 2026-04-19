def generate_signal(ticker, current_data, predicted_price, market_mood, option_data, sentiment_score):
    """
    Generates trading signal based on HFM 4.0 Logic.
    FIX #2: Dynamic confidence instead of hardcoded 80/90.
    FIX #3: Integrates predicted_price direction as a confirmation factor.
    """
    current_price = current_data['Close']
    atr = current_data.get('ATR', current_price * 0.02)
    
    # HFM Inputs
    alpha = current_data.get('Alpha', 0)
    beta = current_data.get('Beta', 1)
    vwap = current_data.get('VWAP', current_price)
    ema_20 = current_data.get('EMA_20', current_price)
    adx = current_data.get('ADX', 0)
    rsi = current_data.get('RSI', 50)
    
    # 1. Alpha Check (Are we beating the market?)
    has_alpha = alpha > 0
    
    # 2. Institutional Flow (VWAP)
    institutional_buying = current_price > vwap
    
    # 3. Trend (EMA 20)
    short_term_trend_up = current_price > ema_20
    
    # 4. Market Bias (FII/DII)
    is_market_bearish = market_mood.get('Market_Bias') == 'BEARISH'
    
    # 5. ML Prediction Direction (FIX #3)
    ml_bullish = predicted_price > current_price * 1.01  # Predicts >1% up
    ml_bearish = predicted_price < current_price * 0.99  # Predicts >1% down
    
    # === DYNAMIC CONFIDENCE CALCULATION (FIX #2) ===
    # Start from a base and add/subtract based on indicator strength
    confidence = 50  # Base
    
    # Alpha contribution (magnitude matters, not just sign)
    # Alpha > 0.2 is excellent, Alpha 0-0.05 is marginal
    alpha_contribution = min(abs(alpha) * 80, 20)  # Up to +20 points
    
    # VWAP distance (how far above/below VWAP)
    vwap_pct = ((current_price - vwap) / vwap) * 100 if vwap > 0 else 0
    vwap_contribution = min(abs(vwap_pct) * 2, 10)  # Up to +10 points
    
    # EMA 20 trend strength
    ema_pct = ((current_price - ema_20) / ema_20) * 100 if ema_20 > 0 else 0
    ema_contribution = min(abs(ema_pct), 5)  # Up to +5 points
    
    # Market bias
    market_contribution = 5  # Neutral adds 5
    if is_market_bearish:
        market_contribution = -5
    
    # ML prediction direction (FIX #3)
    ml_contribution = 0
    if ml_bullish: ml_contribution = 10
    elif ml_bearish: ml_contribution = -10
    
    # Signal Logic
    signal = "WAIT"
    
    # BUY Logic:
    # - Positive Alpha (Outperformer)
    # - Price > VWAP (Institutional Support)
    # - Price > EMA 20 (Trend Up)
    # - Market Not Bearish
    if has_alpha and institutional_buying and short_term_trend_up and not is_market_bearish:
        signal = "BUY"
        confidence = 50 + alpha_contribution + vwap_contribution + ema_contribution + market_contribution + ml_contribution
        if alpha > 0.2 and confidence >= 80:
            signal = "STRONG BUY"  # FIX #11: Use space, not underscore
    
    # SELL Logic:
    elif not has_alpha and not institutional_buying and not short_term_trend_up:
        signal = "SELL"
        confidence = 50 + alpha_contribution + vwap_contribution + ema_contribution + abs(ml_contribution)
        if alpha < -0.2 and confidence >= 80:
            signal = "STRONG SELL"  # FIX #11: Consistent format
            
    # Clamp confidence to [0, 100]
    confidence = max(0, min(100, confidence))
    
    # Stop Loss & Target
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
        "Predicted_Price": round(predicted_price, 2),
        "Alpha": round(alpha, 4),
        "Beta": round(beta, 2),
        "VWAP": round(vwap, 2),
        "Confidence": confidence,
        "Stop_Loss": round(stop_loss, 2),
        "Target": round(target, 2),
        "Market_Bias": market_mood.get('Market_Bias')
    }
