import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# 1. Config & Setup
st.set_page_config(page_title="Customer 360", page_icon="👤", layout="wide")
DB_CONN = 'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db'

# Create a global engine for direct queries later
engine = create_engine(DB_CONN)

@st.cache_data
def load_data():
    try:
        # We use a separate connection for the initial load
        conn = create_engine(DB_CONN)
        try:
            df = pd.read_sql("SELECT * FROM v_enriched_transactions", conn)
        except:
            df = pd.read_sql("SELECT * FROM transactions", conn)
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# 2. Main Title
st.title("👤 Customer 360° Forensics")
df = load_data()

if not df.empty:
    col_search, col_time = st.columns([1, 2])
    
    # --- Sidebar / Top Bar Selection ---
    with col_search:
        subjects = df[['customer_id', 'customer_name']].drop_duplicates().sort_values('customer_id')
        options = subjects.apply(lambda x: f"{x['customer_name']} (ID: {x['customer_id']})", axis=1)
        selected_option = st.selectbox("Select Target Subject", options)
        selected_id = int(selected_option.split("(ID: ")[1].replace(")", ""))

    cust_data_raw = df[df['customer_id'] == selected_id]

    if not cust_data_raw.empty:
        with col_time:
            # Time Filter Logic
            period_type = st.radio("Timeframe", ('All Time', 'Yearly', 'Quarterly', 'Monthly'), horizontal=True)
            cust_data = cust_data_raw.copy()
            years = sorted(cust_data['timestamp'].dt.year.unique(), reverse=True)
            
            if period_type == 'Yearly':
                sel_year = st.selectbox("Select Year", years)
                cust_data = cust_data[cust_data['timestamp'].dt.year == sel_year]
            elif period_type == 'Quarterly':
                sel_year = st.selectbox("Select Year", years)
                sel_q = st.selectbox("Quarter", ['Q1', 'Q2', 'Q3', 'Q4'])
                q_num = int(sel_q.replace("Q",""))
                cust_data = cust_data[(cust_data['timestamp'].dt.year == sel_year) & (cust_data['timestamp'].dt.quarter == q_num)]
            elif period_type == 'Monthly':
                sel_year = st.selectbox("Select Year", years)
                sel_month = st.selectbox("Month", range(1,13))
                cust_data = cust_data[(cust_data['timestamp'].dt.year == sel_year) & (cust_data['timestamp'].dt.month == sel_month)]

        # --- Profile Header (Metrics) ---
        st.markdown("---")
        city = cust_data.iloc[0]['city'] if 'city' in cust_data.columns else "Unknown"
        fraud_tx = cust_data[cust_data['is_fraud'] == 1]
        
        if not fraud_tx.empty:
            status = "🔴 HIGH RISK"
            reason = fraud_tx['fraud_type'].mode()[0]
            st.error(f"⚠️ Flagged for **{reason}**")
        else:
            status = "🟢 Low Risk"
            reason = "Clean"

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Customer ID", selected_id)
        k2.metric("Home Branch", city)
        k3.metric("Volume", f"₹{cust_data['amount'].sum():,.2f}")
        k4.metric("Status", status, delta=reason, delta_color="inverse" if not fraud_tx.empty else "normal")

        st.markdown("---")

        if not cust_data.empty:
            # --- Visualizations ---
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("📉 Spending Trend")
                cust_data['date'] = cust_data['timestamp'].dt.strftime('%Y-%m-%d')
                trend = cust_data.groupby('date')['amount'].sum().reset_index()
                fig = px.line(trend, x='date', y='amount')
                st.plotly_chart(fig, use_container_width=True)

            with g2:
                st.subheader("🕸️ Beneficiary Network")
                ben_col = 'beneficiary_account'
                ben = cust_data.groupby(ben_col)['amount'].sum().reset_index().head(10)
                fig = px.bar(ben, x='amount', y=ben_col, orientation='h')
                st.plotly_chart(fig, use_container_width=True)

            # --- LEDGER SECTION ---
            st.subheader("📄 Ledger (Filtered View)")
            
            def highlight_fraud(row):
                return ['background-color: #ffe6e6']*len(row) if row.get('is_fraud')==1 else ['']*len(row)
            
            st.dataframe(
                cust_data.sort_values('timestamp', ascending=False).style.apply(highlight_fraud, axis=1), 
                use_container_width=True
            )

            # --- NEW FEATURE STORE VIEWER SECTION (Below Ledger) ---
            st.markdown("---")
            st.subheader("📊 Feature Engineering Output (Profile Tables)")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Beneficiary Profile", "Timeline Profile", "Device Profile", "All Transactions"])

            with tab1:
                st.caption(f"A -> B relationship strength for Customer {selected_id}")
                try:
                    # Filtered by selected_id
                    query = f"SELECT * FROM profile_beneficiary WHERE customer_id = {selected_id}"
                    st.dataframe(pd.read_sql(query, engine), use_container_width=True)
                except Exception as e: st.warning("No beneficiary profile data found.")

            with tab2:
                st.caption(f"Global Spending Velocity for Customer {selected_id}")
                try:
                    # Filtered by selected_id
                    query = f"SELECT * FROM profile_timeline WHERE customer_id = {selected_id}"
                    st.dataframe(pd.read_sql(query, engine), use_container_width=True)
                except: st.warning("No timeline profile data found.")

            with tab3:
                st.caption(f"Digital Fingerprints for Customer {selected_id}")
                try:
                    # Filtered by selected_id
                    query = f"SELECT * FROM profile_device_usage WHERE customer_id = {selected_id}"
                    st.dataframe(pd.read_sql(query, engine), use_container_width=True)
                except: st.warning("No device profile data found.")

            with tab4:
                st.caption(f"Full Transaction History (Unfiltered by Time slider) for Customer {selected_id}")
                try:
                    # Filtered by selected_id, but showing last 50 transactions regardless of the Time Slider above
                    query = f"SELECT * FROM transactions WHERE customer_id = {selected_id} ORDER BY timestamp DESC LIMIT 50"
                    st.dataframe(pd.read_sql(query, engine), use_container_width=True)
                except: st.warning("No transaction data found.")

        else:
            st.info("No transactions in selected period.")
    else:
        st.warning("No history found for this customer.")
else:
    st.warning("Data not available.")