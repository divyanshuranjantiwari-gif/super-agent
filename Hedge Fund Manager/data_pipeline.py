import yfinance as yf
from nsepython import *
import pandas as pd
import time

def get_market_mood():
    """
    Fetches FII/DII activity and determines market bias.
    Returns a dictionary with FII/DII net flows and market bias.
    """
    try:
        # Fetch FII/DII data
        # Note: nse_fii_dii() returns a list of dictionaries or similar structure
        # We will try to parse it robustly
        try:
            fii_dii = nse_fii_dii()
        except NameError:
            fii_dii = []
        
        fii_net = 0
        dii_net = 0
        
        # Example structure handling
        if isinstance(fii_dii, list):
            for item in fii_dii:
                category = item.get('category', '')
                net_value = float(item.get('netValue', 0))
                if "FII" in category or "FPI" in category:
                    fii_net += net_value
                elif "DII" in category:
                    dii_net += net_value
        
        market_bias = "NEUTRAL"
        if fii_net < -1000:
            market_bias = "BEARISH"
        elif fii_net > 1000:
            market_bias = "BULLISH"
            
        return {
            "FII_Net": fii_net,
            "DII_Net": dii_net,
            "Market_Bias": market_bias
        }
    except Exception as e:
        print(f"Error in get_market_mood: {e}")
        return {"FII_Net": 0, "DII_Net": 0, "Market_Bias": "NEUTRAL"}

def get_option_chain_analysis(symbol="NIFTY"):
    """
    Fetches Option Chain data and calculates PCR and Max Pain.
    """
    try:
        # nse_optionchain_scrapper returns a large JSON
        payload = nse_optionchain_scrapper(symbol)
        
        if not payload or 'filtered' not in payload:
            return {"PCR": 1.0, "Max_Pain": 0, "Support": "NEUTRAL"}
            
        # PCR Calculation
        ce_oi = payload['filtered']['CE']['totOI']
        pe_oi = payload['filtered']['PE']['totOI']
        pcr = pe_oi / ce_oi if ce_oi > 0 else 0
        
        # Max Pain (Strike with highest Total OI)
        max_oi = 0
        max_pain_strike = 0
        
        for data in payload['records']['data']:
            strike = data['strikePrice']
            ce_oi_strike = data.get('CE', {}).get('openInterest', 0)
            pe_oi_strike = data.get('PE', {}).get('openInterest', 0)
            total_oi = ce_oi_strike + pe_oi_strike
            
            if total_oi > max_oi:
                max_oi = total_oi
                max_pain_strike = strike
        
        support_status = "NEUTRAL"
        if pcr > 1.2:
            support_status = "BULLISH_SUPPORT"
        elif pcr < 0.7:
            support_status = "BEARISH_RESISTANCE"
            
        return {
            "PCR": round(pcr, 2),
            "Max_Pain": max_pain_strike,
            "Support_Status": support_status
        }
        
    except Exception as e:
        print(f"Error in get_option_chain_analysis for {symbol}: {e}")
        return {"PCR": 1.0, "Max_Pain": 0, "Support_Status": "NEUTRAL"}

def get_historical_data(tickers, period="2y"):
    """
    Fetches 2 years of historical data for the given tickers.
    """
    try:
        # Download data
        # group_by='ticker' ensures we get a MultiIndex if multiple tickers
        data = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, progress=False)
        return data
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return pd.DataFrame()

def get_news_sentiment(ticker):
    """
    Fetches news for a ticker and calculates sentiment score.
    Returns: score (-1 to 1)
    """
    try:
        # yfinance Ticker object
        t = yf.Ticker(ticker)
        news = t.news
        
        if not news:
            return 0
            
        sentiment_sum = 0
        count = 0
        
        from textblob import TextBlob
        
        for item in news:
            title = item.get('title', '')
            if title:
                blob = TextBlob(title)
                sentiment_sum += blob.sentiment.polarity
                count += 1
                
        if count == 0:
            return 0
            
        return sentiment_sum / count
        
    except Exception as e:
        # print(f"Error fetching news for {ticker}: {e}")
        return 0

if __name__ == "__main__":
    # Test the functions
    print("Testing Market Mood...")
    print(get_market_mood())
    
    print("\nTesting Option Chain (NIFTY)...")
    print(get_option_chain_analysis("NIFTY"))
