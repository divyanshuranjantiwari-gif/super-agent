import pandas as pd
import io
import requests

def get_nifty500():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            csv_content = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_content))
            # Column name is usually 'Symbol'
            symbols = df['Symbol'].tolist()
            return [s + ".NS" for s in symbols]
        else:
            print(f"Failed to fetch: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

symbols = get_nifty500()
print(f"Fetched {len(symbols)} symbols.")
print(f"First 5: {symbols[:5]}")
