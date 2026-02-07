from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import numpy as np

# ==========================================
#   SECTION 1: SETUP & CONFIGURATION
# ==========================================

from judges.pattern_model import PatternModel
from judges.anomaly_model import AnomalyModel
from judges.network_model import NetworkModel

DB_CONN = 'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db'
engine = create_engine(DB_CONN)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    pattern_engine = PatternModel()
    anomaly_engine = AnomalyModel()
    network_engine = NetworkModel(DB_CONN)
    print("✅ Models Loaded Successfully")
except Exception as e:
    print(f"⚠️ Warning: Models not loaded. {e}")


# ==========================================
#   SECTION 2: DATA MODELS
# ==========================================

class TransactionRequest(BaseModel):
    customer_id: int
    amount: float
    device_id: str
    beneficiary_account: str
    account_age_days: int
    timestamp: str = None

class GNNTransactionRequest(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float
    is_gnn_active: bool
    scenario_type: str = "star"

class PatternRequest(BaseModel):
    customer_id: int
    amount: float
    device_id: str
    beneficiary_account: str
    city: str
    hour: int
    is_active: bool
    is_velocity_attack: bool = False
    is_amount_spike: bool = False

class CustomerDetailRequest(BaseModel):
    customer_id: int


# ==========================================
#   SECTION 3: HELPER FUNCTIONS
# ==========================================

def get_ist_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).isoformat()

def get_live_features(customer_id, amount, device_id):
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
    try:
        q_dev = f"SELECT COUNT(DISTINCT customer_id) FROM transactions WHERE device_id = '{device_id}'"
        users_on_dev = pd.read_sql(q_dev, engine).iloc[0, 0]
    except:
        users_on_dev = 1
    return [amount, opex_ratio, users_on_dev], users_on_dev


# ==========================================
#   SECTION 4: CORE ANALYSIS ENDPOINT
# ==========================================

@app.post("/analyze_transaction/")
async def analyze_transaction(tx: TransactionRequest):
    try:
        base_features, users_on_dev = get_live_features(tx.customer_id, tx.amount, tx.device_id)
        model_features = base_features + [tx.account_age_days]
        
        p_pat, v_pat = pattern_engine.assess(model_features)
        p_ano, v_ano = anomaly_engine.assess(model_features)
        p_net, v_net, reasons_net = network_engine.investigate(
            device_id=tx.device_id, 
            customer_id=tx.customer_id,
            beneficiary_account=tx.beneficiary_account, 
            amount=tx.amount
        )
        
        final_score = (p_pat * 0.4) + (p_ano * 0.3) + (p_net * 0.3)
        status = "APPROVED"
        fraud_flag = 0
        fraud_type = "None"
        
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
        
        try:
            name_q = text(f"SELECT customer_name FROM customers WHERE customer_id = {tx.customer_id}")
            with engine.connect() as conn:
                res = conn.execute(name_q).fetchone()
                cust_name = res[0] if res else f"User {tx.customer_id}"
        except: cust_name = f"User {tx.customer_id}"

        timestamp = tx.timestamp if tx.timestamp else get_ist_time()
        insert_sql = text("""
            INSERT INTO transactions 
            (customer_id, customer_name, amount, timestamp, device_id, beneficiary_account, customer_account_number, city, payment_method_detail, is_fraud, fraud_type)
            VALUES 
            (:cust_id, :c_name, :amt, :time, :dev, :ben, :acc_num, 'Mumbai', 'API Request', :is_fraud, :f_type)
        """)
        with engine.begin() as conn:
            conn.execute(insert_sql, {
                "cust_id": tx.customer_id, "c_name": cust_name, "amt": tx.amount, "time": timestamp, 
                "dev": tx.device_id, "ben": tx.beneficiary_account, "acc_num": f"ACC_{tx.customer_id}", 
                "is_fraud": fraud_flag, "f_type": fraud_type
            })

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


# ==========================================
#   SECTION 5: GNN DEMO LOGIC
# ==========================================

@app.get("/get_customers")
def get_customers():
    try:
        with engine.connect() as conn:
            # 1. Try fetching from Customers table first (if you have metadata)
            try:
                query = text("SELECT customer_id, customer_name FROM customers ORDER BY customer_id ASC")
                result = conn.execute(query).fetchall()
                customers = [{"id": row[0], "name": row[1]} for row in result]
            except:
                # 2. Fallback: Get ALL active IDs from Transactions table
                query = text("SELECT DISTINCT customer_id FROM transactions ORDER BY customer_id ASC")
                result = conn.execute(query).fetchall()
                customers = [{"id": row[0], "name": f"User {row[0]}"} for row in result]
                
        return {"customers": customers}
    except Exception as e:
        print(f"DB Error: {e}")
        return {"error": str(e), "customers": []}

@app.post("/analyze_gnn_transaction")
def analyze_gnn_transaction(req: GNNTransactionRequest):
    try:
        nodes = []
        edges = []
        status = "APPROVED"
        msg = "Transaction Successful"
        color = "green"
        
        with engine.connect() as conn:
            # Get Names
            def get_n(i):
                r = conn.execute(text(f"SELECT customer_name FROM customers WHERE customer_id={i}")).fetchone()
                return r[0] if r else f"User {i}"
            
            s_name = get_n(req.sender_id)
            r_name = get_n(req.receiver_id)

            # ----------------------------------
            # 1. STAR TOPOLOGY (MONEY MULE)
            # ----------------------------------
            if req.scenario_type == "star":
                # Current Tx
                nodes.append({"id": req.sender_id, "label": "YOU", "color": "#10b981", "shape": "dot", "size": 25})
                nodes.append({"id": req.receiver_id, "label": r_name, "color": "#3b82f6", "shape": "dot", "size": 35})
                edges.append({"from": req.sender_id, "to": req.receiver_id, "label": f"₹{req.amount}", "arrows": "to"})

                # Fetch History (Fan-In)
                q = text(f"SELECT customer_id FROM transactions WHERE beneficiary_account = 'ACC_{req.receiver_id}' GROUP BY customer_id LIMIT 12")
                history = conn.execute(q).fetchall()
                
                fan_in = len(history)
                
                for row in history:
                    if row[0] != req.sender_id:
                        nodes.append({"id": row[0], "label": "Source", "color": "#9ca3af", "shape": "dot", "size": 10})
                        edges.append({"from": row[0], "to": req.receiver_id, "arrows": "to"})

                if req.is_gnn_active and fan_in > 3:
                    status = "BLOCKED"
                    msg = f"GNN Detected Star Topology (Degree: {fan_in})"
                    color = "red"
                    nodes[1]['color'] = "#ef4444" # Turn receiver red

            # ----------------------------------
            # 2. CIRCULAR TOPOLOGY (LAYERING)
            # ----------------------------------
            elif req.scenario_type == "cycle":
                # Current Tx (A -> B)
                nodes.append({"id": req.sender_id, "label": "YOU (A)", "color": "#10b981", "shape": "dot", "size": 25})
                nodes.append({"id": req.receiver_id, "label": f"{r_name} (B)", "color": "#3b82f6", "shape": "dot", "size": 25})
                edges.append({"from": req.sender_id, "to": req.receiver_id, "label": f"₹{req.amount}", "arrows": "to"})

                # Check for the Loop (B -> C -> A)
                # We specifically look if B paid someone (C) who paid A
                q_trace = text(f"""
                    SELECT t1.beneficiary_account as b_to_c, t2.beneficiary_account as c_to_a 
                    FROM transactions t1
                    JOIN transactions t2 ON t1.beneficiary_account = CONCAT('ACC_', t2.customer_id)
                    WHERE t1.customer_id = {req.receiver_id} 
                    AND t2.beneficiary_account = 'ACC_{req.sender_id}'
                    LIMIT 1
                """)
                trace = conn.execute(q_trace).fetchone()

                if trace:
                    # Parse ID of 'C' from 'ACC_8003'
                    c_id = int(trace[0].replace("ACC_", ""))
                    c_name = get_n(c_id)

                    # Add Node C
                    nodes.append({"id": c_id, "label": f"{c_name} (C)", "color": "#ef4444", "shape": "dot", "size": 25})
                    
                    # Add Ghost Edges (History)
                    edges.append({"from": req.receiver_id, "to": c_id, "label": "Layer 2", "arrows": "to", "dashes": True})
                    edges.append({"from": c_id, "to": req.sender_id, "label": "Kickback", "arrows": "to", "color": {"color": "red"}, "width": 3})

                    if req.is_gnn_active:
                        status = "BLOCKED"
                        msg = "GNN Detected 3-Hop Circular Loop (A->B->C->A)"
                        color = "red"

            # ----------------------------------
            # 3. SYNTHETIC IDENTITY (DEVICE FARM)
            # ----------------------------------
            elif req.scenario_type == "device":
                # 1. Find Device ID of Sender
                q_dev = text(f"SELECT device_id FROM transactions WHERE customer_id = {req.sender_id} LIMIT 1")
                res = conn.execute(q_dev).fetchone()
                dev_id = res[0] if res else "Unknown_Device"

                # 2. Count Users on this Device
                q_farm = text(f"SELECT DISTINCT customer_id FROM transactions WHERE device_id = '{dev_id}' LIMIT 15")
                farm_users = [r[0] for r in conn.execute(q_farm).fetchall()]
                
                # Nodes
                # Center Node is DEVICE (Square)
                nodes.append({"id": "DEV", "label": f"📱 {dev_id}", "color": "#f59e0b", "shape": "square", "size": 40})
                
                # Sender Node
                nodes.append({"id": req.sender_id, "label": "YOU", "color": "#ef4444", "shape": "dot", "size": 20})
                edges.append({"from": req.sender_id, "to": "DEV", "label": "Login", "dashes": True})

                # Other Farm Bots
                for uid in farm_users:
                    if uid != req.sender_id:
                        nodes.append({"id": uid, "label": f"Bot {uid}", "color": "#ef4444", "shape": "dot", "size": 15})
                        edges.append({"from": uid, "to": "DEV", "dashes": True})

                if req.is_gnn_active and len(farm_users) > 2:
                    status = "BLOCKED"
                    msg = f"GNN Detected Device Farm ({len(farm_users)} Users on 1 Device)"
                    color = "red"
                else:
                    # Normal visual if no farm
                    nodes = [{"id": req.sender_id, "label": "YOU", "color": "#10b981"}, {"id": req.receiver_id, "label": r_name, "color": "#3b82f6"}]
                    edges = [{"from": req.sender_id, "to": req.receiver_id}]

            # SAVE RESULT
            if status == "BLOCKED": is_fraud = 1 
            else: is_fraud = 0
            
            conn.execute(text("INSERT INTO transactions (customer_id, amount, timestamp, device_id, beneficiary_account, customer_account_number, city, is_fraud, fraud_type) VALUES (:c, :a, :t, :d, :b, :acc, 'Mumbai', :f, :ft)"),
            {"c": req.sender_id, "a": req.amount, "t": datetime.now(), "d": "DEMO_DEV", "b": f"ACC_{req.receiver_id}", "acc": f"ACC_{req.sender_id}", "f": is_fraud, "ft": f"GNN_{req.scenario_type.upper()}"})
            conn.commit()

        return {"status": status, "message": msg, "verdict_color": color, "graph_data": {"nodes": nodes, "edges": edges}}

    except Exception as e:
        print(f"GNN Error: {e}")
        return {"status": "ERROR", "message": str(e), "graph_data": {"nodes": [], "edges": []}}

# ==========================================
#   SECTION 6: PATTERN RECOGNITION DEMO
#   (Connected to Random Forest Model)
# ==========================================

# 6.1 GET CUSTOMER DETAILS (Includes Avg Spend)
@app.post("/get_customer_details")
def get_customer_details(req: CustomerDetailRequest):
    try:
        with engine.connect() as conn:
            # Beneficiary Query with Average Spend
            ben_q = text(f"""
                SELECT beneficiary_account, CAST(AVG(amount) AS INT) as avg_spend 
                FROM transactions 
                WHERE customer_id = {req.customer_id} 
                GROUP BY beneficiary_account 
                ORDER BY COUNT(*) DESC LIMIT 3
            """)
            ben_data = conn.execute(ben_q).fetchall()
            
            beneficiaries = []
            if ben_data:
                for r in ben_data:
                    beneficiaries.append({"account": r[0], "avg_spend": r[1]})
            
            # Usual Context
            ctx_q = text(f"""
                SELECT device_id, city, 
                mode() WITHIN GROUP (ORDER BY EXTRACT(HOUR FROM timestamp)) as usual_hour
                FROM transactions 
                WHERE customer_id = {req.customer_id}
                GROUP BY device_id, city
                ORDER BY COUNT(*) DESC LIMIT 1
            """)
            ctx = conn.execute(ctx_q).fetchone()
            
            return {
                "status": "success",
                "beneficiaries": beneficiaries,
                "usual_device": ctx[0] if ctx else "Unknown",
                "usual_city": ctx[1] if ctx else "Unknown",
                "usual_hour": int(ctx[2]) if ctx and ctx[2] is not None else 12
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 6.2 ANALYZE PATTERN (Fixed Toggle Logic)
@app.post("/analyze_pattern_transaction")
def analyze_pattern_transaction(req: PatternRequest):
    try:
        reasons = []
        rf_score = 0.0
        is_fraud = 0
        status = "APPROVED"
        color = "green"
        msg = "Transaction Verified"
        final_risk_percent = 0

        # --- 1. GLOBAL TOGGLE CHECK ---
        # If the Pattern Guard is OFF, we bypass all checks immediately.
        if not req.is_active:
            msg = "Pattern Guard Disabled"
            color = "gray"
            # final_risk_percent remains 0
            # is_fraud remains 0
            
        else:
            # Engine is ON: Proceed with Analysis
            
            # A. VELOCITY OVERRIDE (Demo Simulation)
            if req.is_velocity_attack:
                rf_score = 0.99
                reasons.append("🚀 Velocity Spike (15 txns/sec)")
            
            else:
                # B. AMOUNT SPIKE CHECK
                avg_q = text(f"SELECT AVG(amount) FROM transactions WHERE customer_id={req.customer_id}")
                with engine.connect() as conn:
                    avg_val = conn.execute(avg_q).fetchone()[0] or 0
                
                if avg_val > 0 and req.amount > (avg_val * 2):
                    rf_score += 0.55
                    reasons.append(f"💰 Amount > 2x Avg")
                elif req.amount > 200000:
                    rf_score += 0.4
                    reasons.append("💰 High Value")

                # C. CONTEXT CHECKS
                if req.device_id == "UNSEEN_DEVICE_X":
                    rf_score += 0.45
                    reasons.append("📱 New Device")
                
                if req.city != "HOME" and req.city != "Mumbai":
                    rf_score += 0.50
                    reasons.append(f"✈️ Bad Location")

                # D. RANDOM FOREST SCORING
                base_features, _ = get_live_features(req.customer_id, req.amount, req.device_id)
                model_input = base_features + [365]
                model_score, _ = pattern_engine.assess(model_input)
                
                # Combine Scores
                final_score = (model_score * 0.3) + rf_score
                if final_score > 0.99: final_score = 0.99
                rf_score = final_score

            # Calculate Final Score
            final_risk_percent = int(rf_score * 100)

            # Determine Verdict
            if final_risk_percent > 50:
                status = "BLOCKED"
                color = "red"
                is_fraud = 1
                if not reasons: reasons.append("Pattern Match")
                msg = " + ".join(reasons)
            else:
                status = "APPROVED"
                msg = "Transaction Verified"
                color = "green"

        # --- 2. SAVE TO DB ---
        timestamp = get_ist_time()
        
        # Safety chop for DB column limit (50 chars)
        db_reason = msg if is_fraud else "None"
        if len(db_reason) > 50: db_reason = db_reason[:47] + "..."

        with engine.begin() as conn:
            res = conn.execute(text(f"SELECT customer_name FROM customers WHERE customer_id = {req.customer_id}")).fetchone()
            c_name = res[0] if res else f"User {req.customer_id}"
            
            conn.execute(text("""
                INSERT INTO transactions 
                (customer_id, customer_name, amount, timestamp, device_id, beneficiary_account, customer_account_number, city, payment_method_detail, is_fraud, fraud_type)
                VALUES (:c, :cn, :a, :t, :d, :b, :acc, :city, 'Pattern Check', :f, :ft)
            """), {
                "c": req.customer_id, "cn": c_name, "a": req.amount, "t": timestamp, "d": req.device_id,
                "b": req.beneficiary_account, "acc": f"ACC_{req.customer_id}", "city": req.city,
                "f": is_fraud, "ft": db_reason
            })

        return {
            "status": status, 
            "message": msg, 
            "score": final_risk_percent, 
            "verdict_color": color
        }

    except Exception as e:
        print(f"Pattern Error: {e}")
        return {"status": "ERROR", "message": str(e), "score": 0}
    
# ==========================================
#   SECTION 7: ANOMALY DEMO (Shell Hunter)
# ==========================================

class AnomalyRequest(BaseModel):
    vendor_name: str
    amount: float

@app.post("/analyze_anomaly_transaction")
def analyze_anomaly_transaction(req: AnomalyRequest):
    try:
        # 1. SIMULATE VENDOR HISTORY (The "Features")
        # In a real app, we would query the vendor's transaction history DB.
        
        if "Shell" in req.vendor_name or "Apex" in req.vendor_name:
            # SHELL PROFILE: Huge Money, No Bills
            total_volume = 50000000 # 5 Crores
            opex_bills = 0          # No Rent, No Electricity
            avg_txn_size = 2500000  # Huge chunks
        else:
            # LEGIT PROFILE: Healthy Mix
            total_volume = 15000000 # 1.5 Crores
            opex_bills = 450000     # Pays Rent/Salaries
            avg_txn_size = 5000     # Normal mix
            
        # 2. CALCULATE ISOLATION METRICS
        # Feature A: OpEx Ratio (Healthy companies are usually > 5%)
        opex_ratio = (opex_bills / total_volume) * 100 if total_volume > 0 else 0
        
        # Feature B: Concentration Risk (Is volume just 1-2 big hits?)
        # (Simplified logic for demo)
        
        # 3. ISOLATION FOREST LOGIC (Simplified Deterministic Math)
        # Real IsoForest would give a score between -1 and 1.
        # We simulate that score based on the OpEx signature.
        
        if opex_ratio < 0.1: 
            # ANOMALY: Ghost Entity
            iso_score = -0.85 # Strongly Negative = Anomaly
            status = "BLOCKED"
            verdict = "Shell Company Signature"
            reason = "Entity has High Volume but ZERO Operational Footprint (No Rent/Utilities detected)."
            color = "red"
        else:
            # NORMAL: In-Distribution
            iso_score = 0.65 # Positive = Normal
            status = "APPROVED"
            verdict = "Legitimate Business"
            reason = f"Entity has healthy OpEx Ratio ({opex_ratio:.1f}%). Matches standard business cluster."
            color = "green"

        # 4. SAVE TO DB
        timestamp = get_ist_time()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO transactions 
                (customer_id, customer_name, amount, timestamp, device_id, beneficiary_account, city, payment_method_detail, is_fraud, fraud_type)
                VALUES (8821, 'Rohan Das', :a, :t, 'Auditor_PC', :b, 'Mumbai', 'Vendor Audit', :f, :ft)
            """), {
                "a": req.amount, "t": timestamp, "b": req.vendor_name, 
                "f": 1 if status == "BLOCKED" else 0, 
                "ft": verdict if status == "BLOCKED" else "None"
            })

        return {
            "status": status,
            "verdict": verdict,
            "reason": reason,
            "iso_score": iso_score,
            "opex_ratio": opex_ratio,
            "verdict_color": color
        }

    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
    

# ==========================================
#   SECTION 8: SCENARIO PROFILING (Feature Store)
# ==========================================

@app.post("/get_profile_timeline")
def get_profile_timeline(req: CustomerDetailRequest):
    try:
        with engine.connect() as conn:
            # Query matches image_da5b64.png exactly
            query = text(f"""
                SELECT 
                    grand_total, active_days, 
                    global_daily_avg, global_weekly_avg, 
                    global_monthly_avg, global_yearly_avg
                FROM profile_timeline 
                WHERE customer_id = {req.customer_id}
            """)
            row = conn.execute(query).fetchone()
            
            if not row:
                return {"status": "empty", "timeline": []}
            
            # Format data for the frontend
            data = [{
                "grand_total": f"₹ {row[0]:,.2f}",
                "active_days": row[1],
                "daily_avg": f"₹ {row[2]:,.2f}",
                "weekly_avg": f"₹ {row[3]:,.2f}",
                "monthly_avg": f"₹ {row[4]:,.2f}",
                "yearly_avg": f"₹ {row[5]:,.2f}"
            }]
            
            return {"status": "success", "timeline": data}
    except Exception as e:
        print(f"Timeline Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/get_profile_beneficiary")
def get_profile_beneficiary(req: CustomerDetailRequest):
    try:
        with engine.connect() as conn:
            # Query matches image_da5ba5.png exactly
            query = text(f"""
                SELECT 
                    beneficiary_account, total_amount, txn_count, 
                    active_days, daily_avg, weekly_avg, 
                    monthly_avg, yearly_avg
                FROM profile_beneficiary 
                WHERE customer_id = {req.customer_id}
                ORDER BY total_amount DESC
            """)
            result = conn.execute(query).fetchall()
            
            data = []
            for row in result:
                data.append({
                    "beneficiary": row[0],
                    "total": f"₹ {row[1]:,.2f}",
                    "count": row[2],
                    "days": row[3],
                    "daily": f"₹ {row[4]:,.2f}",
                    "weekly": f"₹ {row[5]:,.2f}",
                    "monthly": f"₹ {row[6]:,.2f}",
                    "yearly": f"₹ {row[7]:,.2f}"
                })
                
            if not data:
                return {"status": "empty", "beneficiaries": []}

            return {"status": "success", "beneficiaries": data}
    except Exception as e:
        print(f"Beneficiary Error: {e}")
        return {"status": "error", "message": str(e)}
    
# ==========================================
#   SECTION 9: VOLUME SIMULATOR (2x Rule)
# ==========================================

class VolumeRequest(BaseModel):
    customer_id: int
    amount: float
    period: str # "Daily", "Weekly", "Monthly", "Yearly"

@app.post("/simulate_volume_check")
def simulate_volume_check(req: VolumeRequest):
    try:
        with engine.connect() as conn:
            # 1. Fetch the user's specific averages
            query = text(f"""
                SELECT global_daily_avg, global_weekly_avg, global_monthly_avg, global_yearly_avg
                FROM profile_timeline 
                WHERE customer_id = {req.customer_id}
            """)
            row = conn.execute(query).fetchone()
            
            if not row:
                return {"status": "error", "message": "Profile not found. Run data pipeline first."}

            # 2. Select the correct average based on dropdown
            avg_map = {
                "Daily": row[0],
                "Weekly": row[1],
                "Monthly": row[2],
                "Yearly": row[3]
            }
            # Handle None/Null values in DB
            limit = float(avg_map.get(req.period, 0) or 0)
            
            # Default fallback if history is 0 (to avoid blocking everything)
            if limit == 0: limit = 1000 

            # 3. THE RULE: Block if > 2x Average
            threshold = limit * 2
            
            if req.amount > threshold:
                status = "BLOCKED"
                msg = f"Volume Breach! ₹{req.amount:,.0f} > 2x {req.period} Avg (₹{limit:,.0f})"
                is_fraud = 1
            else:
                status = "APPROVED"
                msg = f"Safe. Amount within limit (Limit: ₹{threshold:,.0f})"
                is_fraud = 0

            # 4. Save Transaction to DB
            timestamp = get_ist_time()
            res = conn.execute(text(f"SELECT customer_name FROM customers WHERE customer_id = {req.customer_id}")).fetchone()
            c_name = res[0] if res else f"User {req.customer_id}"
            
            conn.execute(text("""
                INSERT INTO transactions 
                (customer_id, customer_name, amount, timestamp, device_id, beneficiary_account, city, payment_method_detail, is_fraud, fraud_type)
                VALUES (:c, :cn, :a, :t, 'Sim_Device', 'VOLUME_TEST', 'Mumbai', 'Volume Check', :f, :ft)
            """), {
                "c": req.customer_id, "cn": c_name, "a": req.amount, "t": timestamp, 
                "f": is_fraud, "ft": f"{req.period} Volume Spike" if is_fraud else "None"
            })

            return {
                "status": status, 
                "message": msg, 
                "threshold": threshold,
                "avg_used": limit
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    

    # ==========================================
#   SECTION 10: BENEFICIARY SIMULATOR (Relationship Limits)
# ==========================================

class BeneficiaryVolumeRequest(BaseModel):
    customer_id: int
    beneficiary_account: str
    amount: float
    period: str # "Daily", "Weekly", "Monthly", "Yearly"

@app.post("/simulate_beneficiary_volume_check")
def simulate_beneficiary_volume_check(req: BeneficiaryVolumeRequest):
    try:
        with engine.connect() as conn:
            # 1. Fetch specific relationship stats
            query = text(f"""
                SELECT daily_avg, weekly_avg, monthly_avg, yearly_avg
                FROM profile_beneficiary 
                WHERE customer_id = {req.customer_id} 
                AND beneficiary_account = '{req.beneficiary_account}'
            """)
            row = conn.execute(query).fetchone()
            
            if not row:
                return {"status": "error", "message": "No history for this beneficiary."}

            # 2. Select Average
            avg_map = {
                "Daily": row[0],
                "Weekly": row[1],
                "Monthly": row[2],
                "Yearly": row[3]
            }
            limit = float(avg_map.get(req.period, 0) or 0)
            
            # Default safe limit if history is 0
            if limit == 0: limit = 5000 

            # 3. Apply 2x Rule
            threshold = limit * 2
            
            if req.amount > threshold:
                status = "BLOCKED"
                msg = f"Relationship Breach! ₹{req.amount:,.0f} > 2x {req.period} Avg to {req.beneficiary_account} (Limit: ₹{threshold:,.0f})"
                is_fraud = 1
            else:
                status = "APPROVED"
                msg = f"Safe. Amount fits normal relationship pattern."
                is_fraud = 0

            # 4. Save to DB
            timestamp = get_ist_time()
            res = conn.execute(text(f"SELECT customer_name FROM customers WHERE customer_id = {req.customer_id}")).fetchone()
            c_name = res[0] if res else f"User {req.customer_id}"
            
            conn.execute(text("""
                INSERT INTO transactions 
                (customer_id, customer_name, amount, timestamp, device_id, beneficiary_account, city, payment_method_detail, is_fraud, fraud_type)
                VALUES (:c, :cn, :a, :t, 'Sim_Device', :b, 'Mumbai', 'Beneficiary Check', :f, :ft)
            """), {
                "c": req.customer_id, "cn": c_name, "a": req.amount, "t": timestamp, 
                "b": req.beneficiary_account, "f": is_fraud, 
                "ft": f"Relationship Spike ({req.period})" if is_fraud else "None"
            })

            return {
                "status": status, 
                "message": msg, 
                "threshold": threshold
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    # ==========================================
#   SECTION 11: BENEFICIARY SIMULATOR (Relationship Limits - 2.5x Rule)
# ==========================================

class BenSimRequest(BaseModel):
    customer_id: int
    beneficiary_account: str
    amount: float
    period: str # "Daily", "Weekly", "Monthly", "Yearly"

@app.post("/simulate_beneficiary_volume_check")
def simulate_beneficiary_volume_check(req: BenSimRequest):
    try:
        with engine.connect() as conn:
            # 1. Fetch specific relationship stats for this pair
            query = text(f"""
                SELECT daily_avg, weekly_avg, monthly_avg, yearly_avg
                FROM profile_beneficiary 
                WHERE customer_id = {req.customer_id} 
                AND beneficiary_account = '{req.beneficiary_account}'
            """)
            row = conn.execute(query).fetchone()
            
            if not row:
                return {"status": "error", "message": "Relationship history not found."}

            # 2. Select the relevant average based on input period
            avg_map = {
                "Daily": row[0],
                "Weekly": row[1],
                "Monthly": row[2],
                "Yearly": row[3]
            }
            # Handle potential None values from DB
            limit = float(avg_map.get(req.period, 0) or 0)
            
            # If no history exists for that specific period, set a low default safety limit
            if limit == 0: limit = 1000 

            # 3. APPLY THE 2.5x RULE
            threshold = limit * 2.5
            
            if req.amount > threshold:
                status = "BLOCKED"
                msg = f"Relationship Breach! ₹{req.amount:,.0f} exceeds 2.5x {req.period} average to {req.beneficiary_account}. (Limit: ₹{threshold:,.0f})"
                is_fraud = 1
            else:
                status = "APPROVED"
                msg = f"Safe. Amount is within 2.5x relationship limits."
                is_fraud = 0

            # 4. Save Transaction to DB for logging
            timestamp = get_ist_time()
            res = conn.execute(text(f"SELECT customer_name FROM customers WHERE customer_id = {req.customer_id}")).fetchone()
            c_name = res[0] if res else f"User {req.customer_id}"
            
            conn.execute(text("""
                INSERT INTO transactions 
                (customer_id, customer_name, amount, timestamp, device_id, beneficiary_account, city, payment_method_detail, is_fraud, fraud_type)
                VALUES (:c, :cn, :a, :t, 'Sim_Device', :b, 'Mumbai', 'Ben. Volume Check', :f, :ft)
            """), {
                "c": req.customer_id, "cn": c_name, "a": req.amount, "t": timestamp, 
                "b": req.beneficiary_account, "f": is_fraud, 
                "ft": f"Relationship Spike ({req.period})" if is_fraud else "None"
            })

            return {
                "status": status, 
                "message": msg, 
                "threshold": threshold
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}