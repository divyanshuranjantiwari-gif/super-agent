import yfinance as yf
from textblob import TextBlob
from utils import logger

def get_sentiment_score(ticker):
    """
    FIX #7: Replaced broken Google News scraper with yfinance news API.
    Uses yfinance Ticker.news for headlines and TextBlob for sentiment.
    Returns the score (-1 to 1) and a list of headlines.
    """
    headlines = []
    score = 0
    
    try:
        # Clean ticker for yfinance (works with both .NS and .BO)
        t = yf.Ticker(ticker)
        news = t.news
        
        if not news:
            return 0, []
        
        polarity_sum = 0
        count = 0
        
        for item in news[:8]:  # Analyze up to 8 recent headlines
            title = item.get('title', '')
            if title:
                headlines.append(title)
                blob = TextBlob(title)
                polarity_sum += blob.sentiment.polarity
                count += 1
        
        if count > 0:
            score = polarity_sum / count
        
    except Exception as e:
        logger.error(f"Sentiment check failed for {ticker}: {e}")
        return 0, []

    return score, headlines
