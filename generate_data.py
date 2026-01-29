import pandas as pd
from sqlalchemy import create_engine, text # <-- IMPORT TEXT
from faker import Faker
import random
from datetime import datetime, timedelta
import numpy as np

# --- 1. DATABASE & SCRIPT CONFIGURATION ---
DB_USER = 'postgres'
DB_PASSWORD = 'Hiking%40786'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'fraud_detection_db'

# --- 2. FAKER INSTANCES ---
fake = Faker('en_IN')
fake_international = Faker()

# --- 3. DATA GENERATION PARAMETERS ---
NUM_CUSTOMERS = 30
START_DATE = datetime(2017, 1, 1)
# Use a current end date to ensure weekly/monthly stats are not zero
END_DATE = datetime.now()

# --- SQL Command to drop dependent views ---
DROP_VIEWS_COMMAND = """
    DROP MATERIALIZED VIEW IF EXISTS profile_customer_beneficiary;
    DROP MATERIALIZED VIEW IF EXISTS profile_customer_location;
"""

# --- 4. GENERATE CUSTOMER & KYC BASE (No changes here) ---
print(f"Generating base data for {NUM_CUSTOMERS} customers and KYC records...")
customers = []
kyc_data = []
for i in range(NUM_CUSTOMERS):
    cust_id = 1000 + i
    cust_city = fake.city()
    cust_pincode = fake.postcode()
    cust_open_date = fake.date_between(start_date=datetime(2010, 1, 1), end_date=datetime(2016, 12, 31))
    customers.append({
        'customer_id': cust_id, 'customer_name': fake.name(), 'customer_account_number': fake.bban(),
        'age': random.randint(18, 70), 'email': fake.email(), 'city': cust_city,
        'pincode': cust_pincode, 'account_open_date': cust_open_date
    })
    kyc_data.append({
        'kyc_id': 7000 + i, 'customer_id': cust_id, 'pan_number': fake.pystr_format('?????####?').upper(),
        'aadhaar_number': fake.numerify('############'), 'nominee_name': fake.name(),
        'kyc_address': f"{fake.street_address()}, {cust_city}, {cust_pincode}",
        'kyc_date_verified': fake.date_between(start_date=cust_open_date, end_date=cust_open_date + timedelta(days=5))
    })
customer_df = pd.DataFrame(customers)
kyc_df = pd.DataFrame(kyc_data)
print("Customer base and KYC data created.")

# --- 5. GENERATE TRANSACTION HISTORY (No changes here) ---
print(f"Generating transactions from {START_DATE.date()} to {END_DATE.date()}...")
transactions = []
transaction_id_counter = 1
for _, customer in customer_df.iterrows():
    known_beneficiaries = []
    for _ in range(random.randint(5, 15)):
        known_beneficiaries.append({
            "id": 2000 + random.randint(1, 500), "name": fake.name(),
            "added_on": fake.date_time_between(start_date=customer['account_open_date'], end_date=START_DATE)
        })
    num_transactions = random.randint(200, 1000)
    for _ in range(num_transactions):
        tx_timestamp = fake.date_time_between(start_date=START_DATE, end_date=END_DATE)
        beneficiary = random.choice(known_beneficiaries)
        is_fraud_flag = 0; fraud_type_label = 'None'
        tx_amount = np.random.normal(loc=10000, scale=5000)
        lat, lon = fake.latitude(), fake.longitude()
        tx_device = random.choice(['Android', 'iOS', 'Windows'])
        tx_city = customer['city']
        if random.random() < 0.06:
            is_fraud_flag = 1
            fraud_pattern = random.choice(['Amount Spike', 'Time Anomaly', 'New Beneficiary', 'Geo-Velocity'])
            if fraud_pattern == 'New Beneficiary':
                fraud_type_label = 'New Beneficiary'
                tx_amount *= random.uniform(3, 8)
                beneficiary = {
                    "id": 9000 + random.randint(1, 100), "name": fake.name(),
                    "added_on": tx_timestamp - timedelta(minutes=random.randint(5, 60))
                }
            elif fraud_pattern == 'Amount Spike':
                tx_amount *= random.uniform(10, 20)
                fraud_type_label = 'Amount Spike'
            elif fraud_pattern == 'Time Anomaly':
                tx_timestamp = tx_timestamp.replace(hour=random.randint(1, 5))
                fraud_type_label = 'Time Anomaly'
            elif fraud_pattern == 'Geo-Velocity':
                fraud_type_label = 'Geo-Velocity'
                lat, lon = fake_international.latitude(), fake_international.longitude()
                tx_city = fake_international.city()
                tx_device = 'Linux'
        beneficiary_age_days = (tx_timestamp.date() - beneficiary['added_on'].date()).days
        account_age_days = (tx_timestamp.date() - customer['account_open_date']).days
        hour = tx_timestamp.hour
        if 5 <= hour < 12: time_of_day = 'Morning'
        elif 12 <= hour < 17: time_of_day = 'Afternoon'
        elif 17 <= hour < 22: time_of_day = 'Evening'
        else: time_of_day = 'Night'
        is_international = random.random() < 0.1
        if is_international:
            beneficiary_city = fake_international.city(); beneficiary_timezone = fake_international.timezone(); currency = 'USD'
        else:
            beneficiary_city = fake.city(); beneficiary_timezone = 'Asia/Kolkata'; currency = 'INR'
        transactions.append({
            'transaction_id': transaction_id_counter, 'timestamp': tx_timestamp, 'amount': round(max(50, tx_amount), 2),
            'is_fraud': is_fraud_flag, 'fraud_type': fraud_type_label, 'customer_id': customer['customer_id'],
            'latitude': lat, 'longitude': lon, 'city': tx_city,
            'beneficiary_id': beneficiary['id'], 'currency': currency, 'transaction_type': random.choice(['Net Banking', 'Deposit', 'Cheque']),
            'payment_method_detail': random.choice(['Google Pay', 'Paytm', 'PhonePe']), 'transaction_status': 'Completed',
            'beneficiary_name': beneficiary['name'], 'beneficiary_account_number': fake.bban(), 'device_used': tx_device,
            'ip_address': fake.ipv4(), 'beneficiary_city': beneficiary_city, 'beneficiary_timezone': beneficiary_timezone,
            'is_international_transfer': 1 if is_international else 0, 'time_of_day': time_of_day, 'account_age_days': account_age_days,
            'beneficiary_age_days': beneficiary_age_days
        })
        transaction_id_counter += 1
transactions_df = pd.DataFrame(transactions)
print("Transaction history generated.")

# --- 6. MERGE DATA (No changes here) ---
final_df = pd.merge(transactions_df, customer_df.rename(columns={'city':'customer_home_city', 'pincode':'customer_pincode'}), on='customer_id')
final_column_order = [
    'customer_id', 'customer_name', 'customer_account_number', 'age', 'email', 'customer_home_city', 'customer_pincode', 'account_open_date', 'account_age_days',
    'transaction_id', 'timestamp', 'time_of_day', 'amount', 'currency', 'is_international_transfer', 'transaction_type', 'payment_method_detail', 'transaction_status',
    'device_used', 'ip_address', 'city', 'latitude', 'longitude', 'is_fraud', 'fraud_type',
    'beneficiary_id', 'beneficiary_name', 'beneficiary_account_number', 'beneficiary_city', 'beneficiary_timezone', 'beneficiary_age_days'
]
final_df = final_df[final_column_order]
print("Columns reordered for logical flow.")

# --- 7. CONNECT TO POSTGRESQL & SAVE ---
print(f"Connecting to PostgreSQL database '{DB_NAME}'...")
try:
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

    # <-- NEW: Drop the materialized views first
    with engine.connect() as connection:
        print("Dropping dependent materialized views before replacing tables...")
        connection.execute(text(DROP_VIEWS_COMMAND))
        connection.commit()

    # This will now succeed because the views are gone
    final_df.to_sql('transactions', engine, if_exists='replace', index=False)
    print(f"Successfully wrote {len(final_df)} rows to 'transactions' table.")
    
    kyc_df.to_sql('kyc', engine, if_exists='replace', index=False)
    print(f"Successfully wrote {len(kyc_df)} rows to 'kyc' table.")
    
    print("\n✅ Success!")
    print(f"Both 'transactions' and 'kyc' tables have been recreated.")
    print("Next Step: Recreate your materialized views in pgAdmin, then run the pipeline.")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")