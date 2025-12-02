import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from utils import logger
import time
import random

def get_sentiment_score(ticker):
    """
    Scrapes Google News for the ticker and calculates a sentiment score (-1 to 1).
    Returns the score and a list of headlines.
    """
    # Clean ticker for search (remove .BO)
    search_term = ticker.replace('.BO', '') + " stock news India"
    url = f"https://www.google.com/search?q={search_term}&tbm=nws"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    headlines = []
    score = 0
    
    try:
        # Add a small random delay to avoid rate limiting if calling in loop
        time.sleep(random.uniform(0.5, 1.5))
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Google News classes change often. 
        # Common classes: 'n0jPhd' (headline), 'GI74Re' (snippet)
        # We'll try to find div classes that look like headlines.
        # A robust way is to look for specific heading tags or classes.
        # As of late 2023/2024, 'n0jPhd' is common for the main link text in news tab.
        
        # Try multiple selectors
        items = soup.find_all('div', class_='n0jPhd')
        if not items:
            items = soup.find_all('div', role='heading')
            
        for item in items[:5]: # Analyze top 5 headlines
            text = item.get_text()
            headlines.append(text)
            
        if not headlines:
            # Fallback: try finding all 'a' tags with some length in main div
            # This is a bit "spray and pray" but better than nothing if class names changed
            pass

        if headlines:
            polarity_sum = 0
            for h in headlines:
                blob = TextBlob(h)
                polarity_sum += blob.sentiment.polarity
            
            avg_polarity = polarity_sum / len(headlines)
            score = avg_polarity
            
            # Log sentiment
            # logger.info(f"Sentiment for {ticker}: {score:.2f} based on {len(headlines)} headlines.")
        else:
            # logger.warning(f"No headlines found for {ticker}")
            score = 0 # Neutral if no news

    except Exception as e:
        logger.error(f"Sentiment check failed for {ticker}: {e}")
        return 0, []

    return score, headlines
