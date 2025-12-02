from jinja2 import Template
import os
from datetime import datetime

def generate_html_report(signals):
    """
    Generates an HTML report from the signals.
    """
    # Sort signals by Confidence and Upside
    # Filter for BUY/STRONG_BUY
    buy_signals = [s for s in signals if "BUY" in s['Signal']]
    # Sort by Confidence desc, then Upside desc
    buy_signals.sort(key=lambda x: (x['Confidence'], x['Upside_Pct']), reverse=True)
    
    top_picks = buy_signals[:3]
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hedge Fund Trading Report</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f0f2f5; color: #333; }
            h1 { color: #1a1a1a; text-align: center; margin-bottom: 30px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }
            .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s; }
            .card:hover { transform: translateY(-5px); }
            .strong-buy { border-top: 5px solid #28a745; }
            .buy { border-top: 5px solid #82c91e; }
            .sell { border-top: 5px solid #dc3545; }
            .neutral { border-top: 5px solid #6c757d; }
            
            .ticker-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
            .ticker-name { font-size: 1.5em; font-weight: bold; }
            .signal-badge { padding: 5px 10px; border-radius: 20px; color: white; font-weight: bold; font-size: 0.9em; }
            .badge-strong-buy { background-color: #28a745; }
            .badge-buy { background-color: #82c91e; }
            
            .metric-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.95em; }
            .metric-label { color: #666; }
            .metric-value { font-weight: 600; }
            
            table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
            th { background-color: #f8f9fa; font-weight: 600; color: #444; }
            tr:hover { background-color: #f8f9fa; }
            
            .positive { color: green; }
            .negative { color: red; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Hedge Fund AI Trading Report</h1>
            <p style="text-align: center; color: #666;">Generated on: {{ date }}</p>
            
            <h2>🏆 Top High-Conviction Picks</h2>
            {% if top_picks %}
            <div class="card-grid">
                {% for pick in top_picks %}
                <div class="card {{ pick.Signal.lower().replace('_', '-') }}">
                    <div class="ticker-header">
                        <span class="ticker-name">{{ pick.Ticker }}</span>
                        <span class="signal-badge badge-{{ pick.Signal.lower().replace('_', '-') }}">{{ pick.Signal.replace('_', ' ') }}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Confidence Score</span>
                        <span class="metric-value">{{ pick.Confidence }}%</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Predicted Upside</span>
                        <span class="metric-value positive">{{ pick.Upside_Pct }}%</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Current Price</span>
                        <span class="metric-value">₹{{ pick.Current_Price }}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Target Price</span>
                        <span class="metric-value">₹{{ pick.Predicted_Price }}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Stop Loss</span>
                        <span class="metric-value" style="color: #dc3545;">₹{{ pick.Stop_Loss }}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Sentiment</span>
                        <span class="metric-value">{{ pick.Sentiment_Score }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <p style="text-align: center;">No Strong Buy/Buy signals generated today.</p>
            {% endif %}
            
            <h2>📊 Full Market Analysis</h2>
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Signal</th>
                    <th>Confidence</th>
                    <th>Upside %</th>
                    <th>Current Price</th>
                    <th>Target Price</th>
                    <th>Sentiment</th>
                </tr>
                {% for signal in all_signals %}
                <tr>
                    <td>{{ signal.Ticker }}</td>
                    <td style="font-weight: bold; color: {% if 'BUY' in signal.Signal %}green{% elif 'SELL' in signal.Signal %}red{% else %}gray{% endif %}">
                        {{ signal.Signal.replace('_', ' ') }}
                    </td>
                    <td>{{ signal.Confidence }}%</td>
                    <td class="{% if signal.Upside_Pct > 0 %}positive{% else %}negative{% endif %}">{{ signal.Upside_Pct }}%</td>
                    <td>{{ signal.Current_Price }}</td>
                    <td>{{ signal.Predicted_Price }}</td>
                    <td>{{ signal.Sentiment_Score }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(top_picks=top_picks, all_signals=signals, date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "report.html")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return output_path
