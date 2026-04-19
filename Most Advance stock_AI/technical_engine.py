import pandas as pd
import ta
from config import OHLCV_DIR
import os

class TechnicalEngine:
    def __init__(self):
        pass

    def analyze(self, symbol, df=None):
        """
        Analyzes technical indicators for a given symbol.
        If df is provided, uses it. Otherwise loads from CSV.
        FIX #5: Redesigned scoring — proper weight distribution for swing trading.
        """
        if df is None:
            file_path = os.path.join(OHLCV_DIR, f"{symbol}.csv")
            if not os.path.exists(file_path):
                print(f"No data found for {symbol}")
                return {"score": 0, "signals": {}}
            df = pd.read_csv(file_path)
        
        if df.empty:
             return {"score": 0, "signals": {}}

        if len(df) < 50:
             return {"score": 0, "signals": {}}

        # Avoid SettingWithCopyWarning when working with slices
        df = df.copy()

        try:
            # Calculate Indicators
            df['rsi'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
            
            macd = ta.trend.MACD(close=df['Close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
            df['bb_high'] = bb.bollinger_hband()
            df['bb_low'] = bb.bollinger_lband()
            
            df['sma_50'] = ta.trend.SMAIndicator(close=df['Close'], window=50).sma_indicator()
            df['sma_200'] = ta.trend.SMAIndicator(close=df['Close'], window=200).sma_indicator()
            
            df['atr'] = ta.volatility.AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14).average_true_range()
            
            df['adx'] = ta.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14).adx()
            
            df['vol_avg'] = df['Volume'].rolling(window=20).mean()
            df['rvol'] = df['Volume'] / df['vol_avg'].replace(0, 1)

            # EMA for trend confirmation
            df['ema_20'] = ta.trend.EMAIndicator(close=df['Close'], window=20).ema_indicator()

            latest = df.iloc[-1]
            
            signals = {
                "rsi": latest['rsi'],
                "macd_bullish": latest['macd_diff'] > 0,
                "macd_crossover_fresh": (df['macd_diff'].iloc[-1] > 0 and df['macd_diff'].iloc[-2] <= 0) if len(df) > 1 else False,
                "above_sma_50": latest['Close'] > latest['sma_50'] if not pd.isna(latest['sma_50']) else False,
                "above_sma_200": latest['Close'] > latest['sma_200'] if not pd.isna(latest['sma_200']) else False,
                "above_ema_20": latest['Close'] > latest['ema_20'] if not pd.isna(latest['ema_20']) else False,
                "bb_position": (latest['Close'] - latest['bb_low']) / (latest['bb_high'] - latest['bb_low']) if (latest['bb_high'] - latest['bb_low']) != 0 else 0.5,
                "atr": latest['atr'],
                "adx": latest['adx'],
                "rvol": latest['rvol']
            }
            
            score = self.calculate_score(signals)
            
            return {
                "score": score,
                "signals": signals,
                "latest_price": latest['Close']
            }
            
        except Exception as e:
            print(f"Error in technical analysis for {symbol}: {e}")
            return {"score": 0, "signals": {}}

    def calculate_score(self, signals):
        """
        FIX #5: Redesigned scoring for swing trading.
        Score range: 0-100 starting from 0, not 50.
        Properly weights trend, momentum, and confirmation.
        """
        score = 0
        
        # === TREND (Max 40 points) ===
        # Golden Cross: SMA 50 > SMA 200 (strongest trend signal)
        if signals['above_sma_200']:
            score += 20  # Long-term uptrend
        
        if signals['above_sma_50']:
            score += 10  # Mid-term uptrend
        
        if signals['above_ema_20']:
            score += 10  # Short-term momentum
        
        # === MOMENTUM (Max 30 points) ===
        rsi = signals['rsi']
        if 40 <= rsi <= 65:
            score += 15  # Healthy momentum zone for swing (not overbought)
        elif 30 < rsi < 40:
            score += 10  # Recovery zone — potential buy
        elif rsi <= 30:
            score += 5   # Oversold — risky reversal bet
        elif 65 < rsi <= 75:
            score += 8   # Strong but getting extended
        # RSI > 75: +0 (overbought, no credit)
        
        if signals['macd_bullish']:
            score += 10  # MACD confirms bullish
            if signals.get('macd_crossover_fresh', False):
                score += 5   # Fresh crossover = extra conviction
        
        # === TREND STRENGTH (Max 15 points) ===
        adx = signals.get('adx', 0)
        if not pd.isna(adx):
            if adx > 30:
                score += 15  # Strong trend
            elif adx > 25:
                score += 10  # Moderate trend
            elif adx > 20:
                score += 5   # Weak trend
            # ADX < 20: +0 (no trend, choppy)
        
        # === VOLUME CONFIRMATION (Max 15 points) ===
        rvol = signals.get('rvol', 0)
        if not pd.isna(rvol):
            if rvol > 2.0:
                score += 15  # Very high volume (institutional)
            elif rvol > 1.5:
                score += 10  # Above average
            elif rvol > 1.0:
                score += 5   # Normal
        
        return max(0, min(100, score))

if __name__ == "__main__":
    pass
