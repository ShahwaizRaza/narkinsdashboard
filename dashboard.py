import streamlit as st
import pandas as pd
from main import fetch_api_data, latest_data

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="Retail Sales Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📊 Narkins / Narmin Monthly Sales Dashboard")

# ----------------------------------------------------
# LOAD DATA (CACHED)
# ----------------------------------------------------
@st.cache_data(show_spinner=False)
def load_sales_data():
    fetch_api_data("ProductDateWiseSale")

    data = latest_data.get("ProductDateWiseSale", [])
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # Create ONCE (major speed fix)
    df["Main Product"] = (
        df["Product Name"]
        .astype(str)
        .str.split("|")
        .str[0]
        .str.strip()
    )

    return df


# Refresh button
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

df = load_sales_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# ----------------------------------------------------
# GLOBAL CSS (UNCHANGED – YOUR STYLE)
# ----------------------------------------------------
st.markdown("""
<style>
div[data-testid="stDataFrame"] table {
    table-layout: fixed !important;
    width: 100% !important;
}
div[data-testid="stDataFrame"] th div {
    pointer-events: none !important;
}
div[data-testid="stDataFrame"] th {
    position: sticky !important;
    top: 0;
    z-index: 3 !important;
    background-color: #f1f1f1 !important;
}
div[data-testid="stDataFrame"] > div {
    height: 400px !important;
    overflow: auto !important;
}
[data-testid="stMetric"] {
    background-image: linear-gradient(to right, #0077C2 , #59a5f5);
    padding: 1.5rem;
    border-radius: .75rem;
}
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
  font-size: 3rem;
  color: white;
  font-weight: 500;
}
[data-testid="stToolbar"], header, footer {
    visibility: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# DATE FILTERS (ONCE)
# ----------------------------------------------------
today = pd.Timestamp.today().normalize()
df["Date"] = df["Date"].dt.normalize()

today_df = df[df["Date"] == today]
month_df = df[df["Date"].dt.month == today.month]

# ----------------------------------------------------
# KPI
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4, gap="medium")

col1.metric("Today's Sales", f"{today_df['Total Sales'].sum():,.0f}")
col2.metric("Today's Units Sold", f"{today_df['SOLD QTY'].sum():,}")
col3.metric("Monthly Sales", f"{month_df['Total Sales'].sum():,.0f}")
col4.metric("Total Units Sold", f"{df['SOLD QTY'].sum():,}")

# ----------------------------------------------------
# TODAY REPORTS
# ----------------------------------------------------
today_branch = (
    today_df.groupby("Branch")[["SOLD QTY", "Total Sales"]]
    .sum().sort_values("Total Sales", ascending=False)
    .reset_index()
)

today_category = (
    today_df.groupby("Category")[["SOLD QTY", "Total Sales"]]
    .sum().sort_values("Total Sales", ascending=False)
    .reset_index()
)

# ----------------------------------------------------
# MONTHLY CONTRIBUTION
# ----------------------------------------------------
monthly_branch = (
    month_df.groupby("Branch")[["Total Sales"]]
    .sum().reset_index()
)
monthly_branch["Contribution %"] = (
    monthly_branch["Total Sales"] /
    monthly_branch["Total Sales"].sum() * 100
).round(2)

monthly_category = (
    month_df.groupby("Category")[["Total Sales"]]
    .sum().reset_index()
)
monthly_category["Contribution %"] = (
    monthly_category["Total Sales"] /
    monthly_category["Total Sales"].sum() * 100
).round(2)

# ----------------------------------------------------
# 4 BOX LAYOUT
# ----------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.subheader("📌 Today's Sale")
c1.dataframe(today_branch, use_container_width=True)

c2.subheader("Today's Category Sale")
c2.dataframe(today_category, use_container_width=True)

c3.subheader("Monthly Sale")
c3.dataframe(monthly_branch, use_container_width=True)

c4.subheader("Monthly Category Sale")
c4.dataframe(monthly_category, use_container_width=True)

# ----------------------------------------------------
# TODAY ALL PRODUCTS
# ----------------------------------------------------
st.subheader("📦 Today's All Products")

today_products = (
    today_df.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
    .sum().sort_values("Total Sales", ascending=False)
    .reset_index()
)

st.dataframe(today_products, height=400, use_container_width=True)

# ----------------------------------------------------
# TOP 10 PRODUCTS
# ----------------------------------------------------
top_10_products = (
    df.groupby("Main Product")["Total Sales"]
    .sum().sort_values(ascending=False)
    .head(10).reset_index()
)

st.subheader("🏆 Top 10 Products (Revenue)")
st.dataframe(top_10_products, use_container_width=True)

# ----------------------------------------------------
# CATEGORY WISE TOP 10
# ----------------------------------------------------
def top10_by_category(keyword):
    temp = df[df["Category"].str.contains(keyword, case=False, na=False)]
    return (
        temp.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
        .sum().sort_values("Total Sales", ascending=False)
        .head(10).reset_index()
    )

col5, col6 = st.columns(2)
col5.subheader("Top 10 Narmin Unstitched")
col5.dataframe(top10_by_category("NARMIN UNSTITCHED"), use_container_width=True)

col6.subheader("Top 10 Narmin Stitched")
col6.dataframe(top10_by_category("NARMIN STITCHED"), use_container_width=True)

col7, col8 = st.columns(2)
col7.subheader("Top 10 Cotton")
col7.dataframe(top10_by_category("COTTON"), use_container_width=True)

col8.subheader("Top 10 Blended")
col8.dataframe(top10_by_category("BLENDED"), use_container_width=True)

col9, _ = st.columns(2)
col9.subheader("Top 10 Winter")
col9.dataframe(top10_by_category("WINTER"), use_container_width=True)
