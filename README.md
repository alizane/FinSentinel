<div align="center">

# 🛡️ FinSentinel
### **The Next-Gen AI Forensics Engine for Financial Fraud Detection**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![GNN](https://img.shields.io/badge/GNN-Graph%20AI-purple?style=for-the-badge)

<p>
  <b>Criminals organize in networks. Why do we still catch them with lists?</b><br>
  FinSentinel combines <b>Supervised Learning</b>, <b>Unsupervised Anomaly Detection</b>, and <b>Graph Neural Networks</b> to expose hidden financial crime rings.
</p>

</div>

---

## ⚡ System Architecture: The 3-Layer Defense

We don't rely on just one model. We use a multi-stage defense system that analyzes transactions in real-time.

```mermaid
graph LR
    A[Transaction Stream] --> B{Ensemble Engine}
    B --> C[🧠 Random Forest]
    B --> D[👻 Isolation Forest]
    B --> E[🕸️ Graph Network]
    C -- Pattern Match --> F[Risk Score]
    D -- Outlier Check --> F
    E -- Topology Scan --> F
    F --> G[🔴 BLOCK / 🟢 APPROVE]
    style F fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#bbf,stroke:#333,stroke-width:2px
🕸️ Forensic CapabilitiesFinSentinel goes beyond simple rules by visualizing the topology of crime.1. Money Mule Detection (Star Topology)Detects high fan-in/fan-out velocity where one account distributes to many (or receives from many) rapidly.Code snippetgraph TD
    M((🔴 MULE))
    V1(Victim 1) -->|$$$| M
    V2(Victim 2) -->|$$$| M
    V3(Victim 3) -->|$$$| M
    V4(Victim 4) -->|$$$| M
    M -->|Laundered| B(Boss Account)
    style M fill:#ff0000,stroke:#333,stroke-width:4px
2. Smurfing & Layering (Circular Loops)Detects hidden kickback loops (A → B → C → A) used to confuse audit trails.Code snippetgraph LR
    A((Account A)) -->|Transfer| B((Account B))
    B -->|Transfer| C((Account C))
    C -->|Return| A
    style A fill:#ff9900,stroke:#333
    style B fill:#ff9900,stroke:#333
    style C fill:#ff9900,stroke:#333
📊 Key FeaturesFeatureDescriptionTech StackReal-Time DashboardLive monitoring of transaction volumes, fraud rates, and flagged accounts.StreamlitGraph AnalysisVisualizes relationships between accounts to find hidden rings.NetworkX, PyVisHybrid AI EngineCombines Random Forest (Rules) + Isolation Forest (Anomalies).Scikit-LearnSQL IntegrationDirect fetch of transaction history and profile enrichment.PostgreSQLExportable ReportsGenerate PDF/CSV reports for forensic investigators.Pandas🛠️ Installation & SetupFollow these steps to deploy FinSentinel on your local machine.PrerequisitesPython 3.10+PostgreSQL (Ensure your server is running)1. Clone the RepositoryBashgit clone [https://github.com/alizane/FinSentinel.git](https://github.com/alizane/FinSentinel.git)
cd FinSentinel
2. Install DependenciesCreate a virtual environment (recommended) and install the required packages.Bash# Create virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
3. Database ConfigurationEnsure your PostgreSQL database is running. Update your .env or db_config.py file with your credentials:PythonDB_HOST = "localhost"
DB_NAME = "finsentinel"
DB_USER = "postgres"
DB_PASS = "your_password"
4. Run the ApplicationLaunch the Streamlit dashboard:Bashstreamlit run app.py
5. Access the DashboardOpen your browser and navigate to:http://localhost:8501📜 LicenseDistributed under the MIT License. See LICENSE for more information.<div align="center"><sub>Built with ❤️ by the FinSentinel Team</sub></div><div align="center">

# 🛡️ FinSentinel
### **The Next-Gen AI Forensics Engine for Financial Fraud Detection**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![GNN](https://img.shields.io/badge/GNN-Graph%20AI-purple?style=for-the-badge)

<p>
  <b>Criminals organize in networks. Why do we still catch them with lists?</b><br>
  FinSentinel combines <b>Supervised Learning</b>, <b>Unsupervised Anomaly Detection</b>, and <b>Graph Neural Networks</b> to expose hidden financial crime rings.
</p>

</div>

---

## ⚡ System Architecture: The 3-Layer Defense

We don't rely on just one model. We use a multi-stage defense system that analyzes transactions in real-time.

```mermaid
graph LR
    A[Transaction Stream] --> B{Ensemble Engine}
    B --> C[🧠 Random Forest]
    B --> D[👻 Isolation Forest]
    B --> E[🕸️ Graph Network]
    C -- Pattern Match --> F[Risk Score]
    D -- Outlier Check --> F
    E -- Topology Scan --> F
    F --> G[🔴 BLOCK / 🟢 APPROVE]
    style F fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#bbf,stroke:#333,stroke-width:2px

    