import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from faker import Faker
import random
from datetime import datetime, timedelta

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
DB_CONN = 'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db'
NUM_TRANSACTIONS = 105000  # Fixed as requested
NUM_CUSTOMERS = 5000       # Pool of distinct users
faker = Faker('en_IN')     # Indian Names context

engine = create_engine(DB_CONN)

def calculate_time_period(hour):
    if 5 <= hour < 12: return 'Morning'
    elif 12 <= hour < 17: return 'Afternoon'
    elif 17 <= hour < 22: return 'Evening'
    else: return 'Night'

def master_setup():
    print("🚀 STARTING MASTER DATA GENERATION (HIGH FRAUD DENSITY MODE)...")

    # ==========================================
    # 2. CLEAN SLATE & SCHEMA
    # ==========================================
    print("\n🗑️  Step 1: Resetting Database Schema...")
    with engine.connect() as conn:
        conn.commit()
        # Clean up old tables
        conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS customers CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS profile_beneficiary CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS profile_timeline CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS profile_device_usage CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS profile_customer_stats CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS v_enriched_transactions CASCADE"))
        conn.commit()

        # Create Tables
        print("🛠️  Step 2: Creating Tables...")
        conn.execute(text("""
            CREATE TABLE customers (
                customer_id BIGINT PRIMARY KEY,
                customer_name VARCHAR(100),
                risk_score INT DEFAULT 0
            );
        """))

        conn.execute(text("""
            CREATE TABLE transactions (
                transaction_id SERIAL PRIMARY KEY,
                customer_id BIGINT,
                customer_name VARCHAR(100),
                amount FLOAT,
                timestamp TIMESTAMP,
                device_id VARCHAR(50),
                beneficiary_account VARCHAR(50),
                customer_account_number VARCHAR(50),
                city VARCHAR(50),
                payment_method_detail VARCHAR(50),
                is_fraud INT,
                fraud_type VARCHAR(50)
            );
        """))
        conn.commit()

    # ==========================================
    # 3. DEFINE ACTORS (The "Cast")
    # ==========================================
    print(f"👥 Step 3: Pre-assigning Fraud Roles to specific Customers...")
    
    # We create a pool of IDs
    all_ids = list(range(1000, 1000 + NUM_CUSTOMERS))
    
    # --- ASSIGN ROLES (So we can find them in the Demo) ---
    # 1. THE MULE (Star Topology)
    MULE_ID = 9001
    
    # 2. THE SHELL COMPANY (Zero OpEx, High Value)
    SHELL_ID = 9002
    
    # 3. THE DEVICE FARM (Synthetic Identities)
    # 10 users sharing one device
    FARM_USERS = list(range(9010, 9020)) 
    FARM_DEVICE_ID = "ONEPLUS_ROOTED_DEV_X"
    
    # 4. THE CIRCULAR LOOP (Layering)
    # A -> B -> C -> A
    CIRCLE_USERS = [8001, 8002, 8003]
    
    # 5. THE TRAVELER (Location Hopping)
    TRAVELER_ID = 9005
    
    # 6. THE SPIKER (Velocity/Amount Spike)
    SPIKER_ID = 9006

    # Combine all special IDs into the main pool so they exist in the customer table
    special_ids = [MULE_ID, SHELL_ID, TRAVELER_ID, SPIKER_ID] + FARM_USERS + CIRCLE_USERS
    
    # Customer Metadata Dicts
    customers = {}
    cust_cities = {}
    cust_devices = {}
    cust_beneficiaries = {}
    
    cities_pool = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad']

    # Generate Profile Data
    cust_data_rows = []
    
    # Helper to generate normal users + special users
    full_population = list(set(all_ids + special_ids))
    
    for cid in full_population:
        # Name generation
        if cid == MULE_ID: name = "Rahul (The Mule)"
        elif cid == SHELL_ID: name = "Apex Global Consultants"
        elif cid in CIRCLE_USERS: name = f"Trader {cid}"
        elif cid in FARM_USERS: name = f"Bot User {cid}"
        elif cid == TRAVELER_ID: name = "Vikram Traveler"
        elif cid == SPIKER_ID: name = "Suresh Spiker"
        else: name = faker.name()
        
        city = random.choice(cities_pool)
        device = f"Dev_{cid}_{random.choice(['A','B'])}"
        
        customers[cid] = name
        cust_cities[cid] = city
        cust_devices[cid] = device
        
        # Sticky beneficiaries (Normal behavior)
        cust_beneficiaries[cid] = [f"ACC_{random.choice(full_population)}" for _ in range(3)]
        
        # Risk Score (For sorting in dropdowns later)
        risk = 90 if cid in special_ids else random.randint(0, 10)
        
        cust_data_rows.append({"customer_id": cid, "customer_name": name, "risk_score": risk})

    # Save Customer Profiles to DB
    pd.DataFrame(cust_data_rows).to_sql('customers', engine, if_exists='append', index=False)
    print("✅ Customer Profiles Created.")

    # ==========================================
    # 4. GENERATE TRANSACTIONS (The "Noise" Loop)
    # ==========================================
    print(f"⏳ Step 4: Generating {NUM_TRANSACTIONS} mixed transactions (Targeting ~8.5% Fraud)...")
    
    data = []
    opex_categories = ['Electricity Bill', 'Rent', 'Broadband', 'Zomato', 'Groceries', 'Uber']
    vendor_categories = ['Vendor Payment', 'Consulting Fee', 'Logistics', 'Raw Materials']

    # Start time: 6 months ago
    curr_time = datetime.now() - timedelta(days=180)
    
    for i in range(NUM_TRANSACTIONS):
        # Slowly advance time (random seconds jump)
        curr_time += timedelta(seconds=random.randint(30, 300))
        
        # --- PROBABILISTIC FRAUD INJECTION (Targeting ~8.5% Total) ---
        # We roll a die (0.0 to 1.0) to decide if this transaction is fraud
        roll = random.random()
        
        # 1. STAR TOPOLOGY (Mule) - 2.0% Chance
        # Random normal users sending money TO the Mule
        if roll < 0.02:
            sender = random.choice(all_ids) # Random Victim from general pool
            if sender == MULE_ID: continue
            
            row = {
                "customer_id": sender, "customer_name": customers[sender],
                "amount": round(random.uniform(25000, 48000), 2), # Just under 50k limit
                "timestamp": curr_time, "device_id": cust_devices[sender],
                "beneficiary_account": f"ACC_{MULE_ID}", # <--- THE TRAP
                "customer_account_number": f"ACC_{sender}", "city": cust_cities[sender],
                "payment_method_detail": "Transfer",
                "is_fraud": 1, "fraud_type": "Star Topology (Mule)"
            }

        # 2. SHELL COMPANY - 1.0% Chance
        # Shell company receiving big money
        elif roll < 0.03:
            row = {
                "customer_id": SHELL_ID, "customer_name": customers[SHELL_ID],
                "amount": round(random.uniform(500000, 2000000), 2), # Huge amount
                "timestamp": curr_time, "device_id": "HQ_SERVER_01",
                "beneficiary_account": "OFFSHORE_HOLDINGS_LLC",
                "customer_account_number": f"ACC_{SHELL_ID}", "city": "Delhi",
                "payment_method_detail": "Consulting Income",
                "is_fraud": 1, "fraud_type": "Shell Company (Zombie)"
            }

        # 3. SYNTHETIC IDENTITY (Device Farm) - 1.5% Chance
        # Farm bots sending money using the SHARED device
        elif roll < 0.045:
            cid = random.choice(FARM_USERS)
            row = {
                "customer_id": cid, "customer_name": customers[cid],
                "amount": round(random.uniform(5000, 9000), 2),
                "timestamp": curr_time, 
                "device_id": FARM_DEVICE_ID, # <--- SHARED DEVICE
                "beneficiary_account": "FARM_MASTER_ACC",
                "customer_account_number": f"ACC_{cid}", "city": "Bangalore",
                "payment_method_detail": "Loan Disbursal",
                "is_fraud": 1, "fraud_type": "Synthetic Identity"
            }

        # 4. CIRCULAR TOPOLOGY - 1.5% Chance
        # A -> B, B -> C, or C -> A
        elif roll < 0.06:
            step = random.randint(0, 2)
            sender = CIRCLE_USERS[step]
            receiver = CIRCLE_USERS[(step + 1) % 3]
            
            row = {
                "customer_id": sender, "customer_name": customers[sender],
                "amount": 150000.00, # Fixed layering amount
                "timestamp": curr_time, "device_id": cust_devices[sender],
                "beneficiary_account": f"ACC_{receiver}", # <--- LOOP
                "customer_account_number": f"ACC_{sender}", "city": "Mumbai",
                "payment_method_detail": "Investment",
                "is_fraud": 1, "fraud_type": "Circular Topology"
            }

        # 5. LOCATION HOPPING - 1.0% Chance
        # Traveler makes a tx in London right after Mumbai
        elif roll < 0.07:
            # We assume he just made a normal tx in Mumbai (simulated by the normal flow), now this:
            row = {
                "customer_id": TRAVELER_ID, "customer_name": customers[TRAVELER_ID],
                "amount": 250000.00,
                "timestamp": curr_time + timedelta(minutes=10), # Impossible travel time
                "device_id": cust_devices[TRAVELER_ID],
                "beneficiary_account": "CASINO_ROYALE",
                "customer_account_number": f"ACC_{TRAVELER_ID}", 
                "city": "London", # <--- IMPOSSIBLE CITY
                "payment_method_detail": "Gambling",
                "is_fraud": 1, "fraud_type": "Location Hopping"
            }

        # 6. AMOUNT SPIKE - 1.5% Chance
        # Spiker suddenly spends huge amount
        elif roll < 0.085:
            row = {
                "customer_id": SPIKER_ID, "customer_name": customers[SPIKER_ID],
                "amount": 800000.00, # Huge Spike
                "timestamp": curr_time, "device_id": cust_devices[SPIKER_ID],
                "beneficiary_account": "LUXURY_JEWELERS",
                "customer_account_number": f"ACC_{SPIKER_ID}", "city": "Pune",
                "payment_method_detail": "Jewelry",
                "is_fraud": 1, "fraud_type": "Amount/Velocity Spike"
            }

        # 7. NORMAL TRANSACTION (91.5% Chance)
        else:
            cid = random.choice(full_population)
            
            # 80% sticky beneficiary, 20% random
            if random.random() < 0.8:
                ben_acc = random.choice(cust_beneficiaries[cid])
            else:
                ben_acc = f"ACC_{random.randint(1000, 9999)}"
            
            is_opex = random.random() < 0.3
            cat = random.choice(opex_categories) if is_opex else random.choice(vendor_categories)

            row = {
                "customer_id": cid, "customer_name": customers[cid],
                "amount": round(random.uniform(100, 20000), 2),
                "timestamp": curr_time, "device_id": cust_devices[cid],
                "beneficiary_account": ben_acc,
                "customer_account_number": f"ACC_{cid}", 
                "city": cust_cities[cid],
                "payment_method_detail": cat,
                "is_fraud": 0, "fraud_type": "None"
            }

        data.append(row)
        
        # Progress Logger
        if i % 20000 == 0:
            print(f"   Generated {i}/{NUM_TRANSACTIONS} transactions...")

    # --- SAVE TO DB ---
    print("💾 Saving transactions to Database...")
    df = pd.DataFrame(data)
    df.to_sql('transactions', engine, if_exists='append', index=False)
    print("✅ Transactions Saved.")

    # ==========================================
    # 5. RECREATE VIEWS & PROFILES
    # ==========================================
    print("⚙️  Step 5: Generating Analytical Views...")
    with engine.connect() as conn:
        conn.commit()
        # Materialized View
        conn.execute(text("""
            CREATE MATERIALIZED VIEW profile_customer_stats AS
            SELECT customer_id, COUNT(transaction_id) as total_txns, SUM(amount) as total_spend, MAX(city) as primary_city
            FROM transactions GROUP BY customer_id
        """))
        # Enriched View
        conn.execute(text("""
            CREATE VIEW v_enriched_transactions AS
            SELECT t.*, p.total_spend, p.total_txns
            FROM transactions t LEFT JOIN profile_customer_stats p ON t.customer_id = p.customer_id
        """))
        conn.commit()

    # --- ADVANCED PROFILING (Pandas) ---
    print("📊 Step 6: Calculating Advanced Profiles...")
    df = pd.read_sql("SELECT * FROM transactions", engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Active Days
    lifespan = df.groupby('customer_id')['timestamp'].agg(['min', 'max'])
    lifespan['active_days'] = (lifespan['max'] - lifespan['min']).dt.days.replace(0, 1)
    df = df.merge(lifespan[['active_days']], on='customer_id', how='left')

    # A. Beneficiary Profile
    ben_profile = df.groupby(['customer_id', 'beneficiary_account']).agg(
        total_amount=('amount', 'sum'),
        txn_count=('transaction_id', 'count'), 
        active_days=('active_days', 'first')
    ).reset_index()
    ben_profile['daily_avg'] = (ben_profile['total_amount'] / ben_profile['active_days']).round(2)
    ben_profile['weekly_avg'] = (ben_profile['total_amount'] / (ben_profile['active_days']/7).replace(0,1)).round(2)
    ben_profile['monthly_avg'] = (ben_profile['total_amount'] / (ben_profile['active_days']/30).replace(0,1)).round(2)
    ben_profile['yearly_avg'] = (ben_profile['total_amount'] / (ben_profile['active_days']/365).replace(0,1)).round(2)
    ben_profile.to_sql('profile_beneficiary', engine, if_exists='replace', index=False)

    # B. Timeline Profile
    time_profile = df.groupby('customer_id').agg(
        grand_total=('amount', 'sum'),
        active_days=('active_days', 'first')
    ).reset_index()
    time_profile['global_daily_avg'] = (time_profile['grand_total'] / time_profile['active_days']).round(2)
    time_profile['global_weekly_avg'] = (time_profile['grand_total'] / (time_profile['active_days']/7).replace(0,1)).round(2)
    time_profile['global_monthly_avg'] = (time_profile['grand_total'] / (time_profile['active_days']/30).replace(0,1)).round(2)
    time_profile['global_yearly_avg'] = (time_profile['grand_total'] / (time_profile['active_days']/365).replace(0,1)).round(2)
    time_profile.to_sql('profile_timeline', engine, if_exists='replace', index=False)

    # C. Device Profile
    df['hour'] = df['timestamp'].dt.hour
    df['time_of_day'] = df['hour'].apply(calculate_time_period)
    dev_counts = df.groupby(['customer_id', 'device_id']).size().reset_index(name='count')
    most_used = dev_counts.sort_values(['customer_id', 'count'], ascending=[True, False]).groupby('customer_id').head(1)
    most_used.rename(columns={'device_id': 'favorite_device'}, inplace=True)
    time_counts = df.pivot_table(index='customer_id', columns='time_of_day', values='transaction_id', aggfunc='count', fill_value=0).reset_index()
    device_profile = pd.merge(most_used[['customer_id', 'favorite_device']], time_counts, on='customer_id')
    device_profile.to_sql('profile_device_usage', engine, if_exists='replace', index=False)

    print("\n🎉 DATA GENERATION COMPLETE.")
    print("=====================================================")
    print("📋  DEMO CHEAT SHEET (Use these IDs in your Dashboard)")
    print("=====================================================")
    print(f"🔴 STAR TOPOLOGY (Mule):       ID {MULE_ID}  (Name: Rahul The Mule)")
    print(f"🟣 SYNTHETIC ID (Device Farm): ID {FARM_USERS[0]} to {FARM_USERS[-1]} (Name: Bot User...)")
    print(f"🟡 CIRCULAR TOPOLOGY:          IDs {CIRCLE_USERS}")
    print(f"🟠 SHELL COMPANY:              ID {SHELL_ID}  (Name: Apex Global)")
    print(f"🟦 LOCATION HOPPING:           ID {TRAVELER_ID} (Name: Vikram Traveler)")
    print(f"🟥 VELOCITY SPIKE:             ID {SPIKER_ID} (Name: Suresh Spiker)")
    print("=====================================================")

if __name__ == "__main__":
    master_setup()