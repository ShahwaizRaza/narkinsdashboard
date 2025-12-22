import streamlit as st
import pandas as pd
from main import fetch_api_data, latest_data
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="Sales Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------
# SESSION STATE (CRITICAL FOR LOADING FIX)
# ----------------------------------------------------
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

# ----------------------------------------------------
# LOADING SCREEN (FIRST RENDER ONLY)
# ----------------------------------------------------
loading = st.empty()

if not st.session_state.data_loaded:
    with loading.container():
        st.markdown("## 🔄 Loading Sales Dashboard")
        st.markdown("Please wait while data is being prepared...")
        st.progress(100)

# ----------------------------------------------------
# LOAD DATA (SECOND PASS)
# ----------------------------------------------------
@st.cache_data(ttl=600)
def load_base_data():
    report_type = "ProductDateWiseSale"
    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df["Date"] = df["Date"].dt.normalize()
        df["Main Product"] = (
            df["Product Name"].astype(str).str.split("|").str[0].str.strip()
        )
        return df
    return pd.DataFrame()

if not st.session_state.data_loaded:
    fetch_api_data("ProductDateWiseSale")
    st.session_state.data_loaded = True
    st.rerun()

df = load_base_data()

# ----------------------------------------------------
# STOP IF NO DATA
# ----------------------------------------------------
if df.empty:
    st.error("No data available. Please check your data source.")
    st.stop()

loading.empty()  # REMOVE LOADING SCREEN

# ----------------------------------------------------
# CLEAN & SIMPLE CSS (AFTER LOAD)
# ----------------------------------------------------
st.markdown(
    """
<style>
[data-testid="stMetric"] {
    background-color: #34495e;
    padding: 1.2rem;
    border-radius: 6px;
    border-left: 4px solid #3498db;
}
[data-testid="stMetricLabel"] {
    color: #ecf0f1;
    font-size: 0.85rem;
}
[data-testid="stMetricValue"] {
    color: white;
    font-size: 2rem;
    font-weight: 600;
}
header, footer, [data-testid="stToolbar"] {
    display: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
col1, col2 = st.columns([5, 1])
with col1:
    st.title("Narkins / Narmin Sales Dashboard")
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.session_state.data_loaded = False
        st.rerun()

# ----------------------------------------------------
# KPI METRICS
# ----------------------------------------------------
today = pd.Timestamp.today().normalize()
today_df = df[df["Date"] == today]
month_df = df[df["Date"].dt.month == today.month]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Sales", f"Rs {today_df['Total Sales'].sum():,.0f}")
c2.metric("Today's Units", f"{today_df['SOLD QTY'].sum():,}")
c3.metric("Monthly Sales", f"Rs {month_df['Total Sales'].sum():,.0f}")
c4.metric("Total Units", f"{df['SOLD QTY'].sum():,}")

st.divider()

# ----------------------------------------------------
# TABS
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Top Products", "Categories", "Trends"]
)

# ----------------------------------------------------
# OVERVIEW
# ----------------------------------------------------
with tab1:
    st.subheader("Today's Sale by Branch")
    today_branch = (
        today_df.groupby("Branch")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values("Total Sales", ascending=False)
        .reset_index()
    )
    st.dataframe(today_branch, use_container_width=True, height=380)

    st.subheader("Today's Sale by Category")
    today_category = (
        today_df.groupby("Category")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values("Total Sales", ascending=False)
        .reset_index()
    )
    st.dataframe(today_category, use_container_width=True, height=380)

# ----------------------------------------------------
# TOP PRODUCTS
# ----------------------------------------------------
with tab2:
    top_products = (
        df.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values("Total Sales", ascending=False)
        .head(10)
        .reset_index()
    )

    st.dataframe(top_products, use_container_width=True, height=380)

    fig = px.bar(
        top_products,
        x="Total Sales",
        y="Main Product",
        orientation="h",
    )
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# CATEGORIES
# ----------------------------------------------------
with tab3:
    cat_sales = (
        df.groupby("Category")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values("Total Sales", ascending=False)
        .reset_index()
    )
    st.dataframe(cat_sales, use_container_width=True, height=380)

# ----------------------------------------------------
# TRENDS
# ----------------------------------------------------
with tab4:
    daily_sales = df.groupby("Date")["Total Sales"].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily_sales["Date"],
            y=daily_sales["Total Sales"],
            mode="lines+markers",
            fill="tozeroy",
        )
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.divider()
st.caption(
    f"Last Updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')} | Cached 10 minutes"
)
