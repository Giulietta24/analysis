import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

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
    if not isinstance(value, (int, float)) or value <= 0:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${round(value / 1_000_000_000_000, 2)}T"
    elif value >= 1_000_000_000:
        return f"${round(value / 1_000_000_000, 1)}B"
    elif value >= 1_000_000:
        return f"${round(value / 1_000_000, 1)}M"
    return f"${value:,.0f}"

@st.cache_resource(ttl=300)
def calculate_dynamic_index_growth(ticker_str: str) -> str:
    """Calculates live TTM market momentum as a growth rate proxy for pure index funds."""
    try:
        tk = yf.Ticker(ticker_str)
        hist = tk.history(period="1y")
        if len(hist) < 20:
            return "N/A"
        initial_val = hist['Close'].iloc[0]
        current_val = hist['Close'].iloc[-1]
        growth_rate = ((current_val - initial_val) / initial_val) * 100
        return f"{round(growth_rate, 1)}%"
    except Exception:
        return "N/A"

@st.cache_resource(ttl=300)
def fetch_ticker_metrics(ticker_str: str, is_index: bool = False) -> tuple[dict, bool]:
    fallback_dict = {
        "Name": ticker_str,
        "Price": "N/A",
        "Cap_Raw": 0,
        "Market Cap": "N/A",
        "P/E": "N/A",
        "Growth": "N/A"
    }
    if not ticker_str:
        return fallback_dict, False

    try:
        ticker = yf.Ticker(ticker_str)
        info = ticker.info
        if not info or len(info) <= 1:
            raise ValueError("No data records found.")

        price = info.get("currentPrice")
        if price is None:
            price = info.get("regularMarketPrice", 0.0)
            
        mcap = info.get("marketCap") or info.get("totalAssets", 0)
        pe = info.get("trailingPE")
        
        # Calculate growth based on asset classification type
        if is_index:
            growth_fmt = calculate_dynamic_index_growth(ticker_str)
            # For indexes/ETFs, P/E may not be meaningful
            if pe is None:
                pe_fmt = "N/A"
            elif isinstance(pe, (int, float)):
                pe_fmt = f"{round(pe, 1)}x"
            else:
                pe_fmt = "N/A"
        else:
            rev_growth = info.get("revenueGrowth")
            growth_fmt = f"{round(rev_growth * 100, 1)}%" if isinstance(rev_growth, (int, float)) else "N/A"
            pe_fmt = f"{round(pe, 1)}x" if isinstance(pe, (int, float)) else "N/A"
        
        # Formatting metrics cleanly
        price_fmt = f"${price:,.2f}" if isinstance(price, (int, float)) else "N/A"
        mcap_fmt = format_mcap_clean(mcap)
        name = info.get("shortName") or ticker_str
        
        return {
            "Name": name,
            "Price": price_fmt,
            "Cap_Raw": mcap,
            "Market Cap": mcap_fmt,
            "P/E": pe_fmt,
            "Growth": growth_fmt
        }, True
    except Exception as e:
        return fallback_dict, False

if st.sidebar.button("Run Financial Evaluation Matrix"):
    if not target_ticker or not rival_ticker or not custom_index:
        st.error("❌ Missing Inputs: Make sure all parameters are typed out.")
        st.stop()
        
    with st.spinner("Fetching underlying real-time exchange data..."):
        # Fetch target and custom tickers dynamically
        t1, ok1 = fetch_ticker_metrics(target_ticker)
        t2, ok2 = fetch_ticker_metrics(rival_ticker)
        t3, ok3 = fetch_ticker_metrics(custom_index, is_index=True)
        
        target_cap = t1["Cap_Raw"]
        
        # Assign benchmark tokens dynamically based on Target sizing parameters
        if target_cap <= 0:
            cap_ticker, eq_ticker = "SPY", "RSP"
        elif target_cap < SMALL_CAP_THRESHOLD:
            cap_ticker, eq_ticker = "IWM", "EWSC"
        elif target_cap < MID_CAP_THRESHOLD:
            cap_ticker, eq_ticker = "MDY", "EWRM"
        else:
            cap_ticker, eq_ticker = "SPY", "RSP"

        # Pull real-time fund profile data natively via the API
        b_cap, ok_cap = fetch_ticker_metrics(cap_ticker, is_index=True)
        b_eq, ok_eq = fetch_ticker_metrics(eq_ticker, is_index=True)

        # Show warnings for any failed fetches
        if not ok1:
            st.sidebar.warning(f"⚠️ Tracking warning for '{target_ticker}': Missing dynamic data points.")
        if not ok2:
            st.sidebar.warning(f"⚠️ Tracking warning for '{rival_ticker}': Missing dynamic data points.")
        if not ok3:
            st.sidebar.warning(f"⚠️ Tracking warning for '{custom_index}': Missing dynamic data points.")
        if not ok_cap:
            st.sidebar.warning(f"⚠️ Tracking warning for '{cap_ticker}': Missing dynamic data points.")
        if not ok_eq:
            st.sidebar.warning(f"⚠️ Tracking warning for '{eq_ticker}': Missing dynamic data points.")

        matrix_data = {
            "Metric": [
                "Asset Name",
                "Share Price",
                "Market Size / AUM",
                "P/E Ratio",
                "TTM Performance / Growth"
            ],
            f"🟢 Target ({target_ticker})": [
                t1["Name"],
                t1["Price"],
                t1["Market Cap"],
                t1["P/E"],
                t1["Growth"]
            ],
            f"🔵 Rival ({rival_ticker})": [
                t2["Name"],
                t2["Price"],
                t2["Market Cap"],
                t2["P/E"],
                t2["Growth"]
            ],
            f"🛠️ Custom ({custom_index})": [
                t3["Name"],
                t3["Price"],
                t3["Market Cap"],
                t3["P/E"],
                t3["Growth"]
            ],
            f"Cap-Weight ({cap_ticker})": [
                b_cap["Name"],
                "N/A",
                b_cap["Market Cap"],
                b_cap["P/E"],
                b_cap["Growth"]
            ],
            f"Equal-Weight ({eq_ticker})": [
                b_eq["Name"],
                "N/A",
                b_eq["Market Cap"],
                b_eq["P/E"],
                b_eq["Growth"]
            ]
        }
        
        df = pd.DataFrame(matrix_data).set_index("Metric")
        st.dataframe(df, use_container_width=True)
        
        st.download_button(
            label="📥 Export Matrix Dataset to CSV",
            data=df.to_csv().encode('utf-8'),
            file_name="dashboard_export.csv",
            mime="text/csv"
        )
        st.caption("⚠️ **Notice:** All index metrics—including fund valuation multiples and historical trends—are derived programmatically in real time.")
