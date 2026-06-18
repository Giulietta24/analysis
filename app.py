import streamlit as st
import yfinance as yf
import pandas as pd

SMALL_CAP_THRESHOLD = 3_000_000_000
MID_CAP_THRESHOLD = 15_000_000_000

st.set_page_config(layout="wide", page_title="Universal Multi-Cap Dashboard")
st.title("📊 Multi-Cap Dynamic Stock Comparison Engine")
st.caption("Input any asset ticker to view real-time fundamentals matched accurately against live market benchmarks.")

st.sidebar.header("User Dashboard Control Panels")
target_ticker = st.sidebar.text_input("🟢 Target Stock Ticker", "NVDA").strip().upper()
rival_ticker = st.sidebar.text_input("🔵 Direct Rival Ticker", "AMD").strip().upper()
custom_index = st.sidebar.text_input("🛠️ Custom ETF/Index Ticker", "QQQ").strip().upper()

def format_mcap_clean(value) -> str:
    if not isinstance(value, (int, float)) or value <= 0:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,.0f}"

def parse_pct(val):
    if isinstance(val, (int, float)):
        return val
    return None

def parse_x(val):
    if isinstance(val, (int, float)):
        return val
    return None

@st.cache_resource(ttl=300)
def calculate_dynamic_index_growth(ticker_str: str) -> str:
    try:
        tk = yf.Ticker(ticker_str)
        hist = tk.history(period="1y")
        if len(hist) < 20:
            return "N/A"
        initial_val = hist["Close"].iloc[0]
        current_val = hist["Close"].iloc[-1]
        growth_rate = ((current_val - initial_val) / initial_val) * 100
        return f"{growth_rate:.1f}%"
    except Exception:
        return "N/A"

@st.cache_resource(ttl=300)
def fetch_ticker_metrics(ticker_str: str, is_index: bool = False) -> tuple[dict, bool]:
    fallback = {
        "Name": ticker_str,
        "Price": "N/A",
        "Cap_Raw": 0,
        "Market Cap": "N/A",
        "P/E": "N/A",
        "Forward P/E": "N/A",
        "PEG Ratio": "N/A",
        "ROIC": "N/A",
        "FCF Yield": "N/A",
        "Growth": "N/A",
    }

    if not ticker_str:
        return fallback, False

    try:
        ticker = yf.Ticker(ticker_str)
        info = ticker.info
        if not info or len(info) <= 1:
            return fallback, False

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        mcap = info.get("marketCap") or info.get("totalAssets", 0)

        pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        peg_ratio = info.get("pegRatio")
        roic = info.get("returnOnInvestedCapital")
        fcf_yield = info.get("freeCashflowYield")

        if is_index:
            growth_fmt = calculate_dynamic_index_growth(ticker_str)
            pe_fmt = "N/A"
            forward_pe_fmt = "N/A"
            peg_fmt = "N/A"
            roic_fmt = "N/A"
            fcf_fmt = "N/A"
        else:
            rev_growth = info.get("revenueGrowth")
            growth_fmt = f"{rev_growth * 100:.1f}%" if isinstance(rev_growth, (int, float)) else "N/A"
            pe_fmt = f"{pe:.1f}x" if isinstance(pe, (int, float)) else "N/A"
            forward_pe_fmt = f"{forward_pe:.1f}x" if isinstance(forward_pe, (int, float)) else "N/A"
            peg_fmt = f"{peg_ratio:.2f}" if isinstance(peg_ratio, (int, float)) else "N/A"
            roic_fmt = f"{roic * 100:.1f}%" if isinstance(roic, (int, float)) else "N/A"
            fcf_fmt = f"{fcf_yield * 100:.1f}%" if isinstance(fcf_yield, (int, float)) else "N/A"

        name = info.get("shortName") or ticker_str
        price_fmt = f"${price:,.2f}" if isinstance(price, (int, float)) else "N/A"

        return {
            "Name": name,
            "Price": price_fmt,
            "Cap_Raw": mcap,
            "Market Cap": format_mcap_clean(mcap),
            "P/E": pe_fmt,
            "Forward P/E": forward_pe_fmt,
            "PEG Ratio": peg_fmt,
            "ROIC": roic_fmt,
            "FCF Yield": fcf_fmt,
            "Growth": growth_fmt,
        }, True

    except Exception:
        return fallback, False

def build_table(metrics_map):
    rows = [
        "Asset Name",
        "Share Price",
        "Market Size / AUM",
        "P/E Ratio (Current)",
        "Forward P/E (Future)",
        "PEG Ratio (Future)",
        "ROIC (Quality)",
        "FCF Yield (Quality)",
        "TTM Performance / Growth",
    ]

    return pd.DataFrame(
        {
            "Metric": rows,
            f"🟢 Target ({target_ticker})": [
                metrics_map["t1"]["Name"],
                metrics_map["t1"]["Price"],
                metrics_map["t1"]["Market Cap"],
                metrics_map["t1"]["P/E"],
                metrics_map["t1"]["Forward P/E"],
                metrics_map["t1"]["PEG Ratio"],
                metrics_map["t1"]["ROIC"],
                metrics_map["t1"]["FCF Yield"],
                metrics_map["t1"]["Growth"],
            ],
            f"🔵 Rival ({rival_ticker})": [
                metrics_map["t2"]["Name"],
                metrics_map["t2"]["Price"],
                metrics_map["t2"]["Market Cap"],
                metrics_map["t2"]["P/E"],
                metrics_map["t2"]["Forward P/E"],
                metrics_map["t2"]["PEG Ratio"],
                metrics_map["t2"]["ROIC"],
                metrics_map["t2"]["FCF Yield"],
                metrics_map["t2"]["Growth"],
            ],
            f"🛠️ Custom ({custom_index})": [
                metrics_map["t3"]["Name"],
                metrics_map["t3"]["Price"],
                metrics_map["t3"]["Market Cap"],
                metrics_map["t3"]["P/E"],
                metrics_map["t3"]["Forward P/E"],
                metrics_map["t3"]["PEG Ratio"],
                metrics_map["t3"]["ROIC"],
                metrics_map["t3"]["FCF Yield"],
                metrics_map["t3"]["Growth"],
            ],
            f"Cap-Weight ({metrics_map['cap_ticker']})": [
                metrics_map["b_cap"]["Name"],
                "N/A",
                metrics_map["b_cap"]["Market Cap"],
                metrics_map["b_cap"]["P/E"],
                metrics_map["b_cap"]["Forward P/E"],
                metrics_map["b_cap"]["PEG Ratio"],
                metrics_map["b_cap"]["ROIC"],
                metrics_map["b_cap"]["FCF Yield"],
                metrics_map["b_cap"]["Growth"],
            ],
            f"Equal-Weight ({metrics_map['eq_ticker']})": [
                metrics_map["b_eq"]["Name"],
                "N/A",
                metrics_map["b_eq"]["Market Cap"],
                metrics_map["b_eq"]["P/E"],
                metrics_map["b_eq"]["Forward P/E"],
                metrics_map["b_eq"]["PEG Ratio"],
                metrics_map["b_eq"]["ROIC"],
                metrics_map["b_eq"]["FCF Yield"],
                metrics_map["b_eq"]["Growth"],
            ],
        }
    ).set_index("Metric")

if st.sidebar.button("Run Financial Evaluation Matrix"):
    if not target_ticker or not rival_ticker or not custom_index:
        st.error("❌ Missing Inputs: Make sure all parameters are typed out.")
        st.stop()

    with st.spinner("Fetching underlying real-time exchange data..."):
        t1, ok1 = fetch_ticker_metrics(target_ticker)
        t2, ok2 = fetch_ticker_metrics(rival_ticker)
        t3, ok3 = fetch_ticker_metrics(custom_index, is_index=True)

        target_cap = t1["Cap_Raw"]

        if target_cap <= 0:
            cap_ticker, eq_ticker = "SPY", "RSP"
        elif target_cap < SMALL_CAP_THRESHOLD:
            cap_ticker, eq_ticker = "IWM", "EWSC"
        elif target_cap < MID_CAP_THRESHOLD:
            cap_ticker, eq_ticker = "MDY", "EWRM"
        else:
            cap_ticker, eq_ticker = "SPY", "RSP"

        b_cap, ok_cap = fetch_ticker_metrics(cap_ticker, is_index=True)
        b_eq, ok_eq = fetch_ticker_metrics(eq_ticker, is_index=True)

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

        metrics_map = {
            "t1": t1, "t2": t2, "t3": t3,
            "b_cap": b_cap, "b_eq": b_eq,
            "cap_ticker": cap_ticker, "eq_ticker": eq_ticker
        }

        df = build_table(metrics_map)

        st.subheader("Current Metrics")
        st.dataframe(df.loc[["P/E Ratio (Current)", "ROIC (Quality)", "FCF Yield (Quality)"]], use_container_width=True)

        st.subheader("Future Metrics")
        st.dataframe(df.loc[["Forward P/E (Future)", "PEG Ratio (Future)", "TTM Performance / Growth"]], use_container_width=True)

        st.subheader("Full Comparison")
        st.dataframe(df, use_container_width=True)

        st.download_button(
            label="📥 Export Matrix Dataset to CSV",
            data=df.to_csv().encode("utf-8"),
            file_name="dashboard_export.csv",
            mime="text/csv",
        )

        st.caption("⚠️ Notice: All index metrics—including fund valuation multiples and historical trends—are derived programmatically in real time.")
