import streamlit as st
from sqlalchemy import create_engine, text
import subprocess
import sys
import pandas as pd

# --- DATABASE CONFIGURATION ---
DB_USER = 'postgres'
DB_PASSWORD = 'Hiking%40786'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'fraud_detection_db'

try:
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
except Exception as e:
    st.error(f"Failed to connect to database: {e}")
    st.stop()

def get_table_counts():
    """Fetches the current row counts from raw transactions and profile tables."""
    counts = {
        "transactions": 0,
        "profile_beneficiary": 0,
        "profile_location": 0,
    }
    try:
        with engine.connect() as conn:
            counts["transactions"] = conn.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
            counts["profile_beneficiary"] = conn.execute(text("SELECT COUNT(*) FROM profile_customer_beneficiary")).scalar()
            counts["profile_location"] = conn.execute(text("SELECT COUNT(*) FROM profile_customer_location")).scalar()
    except Exception as e:
        st.error(f"Error querying table counts: {e}")
    return counts

def fetch_table_preview(table_name, limit=5):
    """Fetches the first few rows of a table as a DataFrame."""
    try:
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        return df
    except Exception as e:
        st.error(f"Error fetching preview for {table_name}: {e}")
        return pd.DataFrame()

st.set_page_config(layout="wide")
st.title("Data Pipeline Control Panel")

if st.button("Run Pipeline (Refresh Profiles)"):
    st.info("Starting pipeline refresh...")
    try:
        process = subprocess.run(
            [sys.executable, "run_pipeline.py"],
            capture_output=True, text=True, check=True
        )
        st.success("Pipeline refresh completed successfully!")
        st.code(process.stdout)
    except Exception as e:
        st.error(f"Pipeline failed to run: {e}")

st.divider()

# --- Pipeline Status Dashboard ---
st.header("Pipeline Status Dashboard")
counts = get_table_counts()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Raw Data Tables")
    st.metric(label="Total Raw Transactions", value=f"{counts['transactions']:,}")

with col2:
    st.subheader("Profile / Output Tables")
    st.metric(label="Customer-Beneficiary Profiles", value=f"{counts['profile_beneficiary']:,}")
    st.metric(label="Customer-Location Profiles", value=f"{counts['profile_location']:,}")

st.button("Refresh Status")

st.divider()

# --- Fraud Detection Scenarios ---
st.header("📈 Fraud Detection Scenarios")
scenario_data = {
    "Scenario": ["Amount Spike", "New Beneficiary", "Geo-Location Anomaly"],
    "Rule / Logic": [
        "Is transaction amount > profile's `monthly_avg_amount`?",
        "Is the beneficiary not found in the `profile_customer_beneficiary` table?",
        "Is the transaction city not found in the `profile_customer_location` table?"
    ]
}
st.dataframe(pd.DataFrame(scenario_data), use_container_width=True)

st.divider()

# --- Data Table Previews ---
st.header("📄 Data Table Previews")

with st.expander("Output Table Preview: `profile_customer_beneficiary` (with all time-based stats)"):
    st.dataframe(fetch_table_preview("profile_customer_beneficiary"), use_container_width=True)

with st.expander("Output Table Preview: `profile_customer_location` (with all time-based stats)"):
    st.dataframe(fetch_table_preview("profile_customer_location"), use_container_width=True)
    