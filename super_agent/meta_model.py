"""
Super Agent 4.0 — Meta-ML Model
=================================
A LightGBM classifier trained on backtest data to predict
whether a stock will hit +3% in the next 5 trading days.

Input features: Individual model signals + technical indicators
Output: Probability of success (0-1)

This model sits ON TOP of the 4 existing models as a "judge"
that learns which combinations of signals actually work.
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# Try to import lightgbm, fall back to sklearn GBM
try:
    import lightgbm as lgb
    USE_LGB = True
except ImportError:
    from sklearn.ensemble import GradientBoostingClassifier
    USE_LGB = False

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, 'meta_model.pkl')
BACKTEST_CSV = os.path.join(MODEL_DIR, 'backtest_trades.csv')


def signal_to_numeric(signal):
    """Convert text signal to numeric value."""
    s = str(signal).upper().replace('_', ' ')
    if 'STRONG BUY' in s: return 2
    if 'STRONG SELL' in s: return -2
    if 'BUY' in s: return 1
    if 'SELL' in s: return -1
    return 0


def prepare_features(df):
    """
    Prepare feature matrix from backtest trade data.
    """
    features = pd.DataFrame()
    
    # Model signals (numeric)
    features['apex_sig'] = df['apex_signal'].apply(signal_to_numeric)
    features['hfm_sig'] = df['hfm_signal'].apply(signal_to_numeric)
    features['stockai_sig'] = df['stockai_signal'].apply(signal_to_numeric)
    features['quant_sig'] = df['quant_signal'].apply(signal_to_numeric)
    
    # Model confidences
    features['apex_conf'] = pd.to_numeric(df['apex_conf'], errors='coerce').fillna(0)
    features['hfm_conf'] = pd.to_numeric(df['hfm_conf'], errors='coerce').fillna(0)
    features['stockai_conf'] = pd.to_numeric(df['stockai_conf'], errors='coerce').fillna(0)
    features['quant_conf'] = pd.to_numeric(df['quant_conf'], errors='coerce').fillna(0)
    
    # Ensemble
    features['super_score'] = pd.to_numeric(df['super_score'], errors='coerce').fillna(0)
    features['ensemble_sig'] = df['ensemble_signal'].apply(signal_to_numeric)
    
    # Technical indicators
    features['rsi'] = pd.to_numeric(df['rsi'], errors='coerce').fillna(50)
    features['adx'] = pd.to_numeric(df['adx'], errors='coerce').fillna(0)
    features['rvol'] = pd.to_numeric(df['rvol'], errors='coerce').fillna(1)
    features['macd_diff'] = pd.to_numeric(df['macd_diff'], errors='coerce').fillna(0)
    
    # Binary features
    features['above_sma50'] = pd.to_numeric(df['above_sma50'], errors='coerce').fillna(0)
    features['above_sma200'] = pd.to_numeric(df['above_sma200'], errors='coerce').fillna(0)
    features['above_ema20'] = pd.to_numeric(df['above_ema20'], errors='coerce').fillna(0)
    features['above_vwap'] = pd.to_numeric(df['above_vwap'], errors='coerce').fillna(0)
    
    # Derived: Model agreement
    sigs = features[['apex_sig', 'hfm_sig', 'stockai_sig', 'quant_sig']]
    features['model_agreement'] = sigs.apply(lambda row: (row > 0).sum() - (row < 0).sum(), axis=1)
    features['all_buy'] = (sigs > 0).all(axis=1).astype(int)
    features['any_sell'] = (sigs < 0).any(axis=1).astype(int)
    features['buy_count'] = (sigs > 0).sum(axis=1)
    features['sell_count'] = (sigs < 0).sum(axis=1)
    
    # Avg confidence of BUY models
    confs = features[['apex_conf', 'hfm_conf', 'stockai_conf', 'quant_conf']]
    buy_mask = sigs > 0
    features['avg_buy_conf'] = confs.where(buy_mask).mean(axis=1).fillna(0)
    
    return features


def train_meta_model():
    """
    Train the meta-model on backtest data.
    """
    if not os.path.exists(BACKTEST_CSV):
        print(f"ERROR: Backtest data not found at {BACKTEST_CSV}")
        print("Run backtester.py first to generate training data.")
        return None
    
    print("Loading backtest data...")
    df = pd.read_csv(BACKTEST_CSV)
    print(f"  Total records: {len(df)}")
    
    # Prepare features
    X = prepare_features(df)
    
    # Target: Did the stock hit +3% in 5 days?
    y = df['hit_target'].astype(int)
    
    print(f"  Features: {X.shape[1]}")
    print(f"  Positive rate: {y.mean()*100:.1f}% ({y.sum()}/{len(y)})")
    
    # Time-series cross-validation (no random split for time series!)
    tscv = TimeSeriesSplit(n_splits=5)
    
    fold_metrics = []
    
    print("\n  Training with 5-Fold Time Series Cross-Validation...\n")
    
    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        if USE_LGB:
            model = lgb.LGBMClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=5,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_samples=20,
                reg_alpha=0.1,
                reg_lambda=0.1,
                verbosity=-1,
                random_state=42
            )
        else:
            model = GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=5,
                subsample=0.8,
                random_state=42
            )
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        fold_metrics.append({'acc': acc, 'prec': prec, 'rec': rec, 'f1': f1})
        print(f"  Fold {fold+1}: Acc={acc:.3f} | Precision={prec:.3f} | Recall={rec:.3f} | F1={f1:.3f}")
    
    # Average metrics
    avg_acc = np.mean([m['acc'] for m in fold_metrics])
    avg_prec = np.mean([m['prec'] for m in fold_metrics])
    avg_rec = np.mean([m['rec'] for m in fold_metrics])
    avg_f1 = np.mean([m['f1'] for m in fold_metrics])
    
    print(f"\n  {'='*55}")
    print(f"  AVG:    Acc={avg_acc:.3f} | Precision={avg_prec:.3f} | Recall={avg_rec:.3f} | F1={avg_f1:.3f}")
    print(f"  {'='*55}")
    
    # Train final model on all data
    print("\n  Training final model on all data...")
    
    if USE_LGB:
        final_model = lgb.LGBMClassifier(
            n_estimators=200, learning_rate=0.05, max_depth=5,
            num_leaves=31, subsample=0.8, colsample_bytree=0.8,
            min_child_samples=20, reg_alpha=0.1, reg_lambda=0.1,
            verbosity=-1, random_state=42
        )
    else:
        final_model = GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.05, max_depth=5,
            subsample=0.8, random_state=42
        )
    
    final_model.fit(X, y)
    
    # Feature importance
    if USE_LGB:
        importance = pd.Series(final_model.feature_importances_, index=X.columns)
    else:
        importance = pd.Series(final_model.feature_importances_, index=X.columns)
    
    print("\n  Feature Importance (Top 10):")
    for feat, imp in importance.sort_values(ascending=False).head(10).items():
        bar = '#' * int(imp / importance.max() * 30)
        print(f"    {feat:20s} {bar} ({imp:.0f})")
    
    # Save model
    model_data = {
        'model': final_model,
        'features': list(X.columns),
        'metrics': {
            'accuracy': avg_acc,
            'precision': avg_prec,
            'recall': avg_rec,
            'f1': avg_f1,
        },
        'positive_rate': float(y.mean()),
        'train_size': len(df),
    }
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"\n  Model saved to: {MODEL_PATH}")
    print(f"  Train size: {len(df)} trades")
    
    return model_data


def load_meta_model():
    """Load the trained meta-model."""
    if not os.path.exists(MODEL_PATH):
        return None
    
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)


def predict_with_meta(model_data, trade_data):
    """
    Use the meta-model to predict success probability.
    
    trade_data: dict with keys matching backtest CSV columns
    Returns: probability (0-1)
    """
    if model_data is None:
        return None
    
    df = pd.DataFrame([trade_data])
    X = prepare_features(df)
    
    model = model_data['model']
    prob = model.predict_proba(X)[0][1]  # Probability of class 1 (hit target)
    
    return prob


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SUPER AGENT 4.0 — META-ML MODEL TRAINER")
    print("="*60 + "\n")
    
    model_data = train_meta_model()
    
    if model_data:
        print(f"\n  [OK] Meta-model trained successfully!")
        print(f"  Cross-validated accuracy: {model_data['metrics']['accuracy']*100:.1f}%")
        print(f"  Cross-validated precision: {model_data['metrics']['precision']*100:.1f}%")
    else:
        print(f"\n  [FAIL] Training failed. Run backtester.py first.")
