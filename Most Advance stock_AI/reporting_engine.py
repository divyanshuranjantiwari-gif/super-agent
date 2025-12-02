import json
import pandas as pd
import os
from config import OUTPUT_DIR

class ReportingEngine:
    def __init__(self):
        pass

    def generate_signals_csv(self, signals):
        """
        Saves signals to a CSV file with flattened structure.
        """
        flattened_data = []
        for s in signals:
            row = {
                "symbol": s.get("symbol"),
                "recommendation": s.get("recommendation"),
                "time_horizon": s.get("time_horizon"),
                "confidence_score": s.get("confidence_score"),
                "risk_grade": s.get("risk_grade"),
                "entry_price": s.get("entry", {}).get("price"),
                "entry_range_low": s.get("entry", {}).get("range", [0, 0])[0],
                "entry_range_high": s.get("entry", {}).get("range", [0, 0])[1],
                "stop_loss": s.get("stop_loss"),
            }
            
            # Targets
            targets = s.get("targets", [])
            if len(targets) > 0:
                row["target_1"] = targets[0].get("price")
                row["target_1_prob"] = targets[0].get("probability")
            else:
                row["target_1"] = None
                row["target_1_prob"] = None
                
            if len(targets) > 1:
                row["target_2"] = targets[1].get("price")
                row["target_2_prob"] = targets[1].get("probability")
            else:
                row["target_2"] = None
                row["target_2_prob"] = None
                
            flattened_data.append(row)

        df = pd.DataFrame(flattened_data)
        output_path = os.path.join(OUTPUT_DIR, "signals.csv")
        df.to_csv(output_path, index=False)
        print(f"Signals saved to {output_path}")

    def export_reports(self, ranked_stocks):
        """
        Exports top lists to CSV.
        """
        df = pd.DataFrame(ranked_stocks)
        
        # Top Buys
        top_buys = df[df['recommendation'] == 'BUY'].head(20)
        top_buys.to_csv(os.path.join(OUTPUT_DIR, "top_buys.csv"), index=False)
        
        # Top Sells
        top_sells = df[df['recommendation'] == 'SELL'].head(20)
        top_sells.to_csv(os.path.join(OUTPUT_DIR, "top_sells.csv"), index=False)
        
        print("Reports exported to output directory.")

if __name__ == "__main__":
    pass
