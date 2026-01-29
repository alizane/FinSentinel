# Version: 1.2
# Description: Fixed the results display to show reasons as clean bullet points.

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import requests
import json

st.set_page_config(page_title="Fraud Simulation", layout="wide", page_icon="🔬")

# ... (load_data function remains the same)
@st.cache_data
def get_customer_data():
    engine = create_engine(f'postgresql://postgres:Hiking%40786@localhost:5432/fraud_detection_db')
    df = pd.read_sql('SELECT customer_name, amount, beneficiary_name, device_used FROM transactions WHERE is_fraud = 0', engine)
    return df

all_data = get_customer_data()
customer_list = sorted(all_data['customer_name'].unique())


st.title("Real-Time Transaction Analysis")
# ... (Layout and form are the same)
st.markdown("Select a customer to see their normal behavior, then craft a transaction to test the detection engine.")
st.markdown("---")
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("1. Select a Customer")
    selected_customer = st.selectbox("Customer Name", customer_list)
    st.markdown("---")
    if selected_customer:
        st.subheader(f"Normal Behavior Profile: {selected_customer}")
        customer_history = all_data[all_data['customer_name'] == selected_customer]
        avg_amount = customer_history['amount'].mean()
        max_amount = customer_history['amount'].max()
        known_devices = customer_history['device_used'].unique()
        top_beneficiaries = customer_history['beneficiary_name'].value_counts().head(5)
        st.metric("Average Transaction Amount", f"₹{avg_amount:,.2f}")
        st.metric("Historical Maximum Amount", f"₹{max_amount:,.2f}")
        with st.expander("**Known Devices**"):
            st.json(list(known_devices))
        with st.expander("**Top 5 Known Beneficiaries**"):
            st.table(top_beneficiaries)

with col2:
    st.subheader("2. Simulate a New Transaction")
    with st.form("transaction_form"):
        amount = st.number_input("Transaction Amount (INR)", min_value=1.0, value=5000.0, step=100.0)
        beneficiary = st.text_input("Beneficiary Name", "Test Beneficiary LLC")
        device = st.selectbox("Device Type", ["Android", "iOS", "Windows", "MacOS", "Linux"])
        submitted = st.form_submit_button("ANALYZE TRANSACTION")
    st.markdown("---")

    if submitted:
        st.subheader("3. Analysis Result")
        api_url = "http://127.0.0.1:8000/analyze_transaction/"
        transaction_data = { "customer_name": selected_customer, "amount": amount, "beneficiary_name": beneficiary, "device": device }
        
        with st.spinner('Contacting Fraud Detection API...'):
            try:
                response = requests.post(api_url, data=json.dumps(transaction_data))
                if response.status_code == 200:
                    result = response.json()
                    verdict = result.get("verdict")
                    reasons = result.get("reasons")
                    
                    if "High Risk" in verdict: st.error(f"**Verdict: {verdict} 🚨**")
                    elif "Medium Risk" in verdict: st.warning(f"**Verdict: {verdict} ⚠️**")
                    else: st.success(f"**Verdict: {verdict} ✅**")
                    
                    # FIX: Display reasons as a clean bulleted list
                    st.write("**Why? The system detected the following patterns:**")
                    for reason in reasons:
                        st.markdown(f"- {reason}")
                else:
                    st.error(f"Error from API: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Connection Error: Could not connect to the FastAPI server. Is it running?")