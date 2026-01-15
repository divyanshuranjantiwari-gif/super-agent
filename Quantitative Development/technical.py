import ta
import yfinance as yf
import pandas as pd
from utils import logger

def get_technical_indicators(ticker, df=None):
    """
    Calculates technical indicators for 1-Day timeframe using 'ta' library.
    Returns a score (0-10) and a dictionary of signals.
    """
    score = 0
    signals = {}
    
    try:
        if df is None:
            # Fetch 1 year of data to ensure enough for 200 SMA
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        if df.empty or len(df) < 200:
            return 0, {"Error": "Insufficient Data"}
            
        # Flatten columns if MultiIndex (common in new yfinance)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Ensure Close is Series
        close_series = df['Close']
        high_series = df['High']
        low_series = df['Low']
        
        # 1. Trend: SMA_50 > SMA_200 (Golden Cross)
        sma_50 = ta.trend.sma_indicator(close_series, window=50)
        sma_200 = ta.trend.sma_indicator(close_series, window=200)
        
        if sma_50.iloc[-1] > sma_200.iloc[-1]:
            score += 2.5
            signals['Trend'] = "Bullish (SMA50 > SMA200)"
        else:
            signals['Trend'] = "Bearish"

        # 2. Momentum: RSI (14) between 30 and 70
        rsi = ta.momentum.rsi(close_series, window=14)
        current_rsi = rsi.iloc[-1]
        
        if 30 < current_rsi < 70:
            score += 2.5
            signals['Momentum'] = f"RSI {current_rsi:.2f} (Neutral/Bullish)"
        else:
            signals['Momentum'] = f"RSI {current_rsi:.2f} (Extreme)"

        # 3. Volatility: Bollinger Bands
        # ta.volatility.BollingerBands(close, window=20, window_dev=2)
        indicator_bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
        
        # Add Bollinger Bands features
        bb_mavg = indicator_bb.bollinger_mavg()
        # bb_hband = indicator_bb.bollinger_hband()
        # bb_lband = indicator_bb.bollinger_lband()
        
        current_close = close_series.iloc[-1]
        current_mid = bb_mavg.iloc[-1]
        
        if current_close > current_mid:
            score += 2.5
            signals['Volatility'] = "Price > BB Mid (Bullish)"
        else:
            signals['Volatility'] = "Price < BB Mid (Bearish)"

        # 4. MACD: Bullish Crossover
        # ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        indicator_macd = ta.trend.MACD(close=close_series, window_slow=26, window_fast=12, window_sign=9)
        
        macd_line = indicator_macd.macd()
        signal_line = indicator_macd.macd_signal()
        
        if macd_line.iloc[-1] > signal_line.iloc[-1]:
            score += 2.5
            signals['MACD'] = "Bullish Crossover"
        else:
            signals['MACD'] = "Bearish"

        # Store last close for stop loss calc
        signals['Close'] = current_close
        
        # Calculate ATR for Stop Loss
        indicator_atr = ta.volatility.AverageTrueRange(high=high_series, low=low_series, close=close_series, window=14)
        atr = indicator_atr.average_true_range()
        signals['ATR'] = atr.iloc[-1]
        
        # 5. ADX (Trend Strength)
        indicator_adx = ta.trend.ADXIndicator(high=high_series, low=low_series, close=close_series, window=14)
        signals['ADX'] = indicator_adx.adx().iloc[-1]
        
        # 6. RVOL (Institutional Volume)
        vol_series = df['Volume']
        vol_avg = vol_series.rolling(window=20).mean()
        # Handle div by zero if vol_avg is 0
        rvol_series = vol_series / vol_avg.replace(0, 1)
        signals['RVOL'] = rvol_series.iloc[-1]

    except Exception as e:
        logger.error(f"Technical check failed for {ticker}: {e}")
        return 0, {"Error": str(e)}

    return score, signals

def check_intraday_vwap(ticker):
    """
    Fetches 15-minute data and checks if Price > VWAP.
    Returns True/False.
    """
    try:
        # Fetch last 5 days to get enough intraday data, 15m interval
        df = yf.download(ticker, period="5d", interval="15m", progress=False)
        
        if df.empty:
            return False
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Calculate VWAP
        # ta.volume.VolumeWeightedAveragePrice(high, low, close, volume, window=14, fillna=False)
        # Note: 'ta' library VWAP is a rolling VWAP, not necessarily anchored to session start unless we handle it.
        # But for this scope, rolling VWAP or standard VWAP implementation is acceptable.
        # Actually ta.volume.VolumeWeightedAveragePrice is a class.
        
        vwap_indicator = ta.volume.VolumeWeightedAveragePrice(
            high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'], window=14
        )
        vwap = vwap_indicator.volume_weighted_average_price()
        
        current_vwap = vwap.iloc[-1]
        current_close = df['Close'].iloc[-1]
        
        return current_close > current_vwap
        
    except Exception as e:
        logger.error(f"Intraday VWAP check failed for {ticker}: {e}")
        return False
