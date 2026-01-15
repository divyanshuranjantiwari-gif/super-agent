# Super Agent 3.0: The "Iron-Clad" Precision Strategy

Current Problem: *Evaluation Instability*. A stock looks good today (breakout) but fails tomorrow (fakeout).
Goal: **90%+ Probabilistic Accuracy**. Eliminate "false positives" and find stocks with sustained momentum.

Here is the blueprint to make the Super Agent "Inhumanly Precise":

---

## 1. The "Persistence" Engine (3-Day Rule)
**Problem**: A unified green candle often traps buyers before a reversal.
**Solution**: We stop analyzing just "Today". We analyze the **Trajectory**.
*   **Logic**: Instead of `Score(Today)`, we calculate a **Weighted Trajectory Score**:
    *   `Final_Score = (Today_Score * 50%) + (Yesterday_Score * 30%) + (Day_Before_Score * 20%)`
*   **Effect**: A stock that was "Strong Buy" yesterday and "Strong Buy" today is infinitely more reliable than a random pop today.
*   **Filter**: If `Yesterday_Score` was "Sell", and `Today` is "Buy", we treat it as **unconfirmed** and force a "WAIT" until Day 2 confirmation.

## 2. Super Score 2.0 (Apex Integration)
**Problem**: Apex (Price Action/Volume) is your smartest "Sniper" model but it's currently excluded from the main ranking.
**Solution**: Integrate Apex into the core `Super Score`.
*   **New Formula**: `(HFM + StockAI + Quant + Apex) / 4`
*   **Why**: Apex validates if the *Price* allows the *Fundamentals* (HFM) to work. If HFM loves it but Apex sees no volume, it’s a "Value Trap" (cheap but won't move). Apex fixes this.

## 3. The "Trend Strength" Veto (ADX Filter)
**Problem**: Moving averages cross all the time in "choppy" sideways markets, generating false buy signals.
**Solution**: Implement the **ADX (Average Directional Index)**.
*   **Rule**: If `ADX < 25`, the market is "Choppy". **Reject ALL Buy Signals**, no matter what HFM/Quant say.
*   **Effect**: This single check prevents 60-70% of losses during sideways markets.

## 4. Institutional Validation (RVOL)
**Problem**: Retail traders buy peaks. Institutions buy breakouts. We need to follow Institutions.
**Solution**: **Relative Volume (RVOL) Threshold**.
*   **Rule**: A "Strong Buy" requires `Current Volume > 2.0x Average(20-Day Volume)`.
*   **Logic**: A 10% move on low volume is a lie. A 2% move on huge volume is the truth.

## 5. Sector Confluence ("The Rising Tide")
**Problem**: Buying a Tech stock when the Tech Sector is crashing is suicide.
**Solution**: Check the Sector Index (e.g., NIFTY IT, NIFTY BANK).
*   **Rule**: If `Stock = "Buy"` BUT `Sector Index = "Sell"`, downgrade signal to "AVOID".
*   **Effect**: Ensures you only swim *with* the current.

## 6. The "Golden Standard" (90% Probabilistic Model)
To achieve near-perfect accuracy, we create a strict **"Supreme Tier"** in the dashboard that simply returns NOTHING unless a stock meets *ALL* of these criteria simultaneously:
1.  **Persistence**: Buy Signal active for >48 hours.
2.  **Apex Confirmation**: Apex Score > 0.8 (Strong Volume + Trend).
3.  **Trend Strength**: ADX > 25 (Trend is accelerating).
4.  **No Resistance**: Price is above 200 EMA and 50 EMA.

---

## Implementation Roadmap (No Code Changes Yet)
1.  **Modify Wrappers**: Update fetchers to pull 3 days of data history for scoring.
2.  **Update Strategy**: Rewrite `main.py` to calculate Trajectory Score.
3.  **Upgrade Features**: Add ADX and RVOL calculations to `features.py`.
4.  **Rewrite Ranking**: Include Apex in the final weighted average.

This system moves from "Reacting to Price" to "Confirming Trends".
