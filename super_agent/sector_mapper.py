import yfinance as yf
import pandas as pd

# Mapping of major Indian stocks to their NSE Sector Indices
SECTOR_MAP = {
    # IT
    'TCS.NS': '^CNXIT', 'INFY.NS': '^CNXIT', 'WIPRO.NS': '^CNXIT', 'HCLTECH.NS': '^CNXIT', 'TECHM.NS': '^CNXIT',
    # Banking & Finance
    'HDFCBANK.NS': '^NSEBANK', 'ICICIBANK.NS': '^NSEBANK', 'SBIN.NS': '^NSEBANK', 'AXISBANK.NS': '^NSEBANK', 'KOTAKBANK.NS': '^NSEBANK',
    'BAJFINANCE.NS': '^CNXFIN', 'BAJAJFINSV.NS': '^CNXFIN',
    # Auto
    'TATAMOTORS.NS': '^CNXAUTO', 'M&M.NS': '^CNXAUTO', 'MARUTI.NS': '^CNXAUTO', 'BAJAJ-AUTO.NS': '^CNXAUTO', 'EICHERMOT.NS': '^CNXAUTO',
    # FMCG
    'ITC.NS': '^CNXFMCG', 'HUL.NS': '^CNXFMCG', 'NESTLEIND.NS': '^CNXFMCG', 'BRITANNIA.NS': '^CNXFMCG', 'TATACONSUM.NS': '^CNXFMCG',
    # Energy / Oil & Gas
    'RELIANCE.NS': '^CNXENERGY', 'ONGC.NS': '^CNXENERGY', 'NTPC.NS': '^CNXENERGY', 'POWERGRID.NS': '^CNXENERGY', 'COALINDIA.NS': '^CNXENERGY',
    # Pharma
    'SUNPHARMA.NS': '^CNXPHARMA', 'DRREDDY.NS': '^CNXPHARMA', 'CIPLA.NS': '^CNXPHARMA', 'DIVISLAB.NS': '^CNXPHARMA', 'APOLLOHOSP.NS': '^CNXPHARMA',
    # Metals
    'TATASTEEL.NS': '^CNXMETAL', 'HINDALCO.NS': '^CNXMETAL', 'JSWSTEEL.NS': '^CNXMETAL',
}

# Cache to avoid repeatedly downloading the same index
_trend_cache = {}

def get_sector_trend(ticker):
    """
    Returns the trend of the parent sector index for a given ticker.
    'UP' if above 20-day SMA, 'DOWN' if below.
    If sector is unknown, returns 'NEUTRAL'.
    """
    sector_index = SECTOR_MAP.get(ticker)
    
    if not sector_index:
        return 'NEUTRAL'
        
    if sector_index in _trend_cache:
        return _trend_cache[sector_index]
        
    try:
        data = yf.download(sector_index, period="3mo", interval="1d", progress=False)['Close']
        if data.empty or len(data) < 20:
            _trend_cache[sector_index] = 'NEUTRAL'
            return 'NEUTRAL'
            
        index_series = data[sector_index].dropna() if isinstance(data, pd.DataFrame) else data.dropna()
        sma20 = index_series.rolling(window=20).mean().iloc[-1]
        current_price = index_series.iloc[-1]
        
        trend = 'UP' if current_price > sma20 else 'DOWN'
        _trend_cache[sector_index] = trend
        return trend
        
    except Exception as e:
        print(f"[Sector Mapper] Error fetching {sector_index} for {ticker}: {e}")
        _trend_cache[sector_index] = 'NEUTRAL'
        return 'NEUTRAL'

if __name__ == "__main__":
    test_stocks = ['TCS.NS', 'HDFCBANK.NS', 'TATAMOTORS.NS', 'RELIANCE.NS', 'UNKNOWN.NS']
    for stock in test_stocks:
        print(f"{stock.ljust(15)} Sector Trend: {get_sector_trend(stock)}")
