import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
import subprocess
import sys
# NEW: Import your central engine logic
from database import get_engine

st.set_page_config(page_title="Pipeline Admin", layout="wide", page_icon="⚙️")

# REPLACED: Hardcoded DB_CONN and engine setup removed
# This now pulls credentials from your .env file
engine = get_engine()

st.title("⚙️ Data Pipeline Control Panel")

col_btn, col_info = st.columns([1, 3])
with col_btn:
    if st.button("🚀 Run Full System Reset", type="primary"):
        with st.spinner("Resetting DB, Generating Data & Rebuilding Views..."):
            try:
                process = subprocess.run([sys.executable, "generate_data.py"], capture_output=True, text=True)
                if process.returncode == 0:
                    st.success("✅ System Reset Complete!")
                    st.rerun()
                else:
                    st.error("❌ Failed.")
                    st.code(process.stderr)
            except Exception as e:
                st.error(f"Error: {e}")

with col_info:
    st.info("Drops tables, generates 100k+ rows, injects 6 Fraud Scenarios, calculates profiles.")

st.divider()

# Status
def get_count(table):
    try:
        # UPDATED: Using the central engine for status counts
        with engine.connect() as conn:
            return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    except:
        return 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Transactions", f"{get_count('transactions'):,}")
c2.metric("Beneficiary Profiles", f"{get_count('profile_beneficiary'):,}")
c3.metric("Timeline Profiles", f"{get_count('profile_timeline'):,}")
c4.metric("Device Profiles", f"{get_count('profile_device_usage'):,}")

st.divider()

# Feature Store Viewer
st.subheader("📊 Feature Engineering Output (Profile Tables)")
tab1, tab2, tab3, tab4 = st.tabs(["Beneficiary Profile", "Timeline Profile", "Device Profile", "Raw Transactions"])

with tab1:
    st.write("Tracks A -> B relationship strength (Daily/Weekly/Monthly/Yearly Avgs).")
    try:
        st.dataframe(pd.read_sql("SELECT * FROM profile_beneficiary LIMIT 50", engine), use_container_width=True)
    except: st.warning("No data.")

with tab2:
    st.write("Tracks Global Spending Velocity per Customer.")
    try:
        st.dataframe(pd.read_sql("SELECT * FROM profile_timeline LIMIT 50", engine), use_container_width=True)
    except: st.warning("No data.")

with tab3:
    st.write("Tracks Digital Fingerprints.")
    try:
        st.dataframe(pd.read_sql("SELECT * FROM profile_device_usage LIMIT 50", engine), use_container_width=True)
    except: st.warning("No data.")

with tab4:
    try:
        st.dataframe(pd.read_sql("SELECT * FROM transactions ORDER BY transaction_id DESC LIMIT 50", engine), use_container_width=True)
    except: st.warning("No data.")