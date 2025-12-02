import os

# Data Directories
DATA_DIR = "data"
OHLCV_DIR = os.path.join(DATA_DIR, "ohlcv")
FUNDAMENTALS_DIR = os.path.join(DATA_DIR, "fundamentals")
OUTPUT_DIR = "output"

# Create directories if they don't exist
os.makedirs(OHLCV_DIR, exist_ok=True)
os.makedirs(FUNDAMENTALS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Analysis Settings
LOOKBACK_YEARS = 10
TIMEFRAMES = ["1d", "1wk", "1mo"] # yfinance free tier limitations for intraday
INTRADAY_INTERVAL = "5m" # For recent data

# Risk Management
DEFAULT_RISK_PER_TRADE = 0.01 # 1% of capital
DEFAULT_CAPITAL = 10000000 # 1 Crore

# BSE Suffix
EXCHANGE_SUFFIX = ".BO"
