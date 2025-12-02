import pandas as pd
from universe import get_bse_tickers, filter_liquid_stocks
from fundamental import get_fundamental_score
from technical import get_technical_indicators, check_intraday_vwap
from sentiment import get_sentiment_score
from utils import logger
import sys

def main():
    logger.info("Starting BSE-Alpha-Agent...")
    
    # Phase 1: Universe
    all_tickers = get_bse_tickers()
    liquid_tickers = filter_liquid_stocks(all_tickers)
    
    if not liquid_tickers:
        logger.error("No liquid stocks found. Exiting.")
        sys.exit(1)
        
    results = []
    
    logger.info(f"Analyzing {len(liquid_tickers)} stocks...")
    
    for ticker in liquid_tickers:
        logger.info(f"Processing {ticker}...")
        
        # Phase 2: Fundamental
        fund_score, fund_details = get_fundamental_score(ticker)
        
        # Phase 3: Technical
        tech_score, tech_signals = get_technical_indicators(ticker)
        
        # Phase 4: Sentiment
        sent_score, headlines = get_sentiment_score(ticker)
        
        # Logic: If Sentiment is Negative (< -0.2), disqualify
        if sent_score < -0.2:
            logger.info(f"Skipping {ticker} due to negative sentiment: {sent_score:.2f}")
            continue
            
        # Phase 5: Alpha Rank
        # Normalize Sentiment (-1 to 1) to (0 to 10) for consistent weighting?
        # Prompt says: FinalScore = (Fundamental * 0.3) + (Technical * 0.5) + (Sentiment * 0.2)
        # Fundamental is 0-10. Technical is 0-10. Sentiment is -1 to 1.
        # We should probably map Sentiment to 0-10 or just use it as a multiplier/filter.
        # Let's map -1 to 1 -> 0 to 10. 
        # (-1 -> 0, 0 -> 5, 1 -> 10) => (sent + 1) * 5
        sent_score_normalized = (sent_score + 1) * 5
        
        final_score = (fund_score * 0.3) + (tech_score * 0.5) + (sent_score_normalized * 0.2)
        
        # Intraday Check
        # Only check if it's a good candidate (e.g. Final Score > 6)
        intraday_signal = False
        if final_score > 6:
            intraday_signal = check_intraday_vwap(ticker)
            
        # Determine Action
        action = "WAIT"
        if final_score > 7 and intraday_signal:
            action = "STRONG BUY"
        elif final_score > 7:
            action = "SWING BUY"
        elif final_score > 5:
            action = "WATCH"
            
        # Prepare Result Row
        atr = tech_signals.get('ATR', 0)
        close = tech_signals.get('Close', 0)
        stop_loss = close - (atr * 2) if atr else 0 # 2x ATR Stop
        target = close + (atr * 4) if atr else 0 # 2:1 Reward
        
        results.append({
            'Ticker': ticker,
            'Final Score': round(final_score, 2),
            'Action': action,
            'Close Price': round(close, 2),
            'Stop Loss': round(stop_loss, 2),
            'Target': round(target, 2),
            'Fund Score': fund_score,
            'Tech Score': tech_score,
            'Sent Score': round(sent_score, 2),
            'Intraday VWAP': intraday_signal,
            'Headlines': headlines[:1] # Just top headline
        })
        
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    if not df_results.empty:
        # Sort by Final Score
        df_results = df_results.sort_values(by='Final Score', ascending=False)
        
        # Save to CSV
        df_results.to_csv("BSE_Signals.csv", index=False)
        logger.info("Saved results to BSE_Signals.csv")
        
        # Print Dashboard
        print("\n=== Trade Signal Dashboard ===")
        print(df_results[['Ticker', 'Action', 'Final Score', 'Close Price', 'Stop Loss', 'Target']].head(10).to_string(index=False))
        print("==============================\n")
    else:
        logger.info("No results generated.")

if __name__ == "__main__":
    main()
