import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from PIL import Image

# Version: 1.0
# Last Updated: 2025-10-01
# Description: Complete customer 360° view page with summary, all filters, correct layout, and 4 graphs.

st.set_page_config(page_title="Customer 360° View", layout="wide", page_icon="👤")

@st.cache_data
def load_data():
    engine = create_engine(f'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db')
    df = pd.read_sql('SELECT * FROM v_enriched_transactions', engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df = load_data()

# --- HEADER WITH LOGO ---
col1, col2 = st.columns([1, 6])
with col1:
    try:
        image = Image.open('sbi_logo.png')
        st.image(image, width=120)
    except FileNotFoundError:
        st.warning("logo not found.")
with col2:
    st.title("Customer 360° View")

# --- CUSTOMER SELECTION ---
customer_info_df = df[['customer_name', 'customer_id']].drop_duplicates().sort_values('customer_name')
customer_info_df['display_name'] = customer_info_df['customer_name'] + " (ID: " + customer_info_df['customer_id'].astype(str) + ")"
selected_display_name = st.selectbox("Select a Customer to Analyze", customer_info_df['display_name'])

if selected_display_name:
    selected_customer_name = selected_display_name.split(" (ID:")[0]
    df_customer = df[df['customer_name'] == selected_customer_name].copy()
    
    st.info(f"**Account:** {df_customer.iloc[0]['customer_account_number']} | **City:** {df_customer.iloc[0]['city']}")
    
    # --- CUSTOMER SUMMARY SECTION ---
    st.markdown("##### Customer Profile Summary")
    if not df_customer.empty:
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Avg. Transaction", f"₹{df_customer['amount'].mean():,.2f}")
        s2.metric("Preferred Payment", df_customer['payment_method_detail'].mode()[0])
        s3.metric("Peak Time", df_customer['time_of_day'].mode()[0])
        s4.metric("Top Beneficiary", df_customer['beneficiary_name'].mode()[0])
    
    st.markdown("---")
    
    # --- ADVANCED FILTERS ---
    st.subheader("Advanced Filters")
    
    st.write("**Time Period**")
    time_filter_cols = st.columns(4)
    period_type = time_filter_cols[0].selectbox("Filter by", ('Yearly', 'Quarterly', 'Monthly', 'Daily', 'Custom Date'), key='cust_period_type')
    
    df_filtered = df_customer.copy()
    years = sorted(df_customer['timestamp'].dt.year.unique(), reverse=True)
    
    if period_type in ['Yearly', 'Quarterly', 'Monthly']:
        selected_year = time_filter_cols[1].selectbox("Year", years, key='cust_year')
        df_filtered = df_filtered[df_filtered['timestamp'].dt.year == selected_year]
        if period_type == 'Quarterly':
            all_quarters = ['Q1', 'Q2', 'Q3', 'Q4']
            selected_q_str = time_filter_cols[2].selectbox("Quarter", all_quarters, key='cust_q')
            q_num = int(selected_q_str.replace("Q", ""))
            df_filtered = df_filtered[df_filtered['timestamp'].dt.quarter == q_num]
        if period_type == 'Monthly':
            month_map = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            selected_m_name = time_filter_cols[2].selectbox("Month", list(month_map.values()), key='cust_m')
            m_num = list(month_map.keys())[list(month_map.values()).index(selected_m_name)]
            df_filtered = df_filtered[df_filtered['timestamp'].dt.month == m_num]
    elif period_type == 'Daily':
        selected_date = time_filter_cols[1].date_input("Select a date", value=df_filtered['timestamp'].max().date())
        df_filtered = df_filtered[df_filtered['timestamp'].dt.date == selected_date]
    elif period_type == 'Custom Date':
        start_date = time_filter_cols[1].date_input("Start date", value=df_filtered['timestamp'].min().date())
        end_date = time_filter_cols[2].date_input("End date", value=df_filtered['timestamp'].max().date())
        df_filtered = df_filtered[(df_filtered['timestamp'].dt.date >= start_date) & (df_filtered['timestamp'].dt.date <= end_date)]

    st.write("**Other Filters**")
    other_filter_cols = st.columns(4)
    locations = ["All"] + sorted(df_customer['city'].unique())
    selected_location = other_filter_cols[0].selectbox("Location", locations)
    tt_options = ["All"] + list(df_customer['transaction_type'].unique())
    selected_types = other_filter_cols[1].multiselect("Transaction Type", tt_options, default=["All"])
    fraud_status = other_filter_cols[2].selectbox("Fraud Status", ["All", "Fraudulent Only", "Non-Fraudulent Only"])
    ben_options = ["All"] + sorted(list(df_customer['beneficiary_name'].unique()))
    selected_beneficiaries = other_filter_cols[3].multiselect("Beneficiaries", ben_options, default=["All"])

    if selected_location != "All": df_filtered = df_filtered[df_filtered['city'] == selected_location]
    if "All" not in selected_types: df_filtered = df_filtered[df_filtered['transaction_type'].isin(selected_types)]
    if "All" not in selected_beneficiaries: df_filtered = df_filtered[df_filtered['beneficiary_name'].isin(selected_beneficiaries)]
    if fraud_status != "All":
        is_fraud_filter = 1 if fraud_status == "Fraudulent Only" else 0
        df_filtered = df_filtered[df_filtered['is_fraud'] == is_fraud_filter]
        
    st.markdown("---")
    
    if not df_filtered.empty:
        # 1. Key Metrics
        st.subheader("Key Metrics (Based on Filters)")
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Transactions", f"{df_filtered.shape[0]:,}")
        kpi2.metric("Total Amount (INR)", f"₹{df_filtered['amount'].sum():,.2f}")
        kpi3.metric("Fraudulent Transactions", f"{df_filtered[df_filtered['is_fraud'] == 1].shape[0]:,}")

        # 2. Transaction History Table
        st.subheader("Filtered Transaction History")
        st.dataframe(df_filtered)
        st.markdown("---")
        
        # 3. Four Graphs
        st.subheader("Visual Analysis")
        fraud_df_cust = df_filtered[df_filtered['is_fraud'] == 1]
        if not fraud_df_cust.empty:
            st.write("**Fraud Pattern Analysis for this Customer**")
            fraud_summary_cust = fraud_df_cust.groupby('fraud_type')['amount'].agg(['count', 'sum']).reset_index().sort_values(by='count', ascending=False)
            fraud_summary_cust.columns = ['Fraud Pattern', 'Count', 'Total Amount (INR)']
            st.table(fraud_summary_cust)
        
        st.markdown("---")
        
        g1, g2 = st.columns(2)
        with g1:
            st.write("**Fraud vs Non-Fraud**")
            fraud_counts = df_filtered['is_fraud'].value_counts().reset_index()
            fraud_counts['is_fraud'] = fraud_counts['is_fraud'].map({1: 'Fraudulent', 0: 'Non-Fraudulent'})
            fig_pie = px.pie(fraud_counts, names='is_fraud', values='count', hole=0.3, color_discrete_map={'Fraudulent':'#EF553B', 'Non-Fraudulent':'#636EFA'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
            st.write("**Payment Method Usage**")
            payment_counts = df_filtered['payment_method_detail'].value_counts().reset_index()
            fig_payment = px.bar(payment_counts, x='payment_method_detail', y='count')
            st.plotly_chart(fig_payment, use_container_width=True)

        with g2:
            st.write("**Deposits vs. Payouts**")
            df_filtered['flow'] = df_filtered['transaction_type'].apply(lambda x: 'Deposit' if x == 'Deposit' else 'Payout')
            flow_summary = df_filtered.groupby('flow')['amount'].sum().reset_index()
            fig_flow = px.bar(flow_summary, x='flow', y='amount', color='flow')
            st.plotly_chart(fig_flow, use_container_width=True)

            st.write("**Transaction Amounts (by Fraud Type)**")
            df_filtered['plot_label'] = df_filtered['fraud_type'].apply(lambda x: x if x != 'None' else 'Non-Fraudulent')
            fig_scatter = px.scatter(df_filtered, x='timestamp', y='amount', color='plot_label')
            st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("No transactions match the selected filters.")