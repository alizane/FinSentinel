import pandas as pd
from sqlalchemy import create_engine, text

class NetworkModel:
    def __init__(self, db_conn):
        self.engine = create_engine(db_conn)
    
    def investigate(self, device_id, customer_id, beneficiary_account, amount):
        """
        Role: Graph Topology Analysis (GNN Logic)
        Checks: Mules (Star), Laundering (Cycles), Synthetic (Bipartite)
        """
        risk_score = 0.0
        reasons = []
        
        # 1. SYNTHETIC IDENTITY (Device Collisions)
        try:
            q_syn = f"SELECT COUNT(DISTINCT customer_id) FROM transactions WHERE device_id = '{device_id}'"
            user_count = pd.read_sql(q_syn, self.engine).iloc[0, 0]
            
            if user_count > 3:
                risk_score += 1.0
                reasons.append(f"Device Collision: {user_count} identities on device '{device_id}'")
        except Exception as e:
            print(f"Network Error (Syn): {e}")

        # 2. MONEY MULE (Star Topology / High Fan-In)
        try:
            q_mule = f"""
                SELECT COUNT(DISTINCT customer_id) 
                FROM transactions 
                WHERE beneficiary_account = '{beneficiary_account}' 
                AND timestamp > NOW() - INTERVAL '24 HOURS'
            """
            fan_in_count = pd.read_sql(q_mule, self.engine).iloc[0, 0]
            
            if fan_in_count >= 5:
                risk_score += 1.0
                reasons.append(f"Mule Node: '{beneficiary_account}' receiving from {fan_in_count} sources")
        except Exception as e:
            print(f"Network Error (Mule): {e}")

        # 3. CIRCULAR TRADING (Graph Cycles)
        try:
            # Check A -> B -> A
            q_loop = f"""
                SELECT COUNT(*) FROM transactions 
                WHERE customer_account_number = '{beneficiary_account}' 
                AND beneficiary_account = (SELECT customer_account_number FROM customers WHERE customer_id = {customer_id})
            """
            direct_loop = pd.read_sql(q_loop, self.engine).iloc[0, 0]
            
            if direct_loop > 0:
                risk_score += 1.0
                reasons.append("Cycle Detected: A->B->A Loop")
        except Exception as e:
            pass

        verdict = "Clean"
        if risk_score > 0:
            verdict = "Network Topology Risk"
            risk_score = 1.0
            
        return risk_score, verdict, reasons