import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="Inside the AI", page_icon="🧠", layout="wide")

st.title("🧠 Inside the System: Visual Intelligence")
st.markdown("### How the 3-Model System Decides Fate")

# --- TAB SELECTION ---
tab1, tab2, tab3, tab4 = st.tabs([
    "⚙️ System Architecture", 
    "🧐 Isolation Forest (Unsupervised)", 
    "🤠 Graph Neural Network (GNN)", 
    "📜 Random Forest (Supervised)"
])

# ==========================================
# TAB 1: THE ARCHITECTURE FLOWCHART
# ==========================================
with tab1:
    st.subheader("The Decision Pipeline")
    st.caption("Live Data Journey: Dual-Stream Processing")
    
    col_flow, col_expl = st.columns([3, 1])
    
    with col_flow:
        G = nx.DiGraph()
        
        # NODES
        G.add_node("USER_A", label="User A\n(Legit)", pos=(0, 2), color='#AED581')
        G.add_node("USER_B", label="User B\n(Attacker)", pos=(0, -2), color='#E57373')
        G.add_node("API", label="API Gateway\n(Traffic Control)", pos=(2, 0), color='#4FC3F7')
        G.add_node("DB", label="Enrichment\n(DB Lookup)", pos=(4, 0), color='#B0BEC5')
        G.add_node("J1", label="M1: Random Forest\n(Supervised)", pos=(6, 2), color='#FFD54F')
        G.add_node("J2", label="M2: Isolation Forest\n(Unsupervised)", pos=(6, 0), color='#FFD54F')
        G.add_node("J3", label="M3: Graph Neural Net\n(GNN)", pos=(6, -2), color='#FFD54F')
        G.add_node("VERDICT", label="FINAL\nVERDICT", pos=(8, 0), color='#FF5722')

        # EDGES
        edges = [
            ("USER_A", "API"), ("USER_B", "API"), ("API", "DB"),
            ("DB", "J1"), ("DB", "J2"), ("DB", "J3"),
            ("J1", "VERDICT"), ("J2", "VERDICT"), ("J3", "VERDICT"),
        ]
        G.add_edges_from(edges)
        
        # DRAWING
        pos = nx.get_node_attributes(G, 'pos')
        colors = nx.get_node_attributes(G, 'color').values()
        labels = nx.get_node_attributes(G, 'label')
        
        fig, ax = plt.subplots(figsize=(12, 7))
        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=10000, node_color=colors, edgecolors='black', linewidths=2)
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color='#455A64', width=3.0, arrowstyle='-|>', arrowsize=30, node_size=9000, connectionstyle='arc3,rad=0.0')
        nx.draw_networkx_labels(G, pos, ax=ax, labels=labels, font_size=9, font_weight="bold", font_family="sans-serif")
        ax.margins(0.2)
        ax.axis('off')
        st.pyplot(fig)

    with col_expl:
        st.info("💡 **Pipeline Logic**")
        st.markdown("""
        **1. Dual Ingestion:** System accepts concurrent streams (Safe vs Attack).
        **2. The System:** Data is enriched and broadcast to 3 Technical Models.
        **3. Consensus:** Logical **OR** gate. Any 'Block' vote kills the transaction.
        """)


# ==========================================
# TAB 2: ISOLATION FOREST (VISUAL ZONES)
# ==========================================
with tab2:
    st.subheader("Visualizing 'The Zombie' (Shell Company)")
    st.markdown("The **Isolation Forest** partitions the mathematical space. We visualize this as 'Safe Zones' vs 'Kill Zones'.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        np.random.seed(42)
        norm_x = np.random.normal(60, 10, 200)
        norm_y = norm_x * 0.65 + np.random.normal(0, 5, 200)
        shell_x = np.random.normal(70, 5, 15)
        shell_y = np.random.normal(2, 1, 15) 

        fig = go.Figure()
        fig.add_shape(type="rect", x0=30, y0=20, x1=90, y1=80, fillcolor="rgba(0, 255, 0, 0.1)", line=dict(width=0), layer="below")
        fig.add_shape(type="rect", x0=50, y0=-5, x1=90, y1=15, fillcolor="rgba(255, 0, 0, 0.2)", line=dict(width=0), layer="below")
        fig.add_trace(go.Scatter(x=norm_x, y=norm_y, mode='markers', name='Healthy Business', marker=dict(color='blue', size=8, opacity=0.6)))
        fig.add_trace(go.Scatter(x=shell_x, y=shell_y, mode='markers', name='🚨 SHELL COMPANY', marker=dict(color='red', size=12, symbol='x')))
        fig.update_layout(title="Isolation Forest Decision Boundary", xaxis_title="Revenue (₹ Lakhs)", yaxis_title="OpEx (₹ Lakhs)", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.write("### 🧠 Visual Logic")
        st.warning("""
        **The Kill Zone:**
        Real businesses (Blue) spend money to make money. 
        Shell companies (Red X) break this correlation. High revenue + Zero expense = **Anomaly**.
        """)

# ==========================================
# TAB 3: GRAPH NEURAL NETWORK (ALL 3 TOPOLOGIES)
# ==========================================
with tab3:
    st.subheader("Visualizing The Network Crimes")
    st.markdown("The **Graph Neural Network (GNN)** uses **Graph Theory** to detect shapes that signify specific crimes.")

    # --- SELECTOR ---
    crime_type = st.radio(
        "Select Crime Topology to Analyze:",
        ["1. Star Topology (Money Mule)", "2. Circular Topology (Layering)", "3. Synthetic Identity (Device Farm)"],
        horizontal=True
    )

    col_net, col_desc = st.columns([3, 1])

    with col_net:
        # Create Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # --- SCENARIO 1: STAR TOPOLOGY (MULE) ---
        if "Star" in crime_type:
            G = nx.DiGraph()
            
            # 1. Central Node (The Mule) - Position (0,0)
            G.add_node("MULE", label="⚠️ MULE\n(Sinkhole)", color='#FF5252', pos=(0, 0))
            
            # 2. Victims (Outer Circle) - Calculated positions
            victims = ["Victim 1", "Victim 2", "Victim 3", "Victim 4", "Victim 5"]
            radius = 1.5
            import math
            
            for i, v in enumerate(victims):
                # Calculate angle for perfect circle distribution
                angle = (2 * math.pi * i) / len(victims)
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                
                G.add_node(v, label=v, color='#81D4FA', pos=(x, y))
                G.add_edge(v, "MULE") # Arrow points TOWARDS Mule

            desc_title = "The Money Mule"
            desc_text = """
            **The Fan-In Attack:**
            Money flows from multiple outer nodes into one central node.
            
            **Detection:**
            High **In-Degree Centrality**. The Red node is receiving funds from too many unrelated sources.
            """

        # --- SCENARIO 2: CIRCULAR TOPOLOGY (LAYERING) ---
        elif "Circular" in crime_type:
            G = nx.DiGraph()
            
            # Perfect Triangle Coordinates
            # Top, Bottom-Left, Bottom-Right
            G.add_node("A", label="Account A\n(Placement)", color='#FFD54F', pos=(0, 1))       
            G.add_node("B", label="Account B\n(Layering)", color='#FFD54F', pos=(-0.86, -0.5)) 
            G.add_node("C", label="Account C\n(Integration)", color='#FFD54F', pos=(0.86, -0.5))
            
            # Edges forming the loop
            G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
            
            desc_title = "The Wash Cycle"
            desc_text = """
            **The Loop Attack:**
            Money circulates A → B → C → A to generate fake volume or hide the source.
            
            **Detection:**
            **Cycle Detection (DFS)** finds closed loops in the transaction graph.
            """

        # --- SCENARIO 3: SYNTHETIC IDENTITY (GHOST) ---
        elif "Synthetic" in crime_type:
            G = nx.Graph() # Undirected (Shared Resource)
            
            # Central Device (Black Box)
            G.add_node("DEVICE", label="📱 DEVICE_ID\n(iPhone 15)", color='#212121', pos=(0, 0))
            
            # Fake Users (Outer Circle)
            users = ["Rahul", "Amit", "Sneha", "Pooja", "Raj"]
            radius = 1.5
            import math
            
            for i, u in enumerate(users):
                angle = (2 * math.pi * i) / len(users)
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                G.add_node(u, label=u, color='#E040FB', pos=(x, y)) # Purple
                G.add_edge(u, "DEVICE")

            desc_title = "The Fraud Farm"
            desc_text = """
            **Device Collision:**
            Multiple 'Unrelated' identities are accessing bank services from the **exact same hardware**.
            
            **Detection:**
            **Bipartite Projection** reveals the shared device link.
            """

        # --- COMMON DRAWING LOGIC (Fixed Visibility) ---
        pos = nx.get_node_attributes(G, 'pos')
        colors = nx.get_node_attributes(G, 'color').values()
        labels = nx.get_node_attributes(G, 'label')
        
        # 1. Draw Nodes
        nx.draw_networkx_nodes(G, pos, ax=ax, 
            node_size=6000, 
            node_color=colors, 
            edgecolors='black', 
            linewidths=2
        )
        
        # 2. Draw Edges (Thick & Visible)
        # We determine arrow style based on graph type
        is_directed = G.is_directed()
        nx.draw_networkx_edges(G, pos, ax=ax, 
            edge_color='#455A64', 
            width=3, 
            arrowstyle='-|>' if is_directed else '-', 
            arrowsize=30, 
            node_size=6000, # Stops arrow at circle edge
            connectionstyle="arc3,rad=0.05" # Slight curve for style
        )
        
        # 3. Draw Labels (Centered)
        nx.draw_networkx_labels(G, pos, ax=ax, 
            labels=labels, 
            font_size=9, 
            font_weight="bold", 
            font_family="sans-serif",
            font_color="white" if "Synthetic" in crime_type else "black" # White text for black device node
        )
        
        # Cleanup
        ax.margins(0.20) # Zoom out slightly so nothing is cut off
        ax.axis('off')
        st.pyplot(fig)

    with col_desc:
        st.error(f"### 🕸️ {desc_title}")
        st.info(desc_text)

# ==========================================
# TAB 4: RANDOM FOREST (PATTERNS)
# ==========================================
with tab4:
    st.subheader("Visualizing 'The Pattern' (Random Forest)")
    st.markdown("The **Random Forest** learns from the past. Which features matter most?")
    
    features = pd.DataFrame({
        'Feature': ['Amount_vs_Avg', 'Location_Mismatch', 'Device_New?', 'Hour_of_Day', 'Beneficiary_Age'],
        'Importance': [0.45, 0.30, 0.15, 0.08, 0.02]
    })
    
    fig_feat = px.bar(
        features, x='Importance', y='Feature', orientation='h', color='Importance',
        color_continuous_scale='Viridis', title="Decision Tree Feature Weighting"
    )
    st.plotly_chart(fig_feat, use_container_width=True)
    
    st.info("""
    **Interpretation:**
    **'Amount_vs_Avg'** is the strongest signal. A sudden 500% spike in transfer amount triggers the block.
    """)