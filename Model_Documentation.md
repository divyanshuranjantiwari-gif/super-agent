# Super Agent Model Documentation

This document provides a detailed technical breakdown of the four proprietary models powering the Super Agent.

---

## 1. Hedge Fund Manager (HFM 2.0)
**Philosophy**: Institutional Flow & Alpha Generation.
This model mimics the decision-making process of a hedge fund manager, focusing on "Smart Money" flow and risk-adjusted returns (Alpha). It ignores retail noise and looks for institutional footprints.

### Key Indicators
1.  **Alpha (α)**: Measures the stock's excess return relative to the benchmark (Nifty 50).
    *   *Calculation*: `Stock Return - (Beta * Benchmark Return)`
    *   *Logic*: Positive Alpha means the stock is outperforming the market due to intrinsic strength.
2.  **Beta (β)**: Measures volatility relative to the market.
    *   *Logic*: Beta > 1 implies high volatility; Beta < 1 implies stability.
3.  **VWAP (Volume Weighted Average Price)**: The average price paid by all traders, weighted by volume.
    *   *Calculation*: Rolling 20-Day VWAP (proxy for monthly institutional cost basis).
    *   *Logic*: If Price > VWAP, institutions are in profit and likely defending the trend.
4.  **Volume Shock**: Detects sudden spikes in volume (>1.5x of 20-day average).

### Signal Logic
*   **BUY Signal**:
    *   **Alpha > 0** (Stock is beating the market)
    *   **Price > VWAP** (Institutions are net buyers)
    *   **Price > EMA 20** (Short-term trend is UP)
    *   **Market Bias != Bearish** (Don't fight the overall market)
*   **SELL Signal**:
    *   **Alpha < 0** (Stock is lagging)
    *   **Price < VWAP** (Institutions are net sellers)
    *   **Price < EMA 20** (Short-term trend is DOWN)

---

## 2. Most Advanced Stock AI (StockAI)
**Philosophy**: Machine Learning Ensemble.
This model uses a weighted scoring system that combines technical analysis with fundamental data (where available) to generate a probabilistic confidence score (0-100).

### Key Indicators
1.  **RSI (Relative Strength Index)**: Momentum oscillator.
    *   *Logic*: Penalizes Overbought (>70), Rewards Oversold (<30) or Healthy Trend (40-60).
2.  **MACD (Moving Average Convergence Divergence)**: Trend-following momentum.
    *   *Logic*: Bullish Crossover (MACD Line > Signal Line) adds to the score.
3.  **Bollinger Bands**: Volatility envelopes.
    *   *Logic*: Measures where price is relative to the bands (Low/High).
4.  **Golden Cross**:
    *   *Logic*: SMA 50 > SMA 200 indicates a long-term bull market.

### Scoring Logic
*   **Technical Score (60% Weight)**: Aggregated score from RSI, MACD, BB, and SMA.
*   **Fundamental Score (40% Weight)**: Derived from financial metrics (P/E, EPS Growth).
*   **Final Output**:
    *   **Score > 70**: BUY
    *   **Score < 30**: SELL
    *   **Score 30-70**: WAIT/HOLD

---

## 3. Quantitative Development (Quant)
**Philosophy**: Statistical Probability & Multi-Factor Scoring.
A rigorous quantitative model that assigns a "Final Score" (0-10) based on three distinct pillars: Fundamentals, Technicals, and Sentiment.

### Key Pillars
1.  **Technical (50% Weight)**:
    *   SMA 50 vs SMA 200 (Trend)
    *   RSI (Momentum)
    *   Bollinger Band Position (Volatility)
    *   MACD Crossover (Signal)
2.  **Fundamental (30% Weight)**:
    *   Evaluates Valuation (P/E), Profitability (ROE), and Growth.
3.  **Sentiment (20% Weight)**:
    *   Analyzes recent news headlines using NLP (Natural Language Processing) to determine if news flow is Positive or Negative.

### Signal Logic
*   **Final Score Calculation**: `(Tech * 0.5) + (Fund * 0.3) + (Sent * 0.2)`
*   **Intraday Filter**: Checks 15-minute VWAP for precise entry timing.
*   **Action**:
    *   **Score > 7**: STRONG BUY (High Conviction)
    *   **Score > 5**: WATCH (Potential Setup)
    *   **Score < 4**: AVOID

---

## 4. Apex Logic
**Philosophy**: Pure Price Action (Trend + Momentum + Volume).
The "Sniper" model. It ignores fundamentals and news, focusing purely on price structure and volume confirmation to catch explosive moves.

### Key Indicators
1.  **Trend Alignment (40% Impact)**:
    *   Checks if `Price > EMA 50 > EMA 200`. This is the "Perfect Alignment" for a bull run.
2.  **Momentum Burst (30% Impact)**:
    *   Requires `RSI > 55` (Strong Momentum) AND `MACD > Signal` (Bullish).
3.  **Volume Confirmation (30% Impact)**:
    *   Requires Current Volume > 20-Day Average Volume. This confirms that "Big Players" are participating.

### Signal Logic
*   **Score Range**: -1.0 to +1.0
*   **STRONG BUY**: Score >= 0.6 (All three conditions met: Trend + Momentum + Volume).
*   **BUY**: Score > 0.2 (Trend + Momentum, but low volume).
*   **SELL**: Score < -0.2 (Trend broken).

---

## Summary Table

| Feature | HFM 2.0 | StockAI | Quant | Apex Logic |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Focus** | Institutional Flow | Machine Learning | Multi-Factor Stats | Price Action |
| **Key Metric** | Alpha & VWAP | Probabilistic Score | Weighted Final Score | Trend Alignment |
| **Time Horizon** | Swing / Positional | Swing | Swing / Intraday | Swing / Momentum |
| **Unique Edge** | Detects "Smart Money" | Balances Tech & Fund | Includes News Sentiment | Volume Confirmation |
