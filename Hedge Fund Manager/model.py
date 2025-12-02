import xgboost as xgb
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np

def train_predict_model(df):
    """
    Trains XGBoost model and predicts next day's close.
    Returns: predicted_price, confidence_score (R2)
    """
    # Define features to use
    # Must match what is generated in features.py
    feature_cols = ['RSI', 'ATR_Normalized', 'Vol_Shock', 'RS_Momentum', 'Day_of_Week']
    
    # Check if columns exist
    available_features = [f for f in feature_cols if f in df.columns]
    
    if not available_features or len(df) < 60:
        return None, 0
    
    # Prepare Target: Next Day Close
    df['Target'] = df['Close'].shift(-1)
    
    # Drop NaNs created by shifting and indicators
    data = df.dropna()
    
    if data.empty:
        return None, 0
    
    X = data[available_features]
    y = data['Target']
    
    # Train/Test Split (Time-based split, no shuffle)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # Initialize and Train Model
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, learning_rate=0.1, max_depth=3)
    model.fit(X_train, y_train)
    
    # Evaluate
    score = model.score(X_test, y_test) # R2 Score
    
    # Retrain on full data for final prediction
    model.fit(X, y)
    
    # Predict for the next day
    # We use the LAST available row of features (from the original df, which has today's data)
    last_row = df.iloc[[-1]][available_features]
    
    # Handle case where last row might have NaNs if indicators need future data (unlikely for these indicators)
    # But if last row has NaNs, we can't predict.
    if last_row.isnull().values.any():
        # Try previous row? No, we need today's data to predict tomorrow.
        # If today's data is incomplete, we can't predict.
        return None, 0
        
    predicted_price = model.predict(last_row)[0]
    
    return predicted_price, score
