import joblib
import numpy as np
import pandas as pd

class AnomalyModel:
    def __init__(self):
        try:
            # Loads the Isolation Forest
            self.pipeline = joblib.load('judges/models/iso_anomaly.pkl')
            self.model_loaded = True
        except:
            self.model_loaded = False
            print("⚠️ Anomaly Model (IsoForest) missing.")

    def assess(self, features):
        """
        Role: Unsupervised Anomaly Detection (Isolation Forest)
        """
        feature_names = ['amount', 'opex_ratio', 'users_on_device', 'account_age_days']
        X_input = pd.DataFrame([features], columns=feature_names)
        
        risk_score = 0.0
        verdict = "Normal Pulse"

        # 1. STATISTICAL OUTLIER DETECTION
        if self.model_loaded:
            # decision_function: Negative values are anomalies
            raw_score = self.pipeline.decision_function(X_input)[0]
            
            if raw_score < -0.15:
                risk_score = 1.0
                verdict = "Statistical Outlier"
            elif raw_score < 0:
                risk_score = 0.5
                verdict = "Deviating Behavior"

        # 2. SHELL COMPANY LOGIC (Deterministic)
        # High Revenue + Zero Operational Expenses
        amount = features[0]
        opex_ratio = features[1]
        
        if amount > 100000 and opex_ratio < 0.01:
            risk_score = 1.0
            verdict = "🚨 SHELL DETECTED (Zero OpEx)"

        return risk_score, verdict