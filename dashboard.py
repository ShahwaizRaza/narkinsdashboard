import streamlit as st
import pandas as pd
import requests

# ─── Page Config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="Retail Sales Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CSS (injected once per session via session_state guard) ─────────────────
if "css_injected" not in st.session_state:
    st.markdown("""
    <style>
    div[data-testid="stDataFrame"] table { table-layout: fixed !important; width: 100% !important; }
    div[data-testid="stDataFrame"] th div { pointer-events: none !important; }
    div[data-testid="stDataFrame"] th {
        position: sticky !important; top: 0;
        background: #f1f1f1 !important; z-index: 3 !important;
    }
    [data-testid="stMetric"] {
        background-image: linear-gradient(to right, #0077C2, #59a5f5);
        padding: 1.5rem; border-radius: .75rem;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        font-size: 2.5rem; color: white; font-weight: 500;
    }
    [data-testid="stToolbar"], header, footer { visibility: hidden !important; }
    </style>
    """, unsafe_allow_html=True)
    st.session_state["css_injected"] = True

FLASK_BASE = "http://127.0.0.1:5000"

# ─── Data Loading ─────────────────────────────────────────────────────────────
# ttl=300 → Streamlit only re-fetches from Flask every 5 minutes.
# The Flask backend serves instantly from its own cache,
# so this call is nearly zero-cost after the first load.
@st.cache_data(ttl=300, show_spinner="Loading sales data…")
def load_raw_data() -> pd.DataFrame:
    """
    Hits the Flask /api/data endpoint (always returns cached data instantly).
    Heavy work: parse dates, clean strings. Cached so it only runs once per TTL.
    """
    try:
        resp = requests.get(
            f"{FLASK_BASE}/api/data",
            params={"reportType": "ProductDateWiseSale"},
            timeout=35
        )
        resp.raise_for_status()
        records = resp.json()
    except Exception as e:
        st.error(f"Could not reach API: {e}")
        return pd.DataFrame()

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["Date"])

    # Compute once, reused everywhere
    df["Main Product"] = (
        df["Product Name"].astype(str).str.split("|").str[0].str.strip()
    )
    return df


@st.cache_data(ttl=300, show_spinner=False)
def compute_all_aggregates(row_count: int, max_date: str) -> dict:
    """
    All groupby / filter / sort work happens here — once per cache TTL.
    row_count + max_date are cheap sentinel values that bust the cache
    only when underlying data actually changes.
    """
    df = load_raw_data()
    today = pd.Timestamp.today().normalize()
    today_df = df[df["Date"] == today]
    month_df = df[df["Date"].dt.month == today.month]

    def _agg(frame, col):
        return (
            frame.groupby(col)[["SOLD QTY", "Total Sales"]]
            .sum()
            .sort_values("Total Sales", ascending=False)
            .reset_index()
        )

    def _with_contrib(frame, col):
        out = _agg(frame, col)
        out["Contribution %"] = (
            out["Total Sales"] / out["Total Sales"].sum() * 100
        ).round(2)
        return out

    def _cat_top10(keyword):
        sub = df[df["Category"].str.contains(keyword, case=False, na=False)]
        if sub.empty:
            return pd.DataFrame()
        return _agg(sub, "Main Product").head(10)

    return {
        # KPIs
        "today_sales":  today_df["Total Sales"].sum(),
        "today_units":  today_df["SOLD QTY"].sum(),
        "month_sales":  month_df["Total Sales"].sum(),
        "total_units":  df["SOLD QTY"].sum(),
        # Tables
        "today_branch":    _agg(today_df, "Branch"),
        "today_category":  _agg(today_df, "Category"),
        "monthly_branch":  _with_contrib(df, "Branch"),
        "monthly_category":_with_contrib(df, "Category"),
        "top10_products": (
            df.groupby("Main Product")["Total Sales"]
            .sum().sort_values(ascending=False).head(10).reset_index()
        ),
        # Category top-10s
        "narmin_unstitched": _cat_top10("NARMIN UNSTITCHED"),
        "narmin_stitched":   _cat_top10("NARMIN STITCHED"),
        "cotton":            _cat_top10("COTTON"),
        "blended":           _cat_top10("BLENDED"),
        "winter":            _cat_top10("WINTER"),
    }


def force_refresh():
    """Tells Flask to re-fetch from Splendid Accounts, then clears Streamlit cache."""
    try:
        requests.post(
            f"{FLASK_BASE}/api/refresh",
            params={"reportType": "ProductDateWiseSale"},
            timeout=40
        )
    except Exception as e:
        st.warning(f"Refresh request failed: {e}")
    st.cache_data.clear()
    st.rerun()


# ─── UI ───────────────────────────────────────────────────────────────────────
st.title("📊 Narkins / Narmin Monthly Sales Dashboard")

if st.button("🔄 Refresh Now"):
    force_refresh()

# Load data
df = load_raw_data()
if df.empty:
    st.warning("No data available.")
    st.stop()

# Compute aggregates (cached — instant on re-renders)
agg = compute_all_aggregates(len(df), str(df["Date"].max()))

# ─── KPIs ────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Sales",    f"{agg['today_sales']:,.0f}")
c2.metric("Today's Units",    f"{agg['today_units']:,}")
c3.metric("Monthly Sales",    f"{agg['month_sales']:,.0f}")
c4.metric("Total Units Sold", f"{agg['total_units']:,}")

# ─── 4-Column Tables ─────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.subheader("📌 Today's Sale")
    st.dataframe(agg["today_branch"], height=400, use_container_width=True)
with col2:
    st.subheader("Today's Category Sale")
    st.dataframe(agg["today_category"], height=400, use_container_width=True)
with col3:
    st.subheader("Monthly Sale")
    st.dataframe(agg["monthly_branch"], height=400, use_container_width=True)
with col4:
    st.subheader("Monthly Category Sale")
    st.dataframe(agg["monthly_category"], height=400, use_container_width=True)

# ─── Top 10 Products ─────────────────────────────────────────────────────────
st.subheader("🏆 Top 10 Products by Revenue")
st.dataframe(agg["top10_products"], height=400, use_container_width=True)

# ─── Category Top 10s ────────────────────────────────────────────────────────
def show_cat(col, title, key):
    with col:
        st.subheader(title)
        data = agg[key]
        if not data.empty:
            st.dataframe(data, height=400, use_container_width=True)
        else:
            st.info("No data for this category.")

c5, c6 = st.columns(2)
show_cat(c5, "Top 10 Narmin Unstitched", "narmin_unstitched")
show_cat(c6, "Top 10 Narmin Stitched",   "narmin_stitched")

c7, c8 = st.columns(2)
show_cat(c7, "Top 10 Cotton",   "cotton")
show_cat(c8, "Top 10 Blended",  "blended")

st.subheader("Top 10 Winter")
data = agg["winter"]
if not data.empty:
    st.dataframe(data, height=400, use_container_width=True)
