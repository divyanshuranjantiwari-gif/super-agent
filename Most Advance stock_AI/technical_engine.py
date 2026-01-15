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
        """
        if df is None:
            file_path = os.path.join(OHLCV_DIR, f"{symbol}.csv")
            if not os.path.exists(file_path):
                print(f"No data found for {symbol}")
                return {"score": 0, "signals": {}}
            df = pd.read_csv(file_path)
        
        if df.empty:
             return {"score": 0, "signals": {}}

        # Ensure we have enough data
        if len(df) < 50:
             return {"score": 0, "signals": {}}

        # Calculate Indicators
        try:
            # RSI
            df['rsi'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
            
            # MACD
            macd = ta.trend.MACD(close=df['Close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
            df['bb_high'] = bb.bollinger_hband()
            df['bb_low'] = bb.bollinger_lband()
            
            # SMA
            df['sma_50'] = ta.trend.SMAIndicator(close=df['Close'], window=50).sma_indicator()
            df['sma_200'] = ta.trend.SMAIndicator(close=df['Close'], window=200).sma_indicator()
            
            # ATR
            df['atr'] = ta.volatility.AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14).average_true_range()
            
            # ADX
            df['adx'] = ta.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14).adx()
            
            # RVOL
            df['vol_avg'] = df['Volume'].rolling(window=20).mean()
            df['rvol'] = df['Volume'] / df['vol_avg'].replace(0, 1)

            # Get latest values
            latest = df.iloc[-1]
            
            signals = {
                "rsi": latest['rsi'],
                "macd_bullish": latest['macd_diff'] > 0,
                "above_sma_50": latest['Close'] > latest['sma_50'] if not pd.isna(latest['sma_50']) else False,
                "above_sma_200": latest['Close'] > latest['sma_200'] if not pd.isna(latest['sma_200']) else False,
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
        Calculates a technical score (0-100).
        """
        score = 50
        
        # RSI
        rsi = signals['rsi']
        if 30 < rsi < 70:
            score += 5 # Neutral-ish but healthy
        elif rsi <= 30:
            score += 15 # Oversold (Buy signal potential)
        elif rsi >= 70:
            score -= 10 # Overbought (Sell signal potential)
            
        # MACD
        if signals['macd_bullish']:
            score += 10
        else:
            score -= 10
            
        # Trends
        if signals['above_sma_50']:
            score += 10
        else:
            score -= 10
            
        if signals['above_sma_200']:
            score += 15 # Long term trend
        else:
            score -= 15
            
        return max(0, min(100, score))

if __name__ == "__main__":
    # Mock DF for testing if needed, or rely on file existence
    pass
