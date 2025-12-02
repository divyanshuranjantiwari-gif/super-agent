import os
import datetime

def generate_dual_reports(swing_results, intraday_results, output_dir):
    """
    Generates two separate HTML reports: Swing and Intraday.
    """
    swing_path = os.path.join(output_dir, "super_agent_swing.html")
    intraday_path = os.path.join(output_dir, "super_agent_intraday.html")
    
    _generate_single_report(swing_results, swing_path, "Swing Trading")
    _generate_single_report(intraday_results, intraday_path, "Intraday Trading")
    
    return swing_path, intraday_path

def _generate_single_report(results, output_file, report_type):
    # Sort results by Super Score (descending)
    sorted_results = sorted(results, key=lambda x: x['super_score'], reverse=True)
    
    # Generate Table Rows
    table_rows = ""
    for res in sorted_results:
        ticker = res['ticker']
        signal = res['final_signal']
        score = res['super_score']
        
        # Color coding
        row_class = ""
        signal_color = "#ffc107" # Yellow
        if signal == "BUY":
            row_class = "buy-row"
            signal_color = "#28a745" # Green
        elif signal == "SELL":
            row_class = "sell-row"
            signal_color = "#dc3545" # Red
        else:
            row_class = "wait-row"
            
        # Individual Model Details
        # Models now contain nested info, but main.py should have flattened it for display or passed the relevant part
        # Let's assume main.py passes the specific scenario data in 'models'
        
        hfm = res['models']['Hedge Fund Manager']
        stock_ai = res['models']['Most Advance stock_AI']
        quant = res['models']['Quantitative Development']
        
        # Trade Params
        entry = res.get('entry', 0)
        target = res.get('target', 0)
        sl = res.get('sl', 0)
        
        # Helper for color
        def get_color(sig):
            if "BUY" in sig.upper(): return "#28a745" # Green
            if "SELL" in sig.upper(): return "#dc3545" # Red
            return "#aaa" # Grey/Default
            
        hfm_sig = hfm.get('signal', 'WAIT')
        stock_sig = stock_ai.get('signal', 'WAIT')
        quant_sig = quant.get('signal', 'WAIT')
        
        apex = res['models'].get('Apex Logic', {})
        apex_sig = apex.get('signal', 'WAIT')
        apex_conf = apex.get('confidence', 0)
        
        apex_style = "color: #aaa;"
        if "STRONG BUY" in apex_sig: apex_style = "color: #ffd700; font-weight: bold; text-shadow: 0 0 5px #ffd700;" # Gold
        elif "STRONG SELL" in apex_sig: apex_style = "color: #ff4500; font-weight: bold; text-shadow: 0 0 5px #ff4500;" # OrangeRed
        elif "BUY" in apex_sig: apex_style = "color: #28a745; font-weight: bold;"
        elif "SELL" in apex_sig: apex_style = "color: #dc3545; font-weight: bold;"
        
        table_rows += f"""
        <tr class="{row_class}">
            <td class="ticker">{ticker}</td>
            <td class="signal" style="color: {signal_color}; font-weight: bold;">{signal}</td>
            <td class="score">{score:.2f}</td>
            <td class="trade-params">
                <div><strong>Entry:</strong> {entry:.2f}</div>
                <div><strong>Target:</strong> {target:.2f}</div>
                <div><strong>SL:</strong> {sl:.2f}</div>
            </td>
            <td class="details">
                <div class="model-detail"><strong>HFM:</strong> <span style="color: {get_color(hfm_sig)}; font-weight: bold;">{hfm_sig}</span> ({hfm.get('confidence',0):.2f})</div>
                <div class="model-detail"><strong>StockAI:</strong> <span style="color: {get_color(stock_sig)}; font-weight: bold;">{stock_sig}</span> ({stock_ai.get('confidence',0):.2f})</div>
                <div class="model-detail"><strong>Quant:</strong> <span style="color: {get_color(quant_sig)}; font-weight: bold;">{quant_sig}</span> ({quant.get('confidence',0):.2f})</div>
            </td>
            <td class="apex-col" style="text-align: center; border-left: 1px solid #444;">
                <div style="{apex_style}; font-size: 1.1em;">{apex_sig}</div>
                <div style="font-size: 0.8em; color: #888;">({apex_conf:.2f})</div>
            </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Super Agent Alpha - {report_type}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #121212;
                color: #e0e0e0;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max_width: 1400px;
                margin: 0 auto;
                background-color: #1e1e1e;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }}
            h1 {{
                text-align: center;
                color: #00d4ff;
                margin-bottom: 5px;
            }}
            .subtitle {{
                text-align: center;
                color: #888;
                margin-bottom: 30px;
                font-size: 1.2em;
                font-weight: 300;
            }}
            .report-tag {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                background-color: #333;
                color: #fff;
                font-size: 0.9em;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                padding: 15px;
                text-align: left;
                border-bottom: 1px solid #333;
            }}
            th {{
                background-color: #2c2c2c;
                color: #fff;
                font-weight: 600;
            }}
            tr:hover {{
                background-color: #252525;
            }}
            .buy-row {{
                border-left: 4px solid #28a745;
            }}
            .sell-row {{
                border-left: 4px solid #dc3545;
            }}
            .wait-row {{
                border-left: 4px solid #ffc107;
            }}
            .ticker {{
                font-size: 1.1em;
                font-weight: bold;
                color: #fff;
            }}
            .score {{
                font-family: 'Courier New', monospace;
                font-weight: bold;
            }}
            .trade-params {{
                font-size: 0.9em;
                color: #ddd;
            }}
            .model-detail {{
                font-size: 0.85em;
                color: #aaa;
                margin-bottom: 2px;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                color: #555;
                font-size: 0.8em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SUPER AGENT ALPHA</h1>
            <div class="subtitle">Unified Intelligence System</div>
            <div style="text-align:center;">
                <span class="report-tag">{report_type.upper()} REPORT</span>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Final Signal</th>
                        <th>Super Score</th>
                        <th>Trade Setup</th>
                        <th>Model Breakdown</th>
                        <th>Apex Signal 🏆</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            
            <div class="footer">
                Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
