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
    
    global_regime = sorted_results[0].get('market_regime', 'UNKNOWN') if sorted_results else 'UNKNOWN'
    
    # Generate Table Rows
    table_rows = ""
    for res in sorted_results:
        ticker = res['ticker']
        signal = res['final_signal']
        score = res['super_score']
        
        ml_conf = res.get('ml_confidence', None)
        
        # Color coding
        row_class = ""
        signal_color = "#ffc107" # Yellow
        if "STRONG BUY" in signal:
            row_class = "buy-row"
            signal_color = "#00ff88"
        elif "BUY" in signal:
            row_class = "buy-row"
            signal_color = "#28a745" # Green
        elif "STRONG SELL" in signal:
            row_class = "sell-row"
            signal_color = "#ff4500"
        elif "SELL" in signal:
            row_class = "sell-row"
            signal_color = "#dc3545" # Red
        else:
            row_class = "wait-row"
        
        # ML Confidence styling
        if ml_conf is not None:
            ml_pct = ml_conf * 100
            if ml_pct >= 70:
                ml_color = "#00ff88"  # Bright green
                ml_label = "HIGH"
            elif ml_pct >= 50:
                ml_color = "#ffd700"  # Gold
                ml_label = "MED"
            elif ml_pct >= 30:
                ml_color = "#ff8c00"  # Orange
                ml_label = "LOW"
            else:
                ml_color = "#dc3545"  # Red
                ml_label = "WEAK"
            ml_html = f'''<div style="color: {ml_color}; font-weight: bold; font-size: 1.2em;">{ml_pct:.0f}%</div>
                <div style="font-size: 0.75em; color: {ml_color}; opacity: 0.7;">{ml_label}</div>
                <div style="background: #333; border-radius: 4px; height: 4px; margin-top: 4px;">
                    <div style="background: {ml_color}; width: {ml_pct:.0f}%; height: 100%; border-radius: 4px;"></div>
                </div>'''
        else:
            ml_html = '<span style="color: #555;">N/A</span>'
            
        # Individual Model Details
        # Models now contain nested info, but main.py should have flattened it for display or passed the relevant part
        # Let's assume main.py passes the specific scenario data in 'models'
        
        hfm = res['models']['Hedge Fund Manager']
        stock_ai = res['models']['Most Advance stock_AI']
        quant = res['models']['Quantitative Development']
        
        # Trade Params & New Features
        entry = res.get('entry', 0)
        target = res.get('target', 0)
        sl = res.get('sl', 0)
        pos_size = res.get('position_size_pct', 0.0)
        sector_trend = res.get('sector_trend', 'NEUTRAL')
        
        sector_color = "#28a745" if sector_trend == 'UP' else "#dc3545" if sector_trend == 'DOWN' else "#aaa"
        
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
        <tr class="data-row {row_class}">
            <td class="ticker">
                {ticker}
                <div style="font-size: 0.7em; color: {sector_color}; margin-top: 6px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">SEC: {sector_trend}</div>
            </td>
            <td class="signal" style="color: {signal_color}; font-weight: bold;">{signal}</td>
            <td class="score">{score:.2f}</td>
            <td style="text-align: center; min-width: 80px;">{ml_html}</td>
            <td class="trade-params">
                <div><strong>Size:</strong> <span style="color: #00d4ff; font-weight: bold;">{pos_size:.1f}%</span></div>
                <div style="margin-top: 3px;"><strong>Entry:</strong> {entry:.2f}</div>
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
    <html>
    <head>
        <title>Tattva TradeAI 5.0</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Outfit', sans-serif;
                background-color: #050a15;
                background-image: radial-gradient(circle at 15% 50%, rgba(0, 229, 255, 0.08), transparent 25%),
                                  radial-gradient(circle at 85% 30%, rgba(0, 255, 136, 0.05), transparent 25%);
                color: #e0e6ed;
                margin: 0;
                padding: 40px;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            h1 {{
                text-align: center;
                color: #ffffff;
                font-weight: 800;
                font-size: 2.8em;
                margin-bottom: 5px;
                letter-spacing: 1px;
                text-shadow: 0 0 20px rgba(0, 229, 255, 0.3);
            }}
            .subtitle {{
                text-align: center;
                color: #00E5FF;
                font-size: 1.2em;
                font-weight: 300;
                margin-bottom: 30px;
                letter-spacing: 3px;
                text-transform: uppercase;
            }}
            .report-tag {{
                display: inline-block;
                padding: 6px 16px;
                background: rgba(0, 229, 255, 0.1);
                color: #00E5FF;
                border: 1px solid rgba(0, 229, 255, 0.3);
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0 10px;
                margin-top: 30px;
            }}
            th {{
                background: transparent;
                color: #8892b0;
                text-transform: uppercase;
                font-size: 0.85em;
                letter-spacing: 1px;
                padding: 12px 20px;
                text-align: left;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }}
            tr.data-row {{
                background: rgba(255, 255, 255, 0.02);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            tr.data-row:hover {{
                background: rgba(255, 255, 255, 0.05);
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,229,255,0.1);
            }}
            td {{
                padding: 20px;
                vertical-align: middle;
                border-top: 1px solid rgba(255,255,255,0.05);
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }}
            td:first-child {{
                border-left: 1px solid rgba(255,255,255,0.05);
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
            }}
            td:last-child {{
                border-right: 1px solid rgba(255,255,255,0.05);
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
            .buy-row td:first-child {{
                border-left: 4px solid #00ff88;
            }}
            .sell-row td:first-child {{
                border-left: 4px solid #ff4500;
            }}
            .wait-row td:first-child {{
                border-left: 4px solid #ffc107;
            }}
            .ticker {{
                font-size: 1.25em;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: 0.5px;
            }}
            .score {{
                font-weight: 600;
                font-size: 1.1em;
            }}
            .trade-params {{
                font-size: 0.95em;
                color: #a8b2d1;
                line-height: 1.6;
            }}
            .model-detail {{
                font-size: 0.85em;
                color: #8892b0;
                margin-bottom: 4px;
            }}
            .footer {{
                text-align: center;
                margin-top: 50px;
                color: #4a5568;
                font-size: 0.85em;
                letter-spacing: 1px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>TATTVA TradeAI</h1>
            <div class="subtitle">Institutional Intelligence System 5.0</div>
            <div style="text-align:center; margin-bottom: 20px;">
                <span class="report-tag" style="background: rgba(0, 229, 255, 0.15); border-color: #00E5FF; color: #00E5FF; margin-right: 15px; box-shadow: 0 0 10px rgba(0,229,255,0.2);">REGIME: {global_regime}</span>
                <span class="report-tag">{report_type.upper()} REPORT</span>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Final Signal</th>
                        <th>Super Score</th>
                        <th style="text-align: center;">ML Confidence</th>
                        <th>Trade Setup</th>
                        <th>Model Breakdown</th>
                        <th>Apex Signal</th>
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
