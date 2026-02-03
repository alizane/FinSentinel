import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from faker import Faker
import random
from datetime import datetime, timedelta

# --- CONFIGURATION ---
DB_CONN = 'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db'
NUM_TRANSACTIONS = 105000 
faker = Faker('en_IN') # Indian Names

engine = create_engine(DB_CONN)

def calculate_time_period(hour):
    if 5 <= hour < 12: return 'Morning'
    elif 12 <= hour < 17: return 'Afternoon'
    elif 17 <= hour < 22: return 'Evening'
    else: return 'Night'

def master_setup():
    print("🚀 STARTING MASTER SYSTEM RESET & SETUP...")

    # ==========================================
    # 1. CLEAN SLATE
    # ==========================================
    print("\n🗑️  Step 1: Cleaning Database...")
    with engine.connect() as conn:
        conn.commit()
        conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS profile_beneficiary CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS profile_timeline CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS profile_device_usage CASCADE"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS profile_customer_stats CASCADE"))
        conn.commit()

    # ==========================================
    # 2. SCHEMA CREATION
    # ==========================================
    print("🛠️  Step 2: Creating Tables...")
    with engine.connect() as conn:
        conn.commit()
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
    # 3. GENERATE REALISTIC RAW DATA
    # ==========================================
    print(f"⏳ Step 3: Generating {NUM_TRANSACTIONS} realistic transactions...")
    data = []
    
    # 3.1 Pre-generate Customers (Consistent IDs 1000+)
    customers = {}
    customer_beneficiaries = {} # Sticky beneficiaries
    
    for cid in range(1000, 6000):
        customers[cid] = faker.name()
        # Assign 3-5 favorite beneficiaries to this customer to ensure A->B count > 1
        customer_beneficiaries[cid] = [f"ACC_{random.randint(1000, 9999)}" for _ in range(random.randint(3, 5))]

    opex_categories = ['Electricity Bill', 'Rent', 'Broadband', 'Zomato', 'Groceries', 'Uber']
    vendor_categories = ['Vendor Payment', 'Consulting Fee', 'Logistics', 'Raw Materials']
    cities_pool = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad']

    for _ in range(NUM_TRANSACTIONS):
        cid = random.randint(1000, 5999) # Pick existing customer
        is_opex = random.random() < 0.2
        category = random.choice(opex_categories) if is_opex else random.choice(vendor_categories)
        
        # 80% chance to pay a known beneficiary (Higher A-B Count), 20% random
        if random.random() < 0.8:
            ben_acc = random.choice(customer_beneficiaries[cid])
        else:
            ben_acc = f"ACC_{random.randint(1000, 9999)}"

        row = {
            "customer_id": cid,
            "customer_name": customers[cid],
            "amount": round(random.uniform(100, 20000), 2),
            "timestamp": faker.date_time_between(start_date='-1y', end_date='now'),
            "device_id": f"Device_{cid}_{random.randint(1, 2)}", # Real users have 1-2 devices
            "beneficiary_account": ben_acc,
            "customer_account_number": f"ACC_{cid}",
            "city": random.choice(cities_pool),
            "payment_method_detail": category,
            "is_fraud": 0,
            "fraud_type": "None"
        }
        data.append(row)

    # --- INJECT 6 FRAUD SCENARIOS ---
    print("💉 Injecting 6 Types of Financial Crime...")

    # 1. STAR TOPOLOGY (Mule) - High Fan In
    mule_acc = "MULE_ACC_99"
    for i in range(20):
        cid = random.randint(1000, 5000)
        data.append({
            "customer_id": cid, "customer_name": customers[cid],
            "amount": round(random.uniform(30000, 49000), 2),
            "timestamp": datetime.now() - timedelta(hours=random.randint(1, 12)),
            "device_id": f"Device_{cid}", "beneficiary_account": mule_acc,
            "customer_account_number": f"ACC_{cid}", "city": "Mumbai",
            "payment_method_detail": "Transfer", "is_fraud": 1, "fraud_type": "Star Topology (Mule)"
        })

    # 2. SHELL COMPANY (Zero OpEx)
    shell_id = 1666
    for i in range(30):
        data.append({
            "customer_id": shell_id, "customer_name": "Apex Consultants Pvt Ltd",
            "amount": round(random.uniform(500000, 2000000), 2),
            "timestamp": faker.date_time_between(start_date='-6m', end_date='now'),
            "device_id": "HQ_Server_1", "beneficiary_account": "Offshore_Holdings",
            "customer_account_number": f"ACC_{shell_id}", "city": "Delhi",
            "payment_method_detail": "Consulting Income", "is_fraud": 1, "fraud_type": "Shell Company (Zombie)"
        })

    # 3. SYNTHETIC IDENTITY (Device Farm)
    farm_device = "OnePlus_Rooted_X"
    for i in range(10):
        cid = 7000 + i
        data.append({
            "customer_id": cid, "customer_name": faker.name(),
            "amount": 5000, "timestamp": datetime.now(),
            "device_id": farm_device, "beneficiary_account": "Farm_Admin",
            "customer_account_number": f"ACC_{cid}", "city": "Bangalore",
            "payment_method_detail": "Loan Disbursal", "is_fraud": 1, "fraud_type": "Synthetic Identity"
        })

    # 4. CIRCULAR TOPOLOGY (Layering Loop)
    # A -> B -> C -> A
    loop_time = datetime.now()
    data.append({"customer_id": 8001, "customer_name": "Rohan Das", "amount": 500000, "timestamp": loop_time, "device_id": "D1", "beneficiary_account": "ACC_8002", "customer_account_number": "ACC_8001", "city": "Mumbai", "payment_method_detail": "Invest", "is_fraud": 1, "fraud_type": "Circular Topology"})
    data.append({"customer_id": 8002, "customer_name": "Amit Verma", "amount": 500000, "timestamp": loop_time, "device_id": "D2", "beneficiary_account": "ACC_8003", "customer_account_number": "ACC_8002", "city": "Mumbai", "payment_method_detail": "Invest", "is_fraud": 1, "fraud_type": "Circular Topology"})
    data.append({"customer_id": 8003, "customer_name": "Sneha P", "amount": 500000, "timestamp": loop_time, "device_id": "D3", "beneficiary_account": "ACC_8001", "customer_account_number": "ACC_8003", "city": "Mumbai", "payment_method_detail": "Invest", "is_fraud": 1, "fraud_type": "Circular Topology"})

    # 5. LOCATION IMPERSONATION (Impossible Travel)
    # User transactions in Mumbai, then London 10 mins later
    traveler_id = 1050
    data.append({"customer_id": traveler_id, "customer_name": customers[traveler_id], "amount": 2000, "timestamp": datetime.now() - timedelta(minutes=15), "device_id": "iPhone_12", "beneficiary_account": "Starbucks_Mum", "customer_account_number": f"ACC_{traveler_id}", "city": "Mumbai", "payment_method_detail": "Food", "is_fraud": 0, "fraud_type": "None"})
    data.append({"customer_id": traveler_id, "customer_name": customers[traveler_id], "amount": 200000, "timestamp": datetime.now(), "device_id": "iPhone_12", "beneficiary_account": "Casino_Lon", "customer_account_number": f"ACC_{traveler_id}", "city": "London", "payment_method_detail": "Gambling", "is_fraud": 1, "fraud_type": "Location Hopping"})

    # 6. AMOUNT SPIKE (Velocity)
    # User usually spends 500, suddenly spends 5 Lakhs
    spike_id = 1051
    # History
    for _ in range(5):
        data.append({"customer_id": spike_id, "customer_name": customers[spike_id], "amount": 500, "timestamp": faker.date_time_between(start_date='-1M', end_date='-1d'), "device_id": "D_Spike", "beneficiary_account": "Grocery", "customer_account_number": f"ACC_{spike_id}", "city": "Pune", "payment_method_detail": "Food", "is_fraud": 0, "fraud_type": "None"})
    # The Attack
    data.append({"customer_id": spike_id, "customer_name": customers[spike_id], "amount": 500000, "timestamp": datetime.now(), "device_id": "D_Spike", "beneficiary_account": "Jeweler", "customer_account_number": f"ACC_{spike_id}", "city": "Pune", "payment_method_detail": "Luxury", "is_fraud": 1, "fraud_type": "Amount/Velocity Spike"})


    # --- SAVE ---
    print("💾 Saving data...")
    df = pd.DataFrame(data)
    df.to_sql('transactions', engine, if_exists='append', index=False)
    print("✅ Raw Data Saved.")

    # ==========================================
    # 4. RECREATE VIEWS
    # ==========================================
    print("⚙️  Step 4: Recreating Views...")
    with engine.connect() as conn:
        conn.commit()
        conn.execute(text("""
            CREATE MATERIALIZED VIEW profile_customer_stats AS
            SELECT customer_id, COUNT(transaction_id) as total_txns, SUM(amount) as total_spend, MAX(city) as primary_city
            FROM transactions GROUP BY customer_id
        """))
        conn.execute(text("""
            CREATE VIEW v_enriched_transactions AS
            SELECT t.*, p.total_spend, p.total_txns
            FROM transactions t LEFT JOIN profile_customer_stats p ON t.customer_id = p.customer_id
        """))
        conn.commit()

    # ==========================================
    # 5. ADVANCED FEATURE PROFILING
    # ==========================================
    print("📊 Step 5: generating Advanced Profiles (Daily/Weekly/Monthly/Yearly)...")
    
    # Reload for processing
    df = pd.read_sql("SELECT * FROM transactions", engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Active Days Calculation
    lifespan = df.groupby('customer_id')['timestamp'].agg(['min', 'max'])
    lifespan['active_days'] = (lifespan['max'] - lifespan['min']).dt.days.replace(0, 1)
    df = df.merge(lifespan[['active_days']], on='customer_id', how='left')

    # A. BENEFICIARY PROFILE
    ben_profile = df.groupby(['customer_id', 'beneficiary_account']).agg(
        total_amount=('amount', 'sum'),
        txn_count=('transaction_id', 'count'), 
        active_days=('active_days', 'first')
    ).reset_index()
    
    # Calculate Averages
    ben_profile['daily_avg'] = (ben_profile['total_amount'] / ben_profile['active_days']).round(2)
    ben_profile['weekly_avg'] = (ben_profile['total_amount'] / (ben_profile['active_days']/7).replace(0,1)).round(2)
    ben_profile['monthly_avg'] = (ben_profile['total_amount'] / (ben_profile['active_days']/30).replace(0,1)).round(2)
    ben_profile['yearly_avg'] = (ben_profile['total_amount'] / (ben_profile['active_days']/365).replace(0,1)).round(2)
    
    # Drop active_days before saving if you don't want to see it, but it's useful context. 
    # I'll keep it for calculation integrity.
    ben_profile.to_sql('profile_beneficiary', engine, if_exists='replace', index=False)

    # B. TIMELINE PROFILE
    time_profile = df.groupby('customer_id').agg(
        grand_total=('amount', 'sum'),
        active_days=('active_days', 'first')
    ).reset_index()
    
    time_profile['global_daily_avg'] = (time_profile['grand_total'] / time_profile['active_days']).round(2)
    time_profile['global_weekly_avg'] = (time_profile['grand_total'] / (time_profile['active_days']/7).replace(0,1)).round(2)
    time_profile['global_monthly_avg'] = (time_profile['grand_total'] / (time_profile['active_days']/30).replace(0,1)).round(2)
    time_profile['global_yearly_avg'] = (time_profile['grand_total'] / (time_profile['active_days']/365).replace(0,1)).round(2)
    
    time_profile.to_sql('profile_timeline', engine, if_exists='replace', index=False)

    # C. DEVICE PROFILE
    df['hour'] = df['timestamp'].dt.hour
    df['time_of_day'] = df['hour'].apply(calculate_time_period)
    
    dev_counts = df.groupby(['customer_id', 'device_id']).size().reset_index(name='count')
    most_used = dev_counts.sort_values(['customer_id', 'count'], ascending=[True, False]).groupby('customer_id').head(1)
    most_used.rename(columns={'device_id': 'favorite_device'}, inplace=True)
    
    time_counts = df.pivot_table(index='customer_id', columns='time_of_day', values='transaction_id', aggfunc='count', fill_value=0).reset_index()
    device_profile = pd.merge(most_used[['customer_id', 'favorite_device']], time_counts, on='customer_id')
    device_profile.to_sql('profile_device_usage', engine, if_exists='replace', index=False)

    print("🎉 FULL SYSTEM COMPLETE.")

if __name__ == "__main__":
    master_setup()