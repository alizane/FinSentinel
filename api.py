from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import numpy as np

# --- 1. IMPORT STRICT MODEL CLASSES ---
from judges.pattern_model import PatternModel
from judges.anomaly_model import AnomalyModel
from judges.network_model import NetworkModel

# CONFIG
DB_CONN = 'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db'

app = FastAPI()

# ENABLE CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. INITIALIZE MODELS ---
# We instantiate the real logic engines here
pattern_engine = PatternModel()     # Random Forest
anomaly_engine = AnomalyModel()     # Isolation Forest
network_engine = NetworkModel(DB_CONN) # Graph Logic

# DATA MODEL
class TransactionRequest(BaseModel):
    customer_id: int
    amount: float
    device_id: str
    beneficiary_account: str
    account_age_days: int
    timestamp: str = None

# HELPER
def get_live_features(customer_id, amount, device_id):
    engine = create_engine(DB_CONN)
    
    # OpEx Check
    try:
        query_hist = f"""
            SELECT SUM(amount) as total,
            SUM(CASE WHEN payment_method_detail IN ('Electricity Bill', 'Rent', 'Metro Recharge') THEN 1 ELSE 0 END) as opex
            FROM transactions WHERE customer_id = {customer_id}
        """
        stats = pd.read_sql(query_hist, engine).iloc[0]
        opex_ratio = (stats['opex'] or 0) / ((stats['total'] or 0) + amount + 1)
    except:
        opex_ratio = 0.5 
    
    # Device Check
    try:
        q_dev = f"SELECT COUNT(DISTINCT customer_id) FROM transactions WHERE device_id = '{device_id}'"
        users_on_dev = pd.read_sql(q_dev, engine).iloc[0, 0]
    except:
        users_on_dev = 1

    return [amount, opex_ratio, users_on_dev], users_on_dev

# --- MAIN ENDPOINT ---
@app.post("/analyze_transaction/")
async def analyze_transaction(tx: TransactionRequest):
    try:
        # 1. Feature Engineering
        base_features, users_on_dev = get_live_features(tx.customer_id, tx.amount, tx.device_id)
        model_features = base_features + [tx.account_age_days]
        
        # 2. ASK THE MODELS
        
        # Call Random Forest
        p_pat, v_pat = pattern_engine.assess(model_features)
        
        # Call Isolation Forest
        p_ano, v_ano = anomaly_engine.assess(model_features)
        
        # Call Graph Engine
        p_net, v_net, reasons_net = network_engine.investigate(
            device_id=tx.device_id, 
            customer_id=tx.customer_id,
            beneficiary_account=tx.beneficiary_account, 
            amount=tx.amount
        )
        
        # 3. ENSEMBLE LOGIC
        final_score = (p_pat * 0.4) + (p_ano * 0.3) + (p_net * 0.3)
        
        status = "APPROVED"
        fraud_flag = 0
        fraud_type = "None"
        
        # Veto Logic: If Network says 100% risk, we block immediately
        if final_score > 0.5 or p_net == 1.0:
            status = "BLOCKED"
            fraud_flag = 1
            
            if p_net == 1.0:
                if "Mule" in str(reasons_net): fraud_type = "Star Topology"
                elif "Collision" in str(reasons_net): fraud_type = "Synthetic Identity"
                elif "Cycle" in str(reasons_net): fraud_type = "Circular Topology"
                else: fraud_type = "Network Anomaly"
            elif v_ano == "Statistical Outlier" or "SHELL" in v_ano:
                fraud_type = "Shell Operation"
            else:
                fraud_type = "Pattern Anomaly"
                
        # 4. SAVE TO DB
        engine = create_engine(DB_CONN)
        timestamp = tx.timestamp if tx.timestamp else datetime.now().isoformat()
        
        insert_sql = text("""
            INSERT INTO transactions 
            (customer_id, amount, timestamp, device_id, beneficiary_account, customer_account_number, city, is_fraud, fraud_type)
            VALUES 
            (:cust_id, :amt, :time, :dev, :ben, :acc_num, 'Mumbai', :is_fraud, :f_type)
        """)
        
        with engine.begin() as conn:
            conn.execute(insert_sql, {
                "cust_id": tx.customer_id,
                "amt": tx.amount,
                "time": timestamp,
                "dev": tx.device_id,
                "ben": tx.beneficiary_account,
                "acc_num": f"ACC_{tx.customer_id}",
                "is_fraud": fraud_flag,
                "f_type": fraud_type
            })

        # 5. RETURN PROFESSIONAL JSON
        return {
            "status": status,
            "risk_score": round(final_score * 100, 2),
            "model_breakdown": {
                "Pattern_Model": {"score": round(p_pat, 2), "verdict": v_pat},
                "Anomaly_Model": {"score": p_ano, "verdict": v_ano},
                "Network_Model": {"score": p_net, "verdict": v_net, "details": reasons_net}
            }
        }
        
    except Exception as e:
        print(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))