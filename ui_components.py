import streamlit as st

def load_paytm_style():
    """
    TRANSFORMS THE ENTIRE PAGE INTO A MOBILE PHONE SIMULATOR.
    """
    st.markdown("""
    <style>
        /* 1. BACKGROUND (The Desk) */
        .stApp {
            background-color: #e0e0e0;
            background-image: radial-gradient(#cfcfcf 1px, transparent 1px);
            background-size: 20px 20px;
        }

        /* 2. THE PHONE BODY (Main Container) */
        .main .block-container {
            max-width: 390px;
            padding: 0 !important;
            margin: auto;
            background-color: #F5F7FD; /* App Background */
            border: 12px solid #1f1f1f; /* Bezel */
            border-radius: 45px;
            box-shadow: 0 40px 100px rgba(0,0,0,0.5);
            min-height: 800px;
            margin-top: 20px;
            margin-bottom: 20px;
            overflow: hidden; /* Keeps everything inside */
        }

        /* 3. THE NOTCH */
        header {visibility: hidden;} /* Hide Streamlit Header */
        
        .notch-container {
            background: #F5F7FD;
            height: 40px;
            position: relative;
            margin-bottom: 10px;
        }
        .notch {
            width: 120px;
            height: 30px;
            background: #000;
            margin: 0 auto;
            border-bottom-left-radius: 16px;
            border-bottom-right-radius: 16px;
        }

        /* 4. APP HEADER */
        .paytm-header {
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #F5F7FD;
        }
        .profile-circle {
            width: 35px; height: 35px;
            background: #D4F1F4; color: #00BAF2;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-weight: bold; font-size: 14px;
        }

        /* 5. ICON GRID STYLING */
        /* This targets the Streamlit Buttons to look like App Icons */
        div[data-testid="stHorizontalBlock"] button {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            color: black !important;
        }
        div[data-testid="stHorizontalBlock"] button:hover {
            color: #00BAF2 !important;
            transform: scale(1.05);
        }
        
        /* The Blue Icon Circle */
        .blue-icon {
            width: 50px; height: 50px;
            background: #002E6E;
            border-radius: 18px;
            margin: 0 auto 5px auto;
            display: flex; align-items: center; justify-content: center;
            font-size: 24px; color: white;
        }
        .icon-text {
            font-size: 10px; font-weight: 600; text-align: center; line-height: 1.2; color: #333;
        }

        /* 6. BANNER & CARDS */
        .banner-img {
            width: 100%;
            border-radius: 12px;
            margin: 10px 0;
        }
        .section-title {
            font-size: 16px; font-weight: 800; color: #1d2b36; margin: 20px 0 15px 15px;
        }

    </style>
    """, unsafe_allow_html=True)

def render_notch():
    st.markdown("""
        <div class="notch-container">
            <div class="notch"></div>
        </div>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown("""
        <div class="paytm-header">
            <div class="profile-circle">MA</div>
            <div style="font-weight: 900; color: #002E6E; font-size: 18px;">
                FRCRCE <span style="color:#00BAF2;">Pay</span>
            </div>
            <div style="font-size: 20px;">🔔</div>
        </div>
    """, unsafe_allow_html=True)