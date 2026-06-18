import streamlit as st
import yfinance as yf
import pandas as pd

# Constants for market capitalization thresholds (Ref: Issue 5)
SMALL_CAP_THRESHOLD = 3_000_000_000
MID_CAP_THRESHOLD = 15_000_000_000

st.set_page_config(layout="wide", page_title="Universal Multi-Cap Dashboard")
st.title("📊 Multi-Cap Dynamic Stock Comparison Engine")
st.caption("Input any asset ticker to view real-time fundamentals matched accurately against sector and sizing benchmarks.") # Ref: Style Note

# --- Sidebar Inputs & Validation ---
st.sidebar.header("User Dashboard Control Panels")
target_ticker = st.sidebar.text_input("🟢 Target Stock Ticker", "NVDA").strip().upper()
rival_ticker = st.sidebar.text_input("🔵 Direct Rival Ticker", "AMD").strip().upper()
custom_index = st.sidebar.text_input("🛠️ Custom ETF/Index Ticker", "QQQ").strip().upper()

# --- Performance Caching Mechanism (Ref: Issue 1) ---
@st.cache_data(ttl=300) # Cache API data for 5 minutes to prevent throttling
def fetch_ticker_metrics(ticker_str: str) -> dict:
    """Fetches real-time market data from Yahoo Finance cleanly with strict error fallbacks."""
    fallback_dict = {"Name": ticker_str, "Price": "N/A", "Cap_Raw": 0, "Market Cap": "N/A", "P/E": "N/A", "Growth": "N/A"}
    
    if not ticker_str:
        return fallback_dict

    try:
        ticker = yf.Ticker(ticker_str)
        info = ticker.info
        
        if not info or len(info) <= 1:
            raise ValueError("Empty or invalid profile dictionary returned from server.")

        # Robust explicit checking instead of dangerous short-circuiting or 'or' operations (Ref: Issue 3)
        price = info.get("currentPrice")
        if price is None:
            price = info.get("regularMarketPrice", 0.0)
            
        mcap = info.get("marketCap", 0)
        pe = info.get("trailingPE")
        rev_growth = info.get("revenueGrowth")
        
        # Formatting calculations safely
        price_fmt = f"${price:,.2f}" if isinstance(price, (int, float)) else "N/A"
        mcap_fmt = f"${mcap:,.0f}" if isinstance(mcap, (int, float)) and mcap > 0 else "N/A"
        pe_fmt = f"{round(pe, 1)}x" if isinstance(pe, (int, float)) else "N/A"
        growth_fmt = f"{round(rev_growth * 100, 1)}%" if isinstance(rev_growth, (int, float)) else "N/A"
        name = info.get("shortName") or info.get("longName") or ticker_str
        
        return {
            "Name": name, 
            "Price": price_fmt, 
            "Cap_Raw": mcap, 
            "Market Cap": mcap_fmt, 
            "P/E": pe_fmt, 
            "Growth": growth_fmt
        }
    except Exception as e:
        # Alert user explicitly about failed fetches rather than swallowing natively (Ref: Issue 2)
        st.sidebar.warning(f"⚠️ Could not pull data for ticker '{ticker_str}': Check spelling or API connectivity status.")
        return fallback_dict

# --- Main Evaluation Loop ---
if st.sidebar.button("Run Financial Evaluation Matrix"):
    # Input Guard (Ref: Issue 8)
    if not target_ticker or not rival_ticker or not custom_index:
        st.error("❌ Missing Inputs: Please make sure all ticker text boxes are filled before processing.")
        st.stop()
        
    with st.spinner("Fetching underlying real-time exchange data..."):
        # Fetch Target Assets
        t1 = fetch_ticker_metrics(target_ticker)
        t2 = fetch_ticker_metrics(rival_ticker)
        t3 = fetch_ticker_metrics(custom_index)
        
        # Dynamic Benchmark Framework Selection based on size (Ref: Issue 4)
        target_cap = t1["Cap_Raw"]
        if target_cap <= 0:
            st.error(f"Could not compute a valid market capitalization for '{target_ticker}'. Defaulting to Large-Cap indexes.")
            cap_ticker, eq_ticker = "SPY", "RSP"
        elif target_cap < SMALL_CAP_THRESHOLD:
            cap_ticker, eq_ticker = "IWM", "EWSC"  # Russell 2000 vs. Small Equal-Weight
        elif target_cap < MID_CAP_THRESHOLD:
            cap_ticker, eq_ticker = "MDY", "EWRM"  # MidCap 400 vs. Mid Equal-Weight
        else:
            cap_ticker, eq_ticker = "SPY", "RSP"   # S&P 500 vs Large Equal-Weight

        # Live Dynamic Fetch of Index Benchmarks (No more hardcoded stale strings!)
        b_cap = fetch_ticker_metrics(cap_ticker)
        b_eq = fetch_ticker_metrics(eq_ticker)

        # Assemble clean DataFrame with standardized shorter header syntax (Ref: Style Note)
        matrix_data = {
            "Metric": ["Asset Name", "Share Price", "Market Cap / AUM", "P/E Ratio", "Y/Y Revenue Growth"],
            f"🟢 Target ({target_ticker})": [t1["Name"], t1["Price"], t1["Market Cap"], t1["P/E"], t1["Growth"]],
            f"🔵 Rival ({rival_ticker})": [t2["Name"], t2["Price"], t2["Market Cap"], t2["P/E"], t2["Growth"]],
            f"🛠️ Custom ({custom_index})": [t3["Name"], t3["Price"], t3["Market Cap"], t3["P/E"], t3["Growth"]],
            f"Cap-Weight ({cap_ticker})": [b_cap["Name"], "N/A", "Index Baseline", b_cap["P/E"], b_cap["Growth"]],
            f"Equal-Weight ({eq_ticker})": [b_eq["Name"], "N/A", "Index Baseline", b_eq["P/E"], b_eq["Growth"]]
        }
        
        df = pd.DataFrame(matrix_data).set_index("Metric")
        
        # Display Dataframe
        st.dataframe(df, use_container_width=True)
        
        # Export Option UI Feature (Ref: Issue 6)
        csv_data = df.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Export Matrix Dataset to CSV",
            data=csv_data,
            file_name=f"multi_cap_comparison_{target_ticker}.csv",
            mime="text/csv"
        )
        
        # Educational warnings & structured context (Ref: Issue 7 / Style Note)
        st.info(
            "💡 **Methodology Warning:** Funds, indexes, and ETFs (like QQQ or RSP) handle 'Market Cap' as total Assets Under Management (AUM) "
            "and calculating P/E distributions across hundreds of holdings often differs structurally from basic single-equity math shares."
        )
        st.caption("⚠️ **Disclaimer:** For informational and educational purposes only. This sandbox does not constitute professional investment advice.")
