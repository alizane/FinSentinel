import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="FinSentinel: Overview", layout="wide", page_icon="🏦")
DB_CONN = 'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db'

if st.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=5)
def load_data():
    try:
        engine = create_engine(DB_CONN)
        try:
            df = pd.read_sql('SELECT * FROM v_enriched_transactions ORDER BY timestamp DESC', engine)
        except:
            df = pd.read_sql('SELECT * FROM transactions ORDER BY timestamp DESC', engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        if 'customer_name' not in df.columns: df['customer_name'] = "User_" + df['customer_id'].astype(str)
        return df
    except Exception as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame()

df = load_data()

col_logo, col_title = st.columns([1, 6])
with col_title:
    st.title("🏦 Bank Performance & Financial Crime Dashboard")
    st.markdown("Monitoring: **Mules, Shells, Synthetics, Loops, Velocity Spikes, Location Hopping**")

if not df.empty:
    st.markdown("#### 🔍 Global Filters")
    fc = st.columns(4)
    if 'city' in df.columns:
        cities = ["All"] + sorted(df['city'].dropna().unique().tolist())
        sel_loc = fc[0].selectbox("City", cities)
    else: sel_loc = "All"
    
    period = fc[1].selectbox("Granularity", ('All Time', 'Yearly', 'Quarterly', 'Monthly', 'Daily'))
    
    df_f = df.copy()
    if sel_loc != "All": df_f = df_f[df_f['city'] == sel_loc]
    
    # Time Filters
    years = sorted(df_f['timestamp'].dt.year.unique(), reverse=True)
    if period == 'Yearly':
        sy = fc[2].selectbox("Year", years)
        df_f = df_f[df_f['timestamp'].dt.year == sy]
        t_group = 'month_str'
    elif period == 'Quarterly':
        sy = fc[2].selectbox("Year", years)
        sq = fc[3].selectbox("Quarter", ['Q1','Q2','Q3','Q4'])
        df_f = df_f[(df_f['timestamp'].dt.year == sy) & (df_f['timestamp'].dt.quarter == int(sq[1]))]
        t_group = 'month_str'
    elif period == 'Monthly':
        sy = fc[2].selectbox("Year", years)
        sm = fc[3].selectbox("Month", range(1,13))
        df_f = df_f[(df_f['timestamp'].dt.year == sy) & (df_f['timestamp'].dt.month == sm)]
        t_group = 'date_str'
    elif period == 'Daily':
        sd = fc[2].date_input("Date")
        df_f = df_f[df_f['timestamp'].dt.date == sd]
        t_group = 'hour'
    else: t_group = 'month_str'

    df_f['month_str'] = df_f['timestamp'].dt.strftime('%Y-%m')
    df_f['date_str'] = df_f['timestamp'].dt.strftime('%Y-%m-%d')
    df_f['hour'] = df_f['timestamp'].dt.hour.astype(str) + ":00"

    # KPIs
    fraud_df = df_f[df_f['is_fraud'] == 1]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Transactions", f"{len(df_f):,}")
    k2.metric("Volume", f"₹{df_f['amount'].sum():,.0f}")
    k3.metric("Alerts", f"{len(fraud_df):,}", delta="Threats", delta_color="inverse")
    k4.metric("Saved", f"₹{fraud_df['amount'].sum():,.0f}", delta="Blocked", delta_color="normal")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🛡️ Attack Vector Distribution**")
        if not fraud_df.empty:
            cmap = {
                'Star Topology (Mule)': '#FF5252',
                'Shell Company (Zombie)': '#FF7043',
                'Synthetic Identity': '#AB47BC',
                'Circular Topology': '#FFCA28',
                'Location Hopping': '#26C6DA',
                'Amount/Velocity Spike': '#EF5350'
            }
            fig = px.pie(fraud_df, names='fraud_type', title='Crime Types', hole=0.4, color='fraud_type', color_discrete_map=cmap)
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No active threats.")

    with c2:
        st.markdown("**💰 Volume Trend**")
        trend = df_f.groupby(t_group).size().reset_index(name='Count')
        fig = px.area(trend, x=t_group, y='Count', title="Txn Flow")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🚨 Live Incident Log")
    if not fraud_df.empty:
        cols = ['timestamp', 'customer_id', 'customer_name', 'amount', 'fraud_type', 'city']
        vcols = [c for c in cols if c in fraud_df.columns]
        def hl(v): return f'color: red; font-weight: bold'
        st.dataframe(fraud_df[vcols].head(10).style.applymap(hl, subset=['fraud_type']), use_container_width=True)

    with st.expander("ℹ️ Crime Typologies"):
        st.markdown("""
        1. **Mule (Star):** Fan-in money transfer to one account.
        2. **Shell (Zombie):** High Volume, Zero Utility Payments.
        3. **Synthetic:** Device Farm attacks.
        4. **Layering (Circular):** A->B->C->A loops.
        5. **Location Hopping:** Impossible travel speed between cities.
        6. **Velocity Spike:** Sudden massive amount deviation.
        """)

   
    # --- WATCHLIST ---
    st.markdown("---")
    st.write("**⚠️ Top Risk Entities (Watchlist)**")
    if not fraud_df.empty:
        st.dataframe(fraud_df[['customer_id', 'customer_name', 'amount', 'fraud_type']].sort_values('amount', ascending=False).head(5), use_container_width=True)
    else:
        st.success("✅ Watchlist Clear.")

else: st.warning("Run Data Generator.")