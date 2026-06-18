import streamlit as st
import yfinance as yf
import pandas as pd

SMALL_CAP_THRESHOLD = 3_000_000_000
MID_CAP_THRESHOLD = 15_000_000_000

st.set_page_config(layout="wide", page_title="Universal Multi-Cap Dashboard")
st.title("📊 Multi-Cap Dynamic Stock Comparison Engine")
st.caption("Input any asset ticker to view real-time fundamentals matched accurately against live market benchmarks.")

# --- Sidebar Inputs & Validation ---
st.sidebar.header("User Dashboard Control Panels")
target_ticker = st.sidebar.text_input("🟢 Target Stock Ticker", "NVDA").strip().upper()
rival_ticker = st.sidebar.text_input("🔵 Direct Rival Ticker", "AMD").strip().upper()
custom_index = st.sidebar.text_input("🛠️ Custom ETF/Index Ticker", "QQQ").strip().upper()

def format_mcap_clean(value) -> str:
    """Helper tool to round huge raw integers into scannable clean strings (e.g. $5.08T)."""
    if not 
