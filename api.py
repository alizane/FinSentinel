# Version: 1.2
# Description: Increased risk scores for better demo sensitivity and fixed reasons output.

from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from sqlalchemy import create_engine

def get_engine():
    return create_engine(f'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db')

class Transaction(BaseModel):
    customer_name: str
    amount: float
    beneficiary_name: str
    device: str

app = FastAPI()

def get_fraud_verdict(customer_name: str, new_tx_amount: float, new_beneficiary_name: str, new_device: str):
    engine = get_engine()
    query = f"SELECT amount, beneficiary_name, device_used FROM transactions WHERE customer_name = '{customer_name}' AND is_fraud = 0"
    history_df = pd.read_sql(query, engine)
    
    if history_df.empty:
        return "High Risk", 1, ["No historical data for this customer (High Risk by default)."]
        
    risk_score = 0
    reasons = []

    # FIX: Increased risk scores for better sensitivity
    # Rule 1: Amount Spike
    historical_max = history_df['amount'].max()
    if new_tx_amount > historical_max * 2.5:
        risk_score += 5 # High impact
        reasons.append(f"Amount Spike: Transaction of ₹{new_tx_amount:,.2f} is >2.5x the customer's historical max of ₹{historical_max:,.2f}.")

    # Rule 2: New Beneficiary
    if new_beneficiary_name not in history_df['beneficiary_name'].unique():
        risk_score += 4 # Medium-High impact
        reasons.append(f"New Beneficiary: '{new_beneficiary_name}' is not in the customer's known beneficiary list.")
    
    # Rule 3: New Device
    if new_device not in history_df['device_used'].unique():
        risk_score += 3 # Medium impact
        reasons.append(f"New Device: Transaction is from '{new_device}', which has not been used by this customer before.")

    # --- Final Verdict ---
    if risk_score >= 8:
        verdict = "High Risk - Blocked"
    elif risk_score >= 4:
        verdict = "Medium Risk - Flagged"
    else:
        verdict = "Approved"
    
    if not reasons:
        reasons.append("No suspicious patterns detected.")
    
    # FIX: Return the actual list of reasons, not a joined string
    return verdict, 1 if risk_score >= 4 else 0, reasons

@app.post("/analyze_transaction/")
async def analyze_transaction(transaction: Transaction):
    verdict, is_fraud, reasons = get_fraud_verdict(
        transaction.customer_name, transaction.amount, transaction.beneficiary_name, transaction.device
    )
    return {"verdict": verdict, "is_fraud": is_fraud, "reasons": reasons}

@app.get("/")
def read_root():
    return {"status": "Fraud Detection API is running"}