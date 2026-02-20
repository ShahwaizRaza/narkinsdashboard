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
# FETCH DATA (RUN ONCE)
# ----------------------------------------------------
fetch_api_data("ProductDateWiseSale")

def get_sales_dataframe():
    report_type = "ProductDateWiseSale"
    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        return df
    return pd.DataFrame()

if st.button("🔄 Refresh Now"):
    fetch_api_data("ProductDateWiseSale")
    st.cache_data.clear()
    st.rerun()

df = get_sales_dataframe()

# ----------------------------------------------------
# STOP IF NO DATA
# ----------------------------------------------------
if df.empty:
    st.warning("No data available.")
    st.stop()

# ----------------------------------------------------
# CREATE MAIN PRODUCT (ONCE)
# ----------------------------------------------------
df["Main Product"] = (
    df["Product Name"]
    .astype(str)
    .str.split("|")
    .str[0]
    .str.strip()
)

# ----------------------------------------------------
# GLOBAL CSS (NO COLUMN JUMP)
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
    background: #f1f1f1 !important;
    z-index: 3 !important;
}
[data-testid="stMetric"] {
    background-image: linear-gradient(to right, #0077C2 , #59a5f5);
    padding: 1.5rem;
    border-radius: .75rem;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    font-size: 2.5rem;
    color: white;
    font-weight: 500;
}
[data-testid="stToolbar"], header, footer {
    visibility: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# KPI CALCULATIONS
# ----------------------------------------------------
today = pd.Timestamp.today().normalize()
df["Date"] = df["Date"].dt.normalize()

today_sales = df[df["Date"] == today]["Total Sales"].sum()
today_units = df[df["Date"] == today]["SOLD QTY"].sum()
month_sales = df[df["Date"].dt.month == today.month]["Total Sales"].sum()
total_units = df["SOLD QTY"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Sales", f"{today_sales:,.0f}")
c2.metric("Today's Units", f"{today_units:,}")
c3.metric("Monthly Sales", f"{month_sales:,.0f}")
c4.metric("Total Units Sold", f"{total_units:,}")

# ----------------------------------------------------
# TODAY SALES
# ----------------------------------------------------
today_branch = (
    df[df["Date"] == today]
    .groupby("Branch")[["SOLD QTY", "Total Sales"]]
    .sum()
    .sort_values("Total Sales", ascending=False)
    .reset_index()
)

today_category = (
    df[df["Date"] == today]
    .groupby("Category")[["SOLD QTY", "Total Sales"]]
    .sum()
    .sort_values("Total Sales", ascending=False)
    .reset_index()
)

# ----------------------------------------------------
# MONTHLY SALES + CONTRIBUTION
# ----------------------------------------------------
monthly_branch = (
    df.groupby("Branch")[["SOLD QTY", "Total Sales"]]
    .sum()
    .sort_values("Total Sales", ascending=False)
    .reset_index()
)
monthly_branch["Contribution %"] = (
    monthly_branch["Total Sales"] / monthly_branch["Total Sales"].sum() * 100
).round(2)

monthly_category = (
    df.groupby("Category")[["SOLD QTY", "Total Sales"]]
    .sum()
    .sort_values("Total Sales", ascending=False)
    .reset_index()
)
monthly_category["Contribution %"] = (
    monthly_category["Total Sales"] / monthly_category["Total Sales"].sum() * 100
).round(2)

# ----------------------------------------------------
# 4 TABLE LAYOUT
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("📌 Today's Sale")
    st.dataframe(today_branch, height=400, use_container_width=True)

with col2:
    st.subheader("Today's Category Sale")
    st.dataframe(today_category, height=400, use_container_width=True)

with col3:
    st.subheader("Monthly Sale")
    st.dataframe(monthly_branch, height=400, use_container_width=True)

with col4:
    st.subheader("Monthly Category Sale")
    st.dataframe(monthly_category, height=400, use_container_width=True)

# ----------------------------------------------------
# TOP 10 PRODUCTS
# ----------------------------------------------------
top_10_products = (
    df.groupby("Main Product")["Total Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

st.subheader("🏆 Top 10 Products by Revenue")
st.dataframe(top_10_products, height=400, use_container_width=True)

# ----------------------------------------------------
# CATEGORY-WISE TOP 10
# ----------------------------------------------------
def top10_by_category(keyword, title):
    data = df[df["Category"].str.contains(keyword, case=False, na=False)]
    if data.empty:
        return
    top10 = (
        data.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values("Total Sales", ascending=False)
        .head(10)
        .reset_index()
    )
    st.subheader(title)
    st.dataframe(top10, height=400, use_container_width=True)

c5, c6 = st.columns(2)
with c5:
    top10_by_category("NARMIN UNSTITCHED", "Top 10 Narmin Unstitched")
with c6:
    top10_by_category("NARMIN STITCHED", "Top 10 Narmin Stitched")

c7, c8 = st.columns(2)
with c7:
    top10_by_category("COTTON", "Top 10 Cotton")
with c8:
    top10_by_category("BLENDED", "Top 10 Blended")

st.subheader("Top 10 Winter")
top10_by_category("WINTER", "")
