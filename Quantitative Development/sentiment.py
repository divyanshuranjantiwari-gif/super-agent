import yfinance as yf
from utils import logger
import sys
import os

# Import the financial sentiment lexicon
# It lives in super_agent/ directory, but this file runs from Quantitative Development/
# When called via wrapper, the wrapper handles paths.
# For standalone, we add the path.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LEXICON_PATH = os.path.join(PROJECT_ROOT, "super_agent")
if LEXICON_PATH not in sys.path:
    sys.path.insert(0, LEXICON_PATH)

try:
    from finance_sentiment import analyze_headlines
    USE_LEXICON = True
except ImportError:
    USE_LEXICON = False

def get_sentiment_score(ticker):
    """
    Fetches news for a ticker and calculates sentiment using the financial lexicon.
    Falls back to basic polarity if lexicon is unavailable.
    Returns the score (-1 to 1) and a list of headlines.
    """
    headlines = []
    score = 0
    
    try:
        t = yf.Ticker(ticker)
        news = t.news
        
        if not news:
            return 0, []
        
        for item in news[:8]:
            title = item.get('title', '')
            if title:
                headlines.append(title)
        
        if not headlines:
            return 0, []
        
        if USE_LEXICON:
            # Use our domain-specific financial sentiment analyzer
            score = analyze_headlines(headlines)
        else:
            # Fallback to TextBlob
            from textblob import TextBlob
            polarity_sum = 0
            for h in headlines:
                blob = TextBlob(h)
                polarity_sum += blob.sentiment.polarity
            score = polarity_sum / len(headlines)
        
    except Exception as e:
        logger.error(f"Sentiment check failed for {ticker}: {e}")
        return 0, []

    return score, headlines
