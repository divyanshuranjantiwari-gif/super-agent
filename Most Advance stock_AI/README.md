# BSE Alpha Agent

An advanced AI agent for researching and analyzing BSE-listed stocks.

## Features
- **Data Engine**: Fetches historical OHLCV and fundamental data from Yahoo Finance.
- **Analysis**: Combines Technical (RSI, MACD, BB, ATR) and Fundamental (PE, ROE, Growth) analysis.
- **Ranking**: Scores stocks based on a weighted confidence model.
- **Strategy**: Generates Buy/Sell/Hold signals with Entry, Stop Loss, and Targets.
- **Reporting**: Outputs structured JSON signals and CSV reports for Top Buys/Sells.

## Prerequisites
- Python 3.8+
- Internet connection

## Installation

1.  **Install Python**: If you haven't, download and install Python from [python.org](https://www.python.org/). Ensure you check "Add Python to PATH" during installation.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Update Data & Run Analysis
To fetch fresh data and run the full analysis:
```bash
python main.py --update-data
```

### 2. Run Analysis on Existing Data
If you already have data downloaded (in `data/` folder):
```bash
python main.py
```

### 3. Test with a few stocks
To run a quick test on top 5 stocks:
```bash
python main.py --update-data --limit 5
```

## Output
Results are saved in the `output/` directory:
- `signals.json`: Detailed analysis for all stocks.
- `top_buys.csv`: Top 20 Buy recommendations.
- `top_sells.csv`: Top 20 Sell recommendations.

## Disclaimer
This tool is for educational and research purposes only. Do not trade based solely on these signals.
