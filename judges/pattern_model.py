import joblib
import numpy as np
import pandas as pd

class PatternModel:
    def __init__(self):
        try:
            # Loads the Random Forest Pipeline
            self.pipeline = joblib.load('judges/models/rf_pattern.pkl')
            self.model_loaded = True
        except Exception as e:
            self.model_loaded = False
            print(f"⚠️ Pattern Model (RF) missing: {e}")

    def assess(self, features):
        """
        Role: Supervised Learning (Random Forest)
        Input: [amount, opex_ratio, users_on_device, account_age_days]
        """
        feature_names = ['amount', 'opex_ratio', 'users_on_device', 'account_age_days']
        X_input = pd.DataFrame([features], columns=feature_names)
        
        ml_score = 0.0
        
        # 1. ML PREDICTION
        if self.model_loaded:
            # Get probability of Fraud (Class 1)
            ml_score = self.pipeline.predict_proba(X_input)[0][1]
        
        # 2. HEURISTIC RULES (Expert Systems)
        amount = features[0]
        account_age = features[3]
        
        # Rule: Structuring (Just below reporting limit)
        if 48000 <= amount < 50000:
            ml_score += 0.2
            
        # Rule: Bust-Out (New account + Massive Spend)
        if account_age < 5 and amount > 50000:
            ml_score += 0.3
            
        final_score = min(ml_score, 1.0)
        
        verdict = "Normal"
        if final_score > 0.75: verdict = "High Risk Pattern"
        elif final_score > 0.4: verdict = "Suspicious Activity"
        
        return final_score, verdict