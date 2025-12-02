import argparse
from data_engine import DataEngine
from fundamental_engine import FundamentalEngine
from technical_engine import TechnicalEngine
from ml_engine import MLEngine
from strategy_engine import StrategyEngine
from reporting_engine import ReportingEngine
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description="BSE Alpha Agent - Advanced Stock Analysis")
    parser.add_argument("--update-data", action="store_true", help="Fetch fresh data for all symbols")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of stocks to analyze (for testing)")
    args = parser.parse_args()

    # 1. Initialize Engines
    data_engine = DataEngine()
    fund_engine = FundamentalEngine()
    tech_engine = TechnicalEngine()
    ml_engine = MLEngine()
    strat_engine = StrategyEngine()
    report_engine = ReportingEngine()

    # 2. Data Ingestion
    if args.update_data:
        data_engine.update_all_data()
    else:
        # Ensure we have symbols loaded
        if not data_engine.symbols:
            data_engine.fetch_bse_symbols()

    symbols = data_engine.symbols
    if args.limit > 0:
        symbols = symbols[:args.limit]

    print(f"Starting analysis for {len(symbols)} symbols...")
    
    analyzed_stocks = []

    # 3. Analysis Loop
    for symbol in tqdm(symbols):
        # Fetch Data
        df = data_engine.fetch_ohlcv(symbol)
        if df is None:
            continue
            
        # Fundamental Analysis
        fund_data = fund_engine.analyze(symbol)
        
        # Technical Analysis
        tech_data = tech_engine.analyze(symbol, df)
        
        if tech_data['score'] == 0 and fund_data['score'] == 0:
            continue

        # 4. ML & Ranking
        # Prepare features (conceptually)
        # features = ml_engine.prepare_features(tech_data, fund_data)
        
        # Combine data for strategy
        stock_data = {
            "symbol": symbol,
            "technical_score": tech_data['score'],
            "fundamental_score": fund_data['score'],
            "technical_signals": tech_data['signals'],
            "fundamental_metrics": fund_data['metrics'],
            "latest_price": tech_data.get('latest_price', 0)
        }
        
        analyzed_stocks.append(stock_data)

    # 5. Ranking
    ranked_stocks = ml_engine.rank_stocks(analyzed_stocks)

    # 6. Strategy Generation
    final_signals = []
    for stock in ranked_stocks:
        signal = strat_engine.generate_signals(stock)
        final_signals.append(signal)

    # 7. Reporting
    report_engine.generate_signals_csv(final_signals)
    
    # Export Top Lists (using the signals which contain the recommendation info)
    # We need to flatten the signal structure slightly for CSV export or just pass the list
    # The reporting engine expects a list of dicts, and our signals are exactly that.
    report_engine.export_reports(final_signals)

    print("\nAnalysis Complete. Check 'output' directory for results.")

if __name__ == "__main__":
    main()
