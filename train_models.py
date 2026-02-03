# train_models.py
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

# CONFIG
DB_CONN = 'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db'

def get_training_data():
    """
    Fetches real data. Handles column name mismatches (device_used vs device_id).
    Generates synthetic data if the DB is too empty.
    """
    try:
        engine = create_engine(DB_CONN)
        df = pd.read_sql("SELECT * FROM transactions", engine)
        print(f"   📊 Loaded {len(df)} rows from Database.")
    except Exception as e:
        print(f"   ⚠️ DB Connection Failed: {e}")
        df = pd.DataFrame()

    # --- SMART COLUMN FIXER (Compatibility Layer) ---
    # If DB has 'device_used', rename it to 'device_id' for consistency
    if 'device_used' in df.columns:
        df.rename(columns={'device_used': 'device_id'}, inplace=True)
        
    # If DB is missing 'payment_method_detail' (sometimes called 'category')
    if 'payment_method_detail' not in df.columns and 'category' in df.columns:
        df.rename(columns={'category': 'payment_method_detail'}, inplace=True)

    # --- IF DATABASE IS EMPTY OR TOO SMALL (< 50 rows) ---
    if len(df) < 50:
        print("   ⚠️ Data insufficient for ML. Generating 2,000 synthetic records...")
        np.random.seed(42)
        n_rows = 2000
        
        # 1. Normal Transactions (95%)
        n_safe = int(n_rows * 0.95)
        safe_data = {
            'amount': np.random.normal(5000, 2000, n_safe), 
            'opex_ratio': np.random.uniform(0.3, 0.8, n_safe), 
            'users_on_device': np.random.choice([1, 2], n_safe, p=[0.9, 0.1]),
            'account_age_days': np.random.uniform(100, 2000, n_safe),
            'device_id': [f"safe_dev_{i}" for i in range(n_safe)],
            'is_fraud': 0
        }
        
        # 2. Fraud Transactions (5%)
        n_fraud = n_rows - n_safe
        fraud_data = {
            'amount': np.random.normal(150000, 50000, n_fraud), 
            'opex_ratio': np.random.uniform(0.0, 0.05, n_fraud), 
            'users_on_device': np.random.choice([5, 10, 15], n_fraud),
            'account_age_days': np.random.uniform(1, 30, n_fraud),
            'device_id': [f"fraud_dev_{i}" for i in range(n_fraud)],
            'is_fraud': 1
        }
        
        df = pd.concat([pd.DataFrame(safe_data), pd.DataFrame(fraud_data)])
        df['amount'] = df['amount'].abs()
        
    else:
        # --- FEATURE ENGINEERING ON REAL DB DATA ---
        print("   ✅ Engineering Features from Real Data...")
        
        # 1. OpEx Ratio
        # Check if payment_method_detail exists, else mock it
        if 'payment_method_detail' in df.columns:
            opex_cats = ['Electricity Bill', 'Rent', 'Metro Recharge', 'Zomato', 'Groceries']
            df['is_opex'] = df['payment_method_detail'].apply(lambda x: 1 if x in opex_cats else 0)
        else:
            df['is_opex'] = 0 # Fallback
        
        cust_stats = df.groupby('customer_id').agg({'amount': 'sum', 'is_opex': 'sum'}).rename(columns={'amount': 'total', 'is_opex': 'opex'})
        df = df.merge(cust_stats, on='customer_id', how='left')
        df['opex_ratio'] = df['opex'] / (df['total'] + 1)
        
        # 2. Device Usage (Crucial Step that failed before)
        # Now we are guaranteed to have 'device_id' because of the fixer above
        dev_map = df.groupby('device_id')['customer_id'].nunique().to_dict()
        df['users_on_device'] = df['device_id'].map(dev_map).fillna(1)
        
        # 3. Account Age
        if 'account_age_days' not in df.columns:
            df['account_age_days'] = np.random.randint(10, 1000, len(df))
            
        # 4. Target Variable
        if 'is_fraud' not in df.columns:
            df['is_fraud'] = 0

    return df

def train():
    print("\n🚀 STARTING PROFESSIONAL MODEL TRAINING PIPELINE...")
    
    # 1. Get Data
    df = get_training_data()
    
    # Final check to ensure we didn't lose data
    if df.empty:
        print("❌ Critical Error: No data could be loaded or generated.")
        return

    features = ['amount', 'opex_ratio', 'users_on_device', 'account_age_days']
    
    # Fill any remaining NaNs with 0 to prevent crashes
    X = df[features].fillna(0)
    y = df['is_fraud']
    
    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # --- JUDGE 1: THE HISTORIAN (Random Forest) ---
    print("\n👨‍⚖️ Training JUDGE 1: The Historian (Supervised)...")
    
    historian_pipeline = Pipeline([
        ('scaler', StandardScaler()), 
        ('clf', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42))
    ])
    
    historian_pipeline.fit(X_train, y_train)
    
    # Validate
    y_pred = historian_pipeline.predict(X_test)
    print("   ✅ Training Complete.")
    print("   📊 Historian Performance Report:")
    # Handle case where only 1 class exists in test set
    try:
        print(classification_report(y_test, y_pred, target_names=['Safe', 'Fraud']))
    except:
        print("   (Report skipped: Not enough fraud samples in test set)")

    # --- JUDGE 2: THE AUDITOR (Isolation Forest) ---
    print("\n🧐 Training JUDGE 2: The Auditor (Unsupervised)...")
    
    auditor_pipeline = Pipeline([
        ('scaler', StandardScaler()), 
        ('model', IsolationForest(contamination=0.05, random_state=42))
    ])
    
    auditor_pipeline.fit(X)
    print("   ✅ Auditor Trained on Distribution Patterns.")

    # --- SAVING MODELS ---
    print("\n💾 Saving Trained Pipelines...")
    if not os.path.exists('judges/models'):
        os.makedirs('judges/models')
        
    joblib.dump(historian_pipeline, 'judges/models/historian.pkl')
    joblib.dump(auditor_pipeline, 'judges/models/auditor.pkl')
    
    print("✅ DONE. Models saved to 'judges/models/'. Ready for Real-Time Inference.")

if __name__ == "__main__":
    train()