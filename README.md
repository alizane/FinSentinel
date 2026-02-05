<div align="center">

  <img src="sbi_logo.png" alt="FinSentinel Logo" width="120" height="120">
  
  # 🛡️ FinSentinel
  ### **The Next-Gen AI Forensics Engine for Financial Fraud Detection**

  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
  ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
  ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
  ![GNN](https://img.shields.io/badge/GNN-Graph%20AI-purple?style=for-the-badge)

  <p>
    <b>Criminals organize in networks. Why do we still catch them with lists?</b><br>
    FinSentinel combines <b>Supervised Learning</b>, <b>Unsupervised Anomaly Detection</b>, and <b>Graph Neural Networks</b> to expose hidden financial crime rings.
  </p>

</div>

---

## ⚡ Visual Demo: The "Wow" Factor

### 1. 🕸️ Real-Time Graph Forensics (GNN)
*Watch FinSentinel expose invisible connections instantly.*

| **🔴 Money Mule (Star Topology)** | **🟡 Layering (Circular Loop)** |
|:----------------:|:----------------:|
| *Detects high fan-in velocity (Recruitment Rings)* | *Detects hidden kickback loops (A → B → C → A)* |
| <img src="https://via.placeholder.com/400x200?text=Upload+Star+Demo+GIF" width="100%"> | <img src="https://via.placeholder.com/400x200?text=Upload+Cycle+Demo+GIF" width="100%"> |

### 2. 📊 Investigator Dashboard (Customer 360)
*A unified command center for tracking live fraud patterns.*

<img src="https://via.placeholder.com/800x400?text=Upload+Dashboard+Screenshot" width="100%">

---

## 🚀 The Defense Architecture

We don't rely on just one model. We use a **3-Layer Defense System**:

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