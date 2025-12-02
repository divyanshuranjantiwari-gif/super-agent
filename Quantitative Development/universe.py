import yfinance as yf
import pandas as pd
import requests
import io
import os
from utils import logger

def get_bse_tickers():
    """
    Returns a list of BSE tickers.
    Attempts to load 'bse500.csv' locally, or download Nifty 500 list from GitHub 
    and convert to BSE tickers (.BO), or falls back to a hardcoded list.
    """
    tickers = []
    
    # 1. Try local file
    if os.path.exists("bse500.csv"):
        try:
            df = pd.read_csv("bse500.csv")
            if 'Symbol' in df.columns:
                tickers = [f"{s}.BO" for s in df['Symbol'].tolist()]
                logger.info(f"Loaded {len(tickers)} tickers from local bse500.csv")
                return tickers
        except Exception as e:
            logger.error(f"Failed to read local bse500.csv: {e}")

    # 2. Try downloading Nifty 500 list (Proxy for BSE 500)
    url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv"
    try:
        logger.info("Downloading Nifty 500 list from GitHub...")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            if 'Symbol' in df.columns:
                # Convert to BSE tickers
                tickers = [f"{s}.BO" for s in df['Symbol'].tolist()]
                logger.info(f"Fetched {len(tickers)} tickers from GitHub.")
                return tickers
    except Exception as e:
        logger.error(f"Failed to download ticker list: {e}")

    # 3. Fallback to hardcoded list
    logger.warning("Using hardcoded fallback list.")
    tickers = [
        "RELIANCE.BO", "TCS.BO", "HDFCBANK.BO", "INFY.BO", "ICICIBANK.BO",
        "HINDUNILVR.BO", "SBIN.BO", "BHARTIARTL.BO", "ITC.BO", "KOTAKBANK.BO",
        "LICI.BO", "LT.BO", "AXISBANK.BO", "HCLTECH.BO", "ASIANPAINT.BO",
        "MARUTI.BO", "SUNPHARMA.BO", "TITAN.BO", "BAJFINANCE.BO", "ULTRACEMCO.BO",
        "NTPC.BO", "ONGC.BO", "TATASTEEL.BO", "POWERGRID.BO", "M&M.BO",
        "ADANIENT.BO", "ADANIPORTS.BO", "COALINDIA.BO", "WIPRO.BO", "JSWSTEEL.BO",
        "BAJAJFINSV.BO", "NESTLEIND.BO", "BPCL.BO", "GRASIM.BO", "TECHM.BO",
        "HINDALCO.BO", "EICHERMOT.BO", "CIPLA.BO", "TATACONSUM.BO", "DRREDDY.BO",
        "BRITANNIA.BO", "SBILIFE.BO", "APOLLOHOSP.BO", "DIVISLAB.BO", "INDUSINDBK.BO",
        "TATAMOTORS.BO", "HEROMOTOCO.BO", "UPL.BO", "SHREECEM.BO", "BAJAJ-AUTO.BO"
    ]
    return tickers

def filter_liquid_stocks(tickers):
    """
    Filters stocks based on Price > 50 and Volume > 100,000.
    Returns a list of valid tickers.
    """
    valid_tickers = []
    logger.info(f"Filtering {len(tickers)} stocks for liquidity...")
    
    # Process in batches of 50 to avoid overwhelming yfinance or getting rate limited
    batch_size = 50
    
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1}...")
        
        try:
            # Download last 5 days
            data = yf.download(batch, period="5d", group_by='ticker', threads=True, progress=False)
            
            if data.empty:
                continue
                
            for ticker in batch:
                try:
                    if len(batch) > 1:
                        if ticker not in data.columns.levels[0]:
                             continue
                        df = data[ticker]
                    else:
                        df = data
                    
                    if df.empty:
                        continue
                    
                    # Check criteria
                    # Handle potential missing data
                    if 'Close' not in df.columns or 'Volume' not in df.columns:
                        continue
                        
                    last_price = df['Close'].iloc[-1]
                    avg_volume = df['Volume'].mean()
                    
                    # Ensure scalar
                    if isinstance(last_price, pd.Series): last_price = last_price.iloc[0]
                    if isinstance(avg_volume, pd.Series): avg_volume = avg_volume.iloc[0]

                    if last_price > 50 and avg_volume > 100000:
                        valid_tickers.append(ticker)
                        
                except Exception as e:
                    # logger.debug(f"Error checking {ticker}: {e}")
                    pass
                    
        except Exception as e:
            logger.error(f"Batch download failed: {e}")
            
    logger.info(f"Universe filtered down to {len(valid_tickers)} stocks.")
    return valid_tickers
