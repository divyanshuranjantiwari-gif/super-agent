import pandas as pd
import numpy as np
# from sklearn.ensemble import GradientBoostingClassifier # Commented out to avoid import errors if not installed
# import xgboost as xgb

class MLEngine:
    def __init__(self):
        pass

    def prepare_features(self, technical_data, fundamental_data):
        """
        Combines technical and fundamental data into a feature vector.
        """
        features = {}
        
        # Add Technicals
        if technical_data and 'signals' in technical_data:
            features.update(technical_data['signals'])
            
        # Add Fundamentals
        if fundamental_data and 'metrics' in fundamental_data:
            features.update(fundamental_data['metrics'])
            
        return features

    def rank_stocks(self, stocks_data):
        """
        Ranks stocks based on a combined score.
        stocks_data: List of dicts containing symbol, technical_score, fundamental_score
        """
        # In a real ML model, we would predict the probability of X% return.
        # Here we use a weighted ensemble of scores.
        
        ranked_stocks = []
        
        for stock in stocks_data:
            tech_score = stock.get('technical_score', 0)
            fund_score = stock.get('fundamental_score', 0)
            
            # Weighted Score: 60% Technical (for trading), 40% Fundamental (for safety)
            # Adjust weights based on time horizon if needed.
            final_score = (tech_score * 0.6) + (fund_score * 0.4)
            
            stock['confidence_score'] = final_score
            ranked_stocks.append(stock)
            
        # Sort by confidence score descending
        ranked_stocks.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return ranked_stocks

if __name__ == "__main__":
    pass
