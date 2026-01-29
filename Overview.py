import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from PIL import Image

# Version: 1.0
# Last Updated: 2025-10-01
# Description: Complete overview page with dynamic KPIs and graphs, plus location and granular time filters.

st.set_page_config(page_title="Bank Overview", layout="wide", page_icon="🏦")

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
    st.title("Bank Performance Dashboard")
    st.markdown("High-level metrics for all customer transactions.")

# --- ADVANCED FILTERS ---
st.markdown("#### Select Filters")
filter_cols = st.columns(4)

# Location Filter
locations = ["All"] + sorted(df['city'].unique())
selected_location = filter_cols[0].selectbox("Filter by Location", locations)

# Granular Time Filters
period_type = filter_cols[1].selectbox("Filter by Time", ('Yearly', 'Quarterly', 'Monthly', 'Daily', 'Custom Date'))

df_filtered = df.copy()
if selected_location != "All":
    df_filtered = df_filtered[df_filtered['city'] == selected_location]

years = sorted(df_filtered['timestamp'].dt.year.unique(), reverse=True)

if period_type in ['Yearly', 'Quarterly', 'Monthly']:
    selected_year = filter_cols[2].selectbox("Year", years)
    df_filtered = df_filtered[df_filtered['timestamp'].dt.year == selected_year]
    if period_type == 'Quarterly':
        all_quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        selected_quarter_str = filter_cols[3].selectbox("Quarter", all_quarters)
        q_num = int(selected_quarter_str.replace("Q", ""))
        df_filtered = df_filtered[df_filtered['timestamp'].dt.quarter == q_num]
    if period_type == 'Monthly':
        month_map = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
        selected_m_name = filter_cols[3].selectbox("Month", list(month_map.values()))
        m_num = list(month_map.keys())[list(month_map.values()).index(selected_m_name)]
        df_filtered = df_filtered[df_filtered['timestamp'].dt.month == m_num]
elif period_type == 'Daily':
    selected_date = filter_cols[2].date_input("Select a date", value=df_filtered['timestamp'].max().date())
    df_filtered = df_filtered[df_filtered['timestamp'].dt.date == selected_date]
elif period_type == 'Custom Date':
    start_date = filter_cols[2].date_input("Start date", value=df_filtered['timestamp'].min().date())
    end_date = filter_cols[3].date_input("End date", value=df_filtered['timestamp'].max().date())
    df_filtered = df_filtered[(df_filtered['timestamp'].dt.date >= start_date) & (df_filtered['timestamp'].dt.date <= end_date)]

# --- KEY METRICS ---
total_transactions = df_filtered.shape[0]
total_amount = df_filtered['amount'].sum()
fraudulent_transactions = df_filtered[df_filtered['is_fraud'] == 1].shape[0]
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Transactions", f"{total_transactions:,}")
kpi2.metric("Total Amount Transacted (INR)", f"₹{total_amount:,.2f}")
kpi3.metric("Flagged Fraudulent Transactions", f"{fraudulent_transactions:,}")
st.markdown("---")

# --- VISUAL ANALYSIS ---
st.subheader("Visual Analysis")
if not df_filtered.empty:
    st.write(f"**Transaction Volume**")
    df_filtered['year'] = df_filtered['timestamp'].dt.year
    df_filtered['quarter_str'] = 'Q' + df_filtered['timestamp'].dt.quarter.astype(str)
    df_filtered['month_str'] = df_filtered['timestamp'].dt.strftime('%Y-%m')
    df_filtered['date_str'] = df_filtered['timestamp'].dt.date.astype(str)

    if period_type == 'Yearly': time_group = 'month_str'
    elif period_type == 'Quarterly': time_group = 'month_str'
    elif period_type == 'Monthly': time_group = 'date_str'
    else: time_group = 'date_str'
    
    transactions_by_time = df_filtered.groupby(time_group).size().reset_index(name='count')
    fig_line = px.line(transactions_by_time, x=time_group, y='count', title=f'Transaction Volume for Selected Period', markers=True, labels={'x': f'{period_type} Period'})
    st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")
    
    analysis1, analysis2 = st.columns(2)
    with analysis1:
        st.write("**Fraud Pattern Analysis**")
        fraud_df = df_filtered[df_filtered['is_fraud'] == 1]
        if not fraud_df.empty:
            fraud_summary = fraud_df.groupby('fraud_type')['amount'].agg(['count', 'sum']).reset_index().sort_values(by='count', ascending=False)
            fraud_summary.columns = ['Fraud Pattern', 'Count', 'Total Amount (INR)']
            st.dataframe(fraud_summary, use_container_width=True)
        else:
            st.info("No fraudulent transactions in this period.")
            
    with analysis2:
        st.write("**Fraud Count Visualization**")
        if not fraud_df.empty:
            fig_fraud_bar = px.bar(fraud_summary, x='Count', y='Fraud Pattern', orientation='h', title="Frequency of Fraud Types")
            st.plotly_chart(fig_fraud_bar, use_container_width=True)
        else:
            st.info("No fraud to visualize.")
else:
    st.warning("No data available for the selected filters.")