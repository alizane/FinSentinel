import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import graphviz # Needed for the new flowchart

# --- CONFIG ---
st.set_page_config(page_title="Model Inference Engine", page_icon="⚙️", layout="wide")

st.title("⚙️ System Architecture & Inference Logic")
st.markdown("### Hybrid Ensemble Decision Matrix")

# --- TAB SELECTION ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🏗️ System Architecture", 
    "📊 Isolation Forest (Anomaly)", 
    "🕸️ Graph Neural Network (GNN)", 
    "🌲 Random Forest (Supervised)"
])

# ==========================================
# TAB 1: THE ARCHITECTURE FLOWCHART (GRAPHVIZ)
# ==========================================
with tab1:
    st.subheader("Transaction Processing Pipeline")
    st.caption("Data Flow: Ingestion → Enrichment → Multi-Model Inference → Final Decision")
    
    col_flow, col_expl = st.columns([3, 1])
    
    with col_flow:
        # Use Graphviz for perfect rectangles, arrows, and text rendering
        dot = graphviz.Digraph(comment='System Architecture')
        
        # Graph Attributes for Left-to-Right flow and clean lines
        dot.attr(rankdir='LR', splines='polyline', nodesep='0.6', ranksep='0.8', bgcolor='transparent')

        # Default Node Styles (Rounded Rectangles)
        dot.attr('node', shape='box', style='filled, rounded', fontname="sans-serif", fontsize='12', penwidth='1.5', fixedsize='false', margin='0.2')
        # Default Edge Styles
        dot.attr('edge', fontname="sans-serif", fontsize='10', penwidth='1.5', arrowsize='1.2')

        # --- Define Nodes with Technical Colors ---
        # Source/Ingestion (Grey/Light Blue)
        dot.node('USER', 'User / Client\n(Source)', fillcolor='#CFD8DC', color='#455A64')
        dot.node('API', 'API Gateway\n(Ingestion)', fillcolor='#B3E5FC', color='#0288D1')
        dot.node('DB', 'Feature Store\n(Enrichment)', fillcolor='#CFD8DC', color='#455A64')

        # Models (Yellow - Aligned in a vertical group automatically by rankdir=LR)
        dot.attr('node', fillcolor='#FFF59D', color='#FBC02D')
        dot.node('M1', 'M1: Random Forest\n(Supervised)')
        dot.node('M2', 'M2: Iso Forest\n(Anomaly)')
        dot.node('M3', 'M3: Graph Neural\n(Topology)')
        dot.node('M4', 'M4: Rule Engine\n(Scenarios)')

        # Output (Orange)
        dot.node('OUTPUT', 'AGGREGATED\nOUTPUT', fillcolor='#FFCCBC', color='#E64A19')

        # --- Define Edges (Arrows implied by Digraph) ---
        # Main Spine
        dot.edge('USER', 'API')
        dot.edge('API', 'DB')

        # Fan-out to models
        dot.edge('DB', 'M1')
        dot.edge('DB', 'M2')
        dot.edge('DB', 'M3')
        dot.edge('DB', 'M4')

        # Fan-in to output
        dot.edge('M1', 'OUTPUT')
        dot.edge('M2', 'OUTPUT')
        dot.edge('M3', 'OUTPUT')
        dot.edge('M4', 'OUTPUT')

        # Render the chart
        st.graphviz_chart(dot, use_container_width=True)

    with col_expl:
        st.info("ℹ️ **Pipeline Specification**")
        st.markdown("""
        **1. Transaction Ingestion Stream:**
        Unified entry point for all client requests via API Gateway.
        
        **2. Feature Enrichment:**
        Real-time lookup of historical profiles (Velocity, Beneficiary Stats) from the Feature Store.
        
        **3. Ensemble Inference:**
        Parallel evaluation by 4 specialized engines:
        * **M1:** Supervised Learning (Patterns)
        * **M2:** Unsupervised Learning (Outliers)
        * **M3:** Graph Topology (Relationships)
        * **M4:** Deterministic Rules (Scenarios)
        
        **4. Aggregation Logic:**
        Priority-based voting mechanism. A high-risk flag from any single model triggers a block.
        """)


# ==========================================
# TAB 2: ISOLATION FOREST (DECISION BOUNDARY)
# ==========================================
with tab2:
    st.subheader("Outlier Detection: Statistical Deviation")
    st.markdown("Visualizing the **Decision Boundary** in high-dimensional feature space (projected to 2D).")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        np.random.seed(42)
        # Normal Cluster
        norm_x = np.random.normal(60, 10, 200)
        norm_y = norm_x * 0.65 + np.random.normal(0, 5, 200)
        
        # Anomalies (Shell Company Signature)
        shell_x = np.random.normal(70, 5, 15)
        shell_y = np.random.normal(2, 1, 15) 

        fig = go.Figure()
        # Safe Region
        fig.add_shape(type="rect", x0=30, y0=20, x1=90, y1=80, fillcolor="rgba(0, 255, 0, 0.1)", line=dict(width=0), layer="below")
        # Anomaly Region
        fig.add_shape(type="rect", x0=50, y0=-5, x1=90, y1=15, fillcolor="rgba(255, 0, 0, 0.2)", line=dict(width=0), layer="below")
        
        fig.add_trace(go.Scatter(x=norm_x, y=norm_y, mode='markers', name='In-Distribution (Normal)', marker=dict(color='blue', size=8, opacity=0.6)))
        fig.add_trace(go.Scatter(x=shell_x, y=shell_y, mode='markers', name='Out-of-Distribution (Anomaly)', marker=dict(color='red', size=12, symbol='x')))
        
        fig.update_layout(
            title="Isolation Forest: Feature Space Projection", 
            xaxis_title="Transaction Volume (Normalized)", 
            yaxis_title="Operational Expenses (Normalized)", 
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.write("### 📉 Analysis")
        st.warning("""
        **Anomaly Signature:**
        High Transaction Volume paired with near-zero Operational Expenses (OpEx) violates the standard regression line of legitimate businesses.
        
        **Metric:**
        These points have a negative Anomaly Score (e.g., -0.75), triggering an immediate flag.
        """)

# ==========================================
# TAB 3: GRAPH NEURAL NETWORK (TOPOLOGY)
# ==========================================
with tab3:
    st.subheader("Network Topology Analysis")
    st.markdown("The **GNN** analyzes node relationships to identify structural fraud patterns.")

    # --- SELECTOR ---
    crime_type = st.radio(
        "Select Network Topology:",
        ["1. Star Topology (Fan-In/Mule)", "2. Circular Topology (Layering Loop)", "3. Shared Resource (Synthetic Identity)"],
        horizontal=True
    )

    col_net, col_desc = st.columns([3, 1])

    with col_net:
        # Keep using Matplotlib/NetworkX here as it handles circular layouts better for GNN visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # --- SCENARIO 1: STAR TOPOLOGY ---
        if "Star" in crime_type:
            G = nx.DiGraph()
            G.add_node("HUB", label="TARGET\n(Aggregator)", color='#FF5252', pos=(0, 0))
            
            senders = ["Acct 1", "Acct 2", "Acct 3", "Acct 4", "Acct 5"]
            radius = 1.5
            import math
            for i, v in enumerate(senders):
                angle = (2 * math.pi * i) / len(senders)
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                G.add_node(v, label=v, color='#81D4FA', pos=(x, y))
                G.add_edge(v, "HUB")

            desc_title = "Star Topology"
            desc_text = """
            **Structure:**
            Multiple unrelated nodes directing funds to a single central node within a short time window.
            
            **Indicator:**
            High In-Degree Centrality with low Out-Degree on the source nodes.
            """

        # --- SCENARIO 2: CIRCULAR TOPOLOGY ---
        elif "Circular" in crime_type:
            G = nx.DiGraph()
            G.add_node("A", label="Entity A", color='#FFD54F', pos=(0, 1))       
            G.add_node("B", label="Entity B", color='#FFD54F', pos=(-0.86, -0.5)) 
            G.add_node("C", label="Entity C", color='#FFD54F', pos=(0.86, -0.5))
            G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
            
            desc_title = "Closed Loop"
            desc_text = """
            **Structure:**
            Funds circulate through a closed chain (A→B→C→A) to artificially inflate volume or obfuscate origin.
            
            **Indicator:**
            Cycle detection algorithm returns True; Net displacement of funds is zero.
            """

        # --- SCENARIO 3: SYNTHETIC IDENTITY ---
        elif "Synthetic" in crime_type:
            G = nx.Graph()
            G.add_node("DEV", label="DEVICE_ID\n(Shared)", color='#212121', pos=(0, 0))
            
            users = ["User A", "User B", "User C", "User D", "User E"]
            radius = 1.5
            import math
            for i, u in enumerate(users):
                angle = (2 * math.pi * i) / len(users)
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                G.add_node(u, label=u, color='#E040FB', pos=(x, y))
                G.add_edge(u, "DEV")

            desc_title = "Bipartite Projection"
            desc_text = """
            **Structure:**
            Multiple distinct identities associated with a single physical attribute (Device ID or IP).
            
            **Indicator:**
            High degree centrality on a non-transactional node (Device/IP).
            """

        # --- DRAWING ---
        pos = nx.get_node_attributes(G, 'pos')
        colors = nx.get_node_attributes(G, 'color').values()
        labels = nx.get_node_attributes(G, 'label')
        
        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=6000, node_color=colors, edgecolors='black', linewidths=2)
        
        is_directed = G.is_directed()
        nx.draw_networkx_edges(G, pos, ax=ax, 
            edge_color='#455A64', width=3, arrowstyle='-|>' if is_directed else '-', arrowsize=30, 
            node_size=6000, connectionstyle="arc3,rad=0.05")
        
        nx.draw_networkx_labels(G, pos, ax=ax, labels=labels, font_size=9, font_weight="bold", font_family="sans-serif", 
                                font_color="white" if "Synthetic" in crime_type else "black")
        
        ax.margins(0.20)
        ax.axis('off')
        st.pyplot(fig)

    with col_desc:
        st.error(f"### {desc_title}")
        st.info(desc_text)

# ==========================================
# TAB 4: RANDOM FOREST (FEATURE IMPORTANCE)
# ==========================================
with tab4:
    st.subheader("Feature Importance Ranking")
    st.markdown("Analysis of the Random Forest Decision Tree weighting.")
    
    features = pd.DataFrame({
        'Feature Name': ['Velocity_Deviation (Amount > Avg)', 'Geospatial_Mismatch', 'Device_New_Flag', 'Time_Since_Last_Txn', 'Beneficiary_Risk_Score'],
        'Importance Score': [0.45, 0.30, 0.15, 0.08, 0.02]
    })
    
    fig_feat = px.bar(
        features, x='Importance Score', y='Feature Name', orientation='h', color='Importance Score',
        color_continuous_scale='Viridis', title="Model Weighting Distribution"
    )
    st.plotly_chart(fig_feat, use_container_width=True)
    
    st.info("""
    **Technical Interpretation:**
    The model assigns the highest weight (0.45) to **Velocity Deviation**, indicating that statistical spikes in transfer amounts are the primary predictor of fraud in the current dataset.
    """)