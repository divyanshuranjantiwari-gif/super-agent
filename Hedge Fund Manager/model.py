import xgboost as xgb
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np

def train_predict_model(df):
    """
    Trains XGBoost model and predicts next day's close.
    FIX #4: Uses all meaningful features instead of just 5.
    Returns: predicted_price, confidence_score (R2)
    """
    # FIX #4: Expanded feature set — use all indicators that features.py calculates
    feature_cols = [
        'RSI', 
        'MACD_12_26_9',    # MACD line value
        'MACDh_12_26_9',   # MACD histogram (momentum direction)
        'ATR_Normalized',  # Volatility relative to price
        'Vol_Shock',       # Institutional volume spike
        'EMA_20',          # Short-term trend level
        'ADX',             # Trend strength
        'RVOL',            # Relative volume
        'RS_Momentum',     # Relative strength vs benchmark
    ]
    
    # Check which features actually exist in the data
    available_features = [f for f in feature_cols if f in df.columns]
    
    if len(available_features) < 3 or len(df) < 60:
        return None, 0
    
    # Prepare Target: Next Day Close
    df = df.copy()  # Avoid SettingWithCopyWarning
    df['Target'] = df['Close'].shift(-1)
    
    # Drop NaNs created by shifting and indicators
    data = df.dropna(subset=available_features + ['Target'])
    
    if len(data) < 40:
        return None, 0
    
    X = data[available_features]
    y = data['Target']
    
    # Train/Test Split (Time-based split, no shuffle)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    if len(X_train) < 20 or len(X_test) < 5:
        return None, 0
    
    # Initialize and Train Model
    model = xgb.XGBRegressor(
        objective='reg:squarederror', 
        n_estimators=150, 
        learning_rate=0.08, 
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        verbosity=0
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    score = model.score(X_test, y_test)  # R2 Score
    
    # Retrain on full data for final prediction
    model.fit(X, y)
    
    # Predict for the next day using today's features
    last_row = df.iloc[[-1]][available_features]
    
    if last_row.isnull().values.any():
        # Fill remaining NaNs with column medians as fallback
        last_row = last_row.fillna(X.median())
        
    predicted_price = model.predict(last_row)[0]
    
    return predicted_price, score
