import pandas as pd
from config import NIFTY_50, SENSEX_30
from data_pipeline import get_market_mood, get_option_chain_analysis, get_historical_data, get_news_sentiment
from features import add_technical_indicators, add_relative_strength, calculate_vwap, calculate_alpha_beta
from model import train_predict_model
from strategy import generate_signal
from reporting import generate_html_report
import time
import os

def main():
    print("Starting Hedge Fund Trading Engine (HFM 2.0)...")
    
    # 1. Market Mood
    print("Fetching Market Mood...")
    market_mood = get_market_mood()
    print(f"Market Bias: {market_mood['Market_Bias']} (FII Net: {market_mood['FII_Net']}, DII Net: {market_mood['DII_Net']})")
    
    # 2. Option Chain
    print("Analyzing Option Chain...")
    option_data = get_option_chain_analysis("NIFTY")
    print(f"PCR: {option_data['PCR']}, Max Pain: {option_data['Max_Pain']}, Support: {option_data['Support_Status']}")
    
    # 3. Stock Universe
    tickers = list(set(NIFTY_50 + SENSEX_30))
    # tickers = tickers[:10] # Uncomment for quick testing
    
    print(f"Fetching data for {len(tickers)} stocks...")
    hist_data = get_historical_data(tickers, period="2y")
    
    # Fetch Nifty data for Relative Strength & Alpha
    print("Fetching Nifty data...")
    nifty_data = get_historical_data(["^NSEI"], period="2y")
    if not nifty_data.empty and isinstance(nifty_data.columns, pd.MultiIndex):
         nifty_data = nifty_data["^NSEI"]
    
    signals = []
    
    print("Processing stocks...")
    for i, ticker in enumerate(tickers):
        print(f"[{i+1}/{len(tickers)}] Processing {ticker}...", end="\r")
        try:
            # Extract stock data
            if isinstance(hist_data.columns, pd.MultiIndex):
                if ticker not in hist_data.columns.levels[0]:
                    continue
                df = hist_data[ticker].copy()
            else:
                if hist_data.empty: continue
                df = hist_data.copy()
            
            if df.empty:
                continue
                
            # Feature Engineering
            df = add_technical_indicators(df)
            df = add_relative_strength(df, nifty_data)
            
            # HFM 2.0 Calculations
            df = calculate_vwap(df)
            df = calculate_alpha_beta(df, nifty_data)
            
            # AI Prediction (Kept as confidence booster)
            predicted_price, model_score = train_predict_model(df)
            
            if predicted_price is None:
                predicted_price = df['Close'].iloc[-1]
                
            # Sentiment
            sentiment_score = get_news_sentiment(ticker)
            
            # Generate Signal (HFM 2.0)
            # Pass the full last row which contains Alpha, Beta, VWAP, EMA_20
            current_row = df.iloc[-1]
            
            signal = generate_signal(
                ticker, 
                current_row, 
                predicted_price, 
                market_mood, 
                option_data, 
                sentiment_score
            )
            
            signals.append(signal)
            
        except Exception as e:
            # print(f"Error processing {ticker}: {e}")
            continue
            
    print("\nGenerating Report...")
    report_path = generate_html_report(signals)
    print(f"Report generated at: {os.path.abspath(report_path)}")

if __name__ == "__main__":
    main()
