import streamlit as st
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FinSentinel AI",
    page_icon="🛡️",
    layout="wide"
)

# --- SIDEBAR INFO ---
st.sidebar.success("Select a module above to begin.")
st.sidebar.info("🎓 Major Project 2026")

# --- MAIN CONTENT ---
col1, col2 = st.columns([1, 2])

with col1:
    try:
        # Ensure 'sbi_logo.png' is in your main folder
        image = Image.open('sbi_logo.png')
        st.image(image, width=200)
    except FileNotFoundError:
        st.info("Logo Placeholder")

with col2:
    st.title("FinSentinel: ML-Driven Fraud Detection")
    st.markdown("### Next-Gen Financial Crime Prevention Core")
    st.markdown("**V3 Architecture: Hybrid Tribunal (Random Forest + Isolation Forest + GNN)**")

st.markdown("---")

# --- TEAM INFO (Simple Version - No Pandas needed) ---
st.subheader("👨‍💻 Project Team")

st.markdown("### 🏫 Fr. Conceicao Rodrigues College of Engineering")
st.markdown("**🎓 Guided By:** Prof. Sachin Narkhede")

st.markdown("---")
st.markdown("### 🛠️ Student Developers")

c1, c2 = st.columns(2)

with c1:
    st.write("**Name**")
    st.write("1. Ansari Allauddin")
    st.write("2. Kaushal Mahajan")
    st.write("3. Kartik Dhar")

with c2:
    st.write("**Roll No**")
    st.write("9876")
    st.write("9554")
    st.write("9530")

# --- PROJECT OVERVIEW ---
st.header("🚀 Project Mission")
st.markdown("""
**FinSentinel** is a comprehensive financial security suite designed to detect sophisticated white-collar crimes. 
It utilizes a **'Tribunal'** of three distinct AI models to analyze transactions, detect money laundering rings, and flag synthetic identities in real-time.
""")

st.markdown("---")

# --- SYSTEM MODULES (2x2 GRID) ---
st.subheader("📂 System Modules")

# ROW 1
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.info("**1. The Face (User App)**")
    st.markdown("### 📱 App Simulator")
    st.caption("A 'PhonePe' clone to simulate live user transactions. Use this to inject 'Ghost' and 'Mule' attacks.")
    st.markdown("👉 **Go to: App Simulator**")

with row1_col2:
    st.error("**2. The Brain (Bank Dashboard)**")
    st.markdown("### 🏦 Global Overview")
    st.caption("The Command Center. View global transaction volume, fraud heatmaps, and 'Zombie' company alerts.")
    st.markdown("👉 **Go to: Overview**")

# ROW 2
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.warning("**3. The Tribunal (Live Detection)**")
    st.markdown("### ⚡ Real-Time Tribunal")
    st.caption("Watch the 3 Judges (Historian, Auditor, Sheriff) vote on a single transaction in real-time.")
    st.markdown("👉 **Go to: Real-Time Detection**")

with row2_col2:
    st.success("**4. The Guts (Forensics & Admin)**")
    st.markdown("### ⚙️ Pipeline & Customer 360")
    st.caption("Manage the ETL pipeline, database views, and perform deep-dive audits on suspicious customers.")
    st.markdown("👉 **Go to: Pipeline Admin / Customer 360**")

st.markdown("---")

# --- TECH STACK ---
st.subheader("🛠️ Technology Stack")
t1, t2, t3, t4 = st.columns(4)
t1.metric("Frontend", "Streamlit UI")
t2.metric("Backend", "FastAPI + Python")
t3.metric("Database", "PostgreSQL")
t4.metric("AI Models", "RF + IsoForest + GNN")

st.markdown("---")

