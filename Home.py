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
    st.markdown("**V3 Architecture: Hybrid Ensemble (Random Forest + Isolation Forest + GNN)**")

st.markdown("---")

# --- TEAM INFO ---
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
It utilizes a multi-model architecture to analyze transactions, detect money laundering rings, and flag synthetic identities in real-time.
""")

st.markdown("---")

# --- SYSTEM MODULES (Technical Naming) ---
st.subheader("📂 System Architecture Modules")

# ROW 1: Analytics & Explainability
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.info("**1. Global Overview**")
    st.markdown("### 🏦 Analytics Dashboard")
    st.caption("Primary Command Center. View global transaction volume, fraud heatmaps, and high-level alert statistics.")
    st.markdown("👉 **Module: Overview**")

with row1_col2:
    st.warning("**2. Model Explainability**")
    st.markdown("### ⚡ Inference Engine")
    st.caption("Real-time decision analysis. Visualize voting logic from Random Forest, Isolation Forest, and GNN models per transaction.")
    st.markdown("👉 **Module: Model Explainability**")

# ROW 2: Administration & Profiles
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.error("**3. Pipeline Administration**")
    st.markdown("### ⚙️ ETL & Data Ops")
    st.caption("Manage the data pipeline, execute batch processing, refresh database views, and monitor system health.")
    st.markdown("👉 **Module: Pipeline Admin**")

with row2_col2:
    st.success("**4. Customer 360**")
    st.markdown("### 👤 Entity Profiling")
    st.caption("Deep-dive forensic audit on specific customers. View transaction history, behavioral graphs, and risk scores.")
    st.markdown("👉 **Module: Customer 360**")

# ROW 3: Simulation (Separate)
st.markdown("---")
st.markdown("### 📱 External Interface")
with st.container():
    st.info("**5. App Simulator**")
    st.caption("Transaction Injection Utility. Simulates client-side activity to test fraud detection response mechanisms.")
    st.markdown("👉 **Module: App Simulator**")

st.markdown("---")

# --- TECH STACK ---
st.subheader("🛠️ Technology Stack")
t1, t2, t3, t4 = st.columns(4)
t1.metric("Frontend", "Streamlit UI")
t2.metric("Backend", "FastAPI + Python")
t3.metric("Database", "PostgreSQL")
t4.metric("AI Models", "RF + IsoForest + GNN")

st.markdown("---")