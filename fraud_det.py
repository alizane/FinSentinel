# Version: 1.1
# Description: Upgraded API to handle device type and check for multiple fraud rules.

from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from sqlalchemy import create_engine

# --- DATABASE CONNECTION ---
def get_engine():
    return create_engine(f'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db')

# --- DATA MODEL (Upgraded to include device) ---
class Transaction(BaseModel):
    customer_name: str
    amount: float
    beneficiary_name: str
    device: str

app = FastAPI()

# --- FRAUD DETECTION LOGIC (Upgraded) ---
def get_fraud_verdict(customer_name: str, new_tx_amount: float, new_beneficiary_name: str, new_device: str):
    engine = get_engine()
    # Fetch more historical data for a richer profile
    query = f"SELECT amount, beneficiary_name, device_used FROM transactions WHERE customer_name = '{customer_name}' AND is_fraud = 0"
    history_df = pd.read_sql(query, engine)
    
    if history_df.empty:
        return "High Risk", 1, ["No historical data for this customer (High Risk by default)."]
        
    risk_score = 0
    reasons = []

    # Rule 1: Amount Spike
    historical_max = history_df['amount'].max()
    if new_tx_amount > historical_max * 5:
        risk_score += 5
        reasons.append(f"Amount Spike: Transaction of ₹{new_tx_amount:,.2f} is >5x the customer's historical maximum of ₹{historical_max:,.2f}.")

    # Rule 2: New Beneficiary
    if new_beneficiary_name not in history_df['beneficiary_name'].unique():
        risk_score += 3
        reasons.append(f"New Beneficiary: '{new_beneficiary_name}' is not in the customer's known beneficiary list.")
    
    # NEW Rule 3: New Device
    if new_device not in history_df['device_used'].unique():
        risk_score += 2
        reasons.append(f"New Device: The transaction is from '{new_device}', which has not been used by this customer before.")

    # --- Final Verdict ---
    if risk_score >= 8:
        verdict = "High Risk - Blocked"
        is_fraud = 1
    elif risk_score >= 4:
        verdict = "Medium Risk - Flagged"
        is_fraud = 1
    else:
        verdict = "Approved"
        is_fraud = 0
    
    if not reasons:
        reasons.append("No suspicious patterns detected.")
    
    return verdict, is_fraud, reasons

# --- API ENDPOINT (Upgraded) ---
@app.post("/analyze_transaction/")
async def analyze_transaction(transaction: Transaction):
    verdict, is_fraud, reasons = get_fraud_verdict(
        transaction.customer_name, transaction.amount, transaction.beneficiary_name, transaction.device
    )
    
    return {"verdict": verdict, "is_fraud": is_fraud, "reasons": reasons}

@app.get("/")
def read_root():
    return {"status": "Fraud Detection API is running"}