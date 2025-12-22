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
# CACHE API CALL
# ----------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data():
    fetch_api_data("ProductDateWiseSale")

    data = latest_data.get("ProductDateWiseSale", [])
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # Create once (BIG SPEED BOOST)
    df["Main Product"] = (
        df["Product Name"]
        .astype(str)
        .str.split("|")
        .str[0]
        .str.strip()
    )

    return df


# Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

df = load_data()

if df.empty:
    st.warning("No data available")
    st.stop()

# ----------------------------------------------------
# CSS (NO COLUMN JUMP)
# ----------------------------------------------------
st.markdown("""
<style>
div[data-testid="stDataFrame"] table {
    table-layout: fixed !important;
}
div[data-testid="stDataFrame"] th div {
    pointer-events: none !important;
}
div[data-testid="stDataFrame"] > div {
    height: 400px !important;
    overflow: auto !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# DATE FILTERS
# ----------------------------------------------------
today = pd.Timestamp.today().normalize()
df["Date"] = df["Date"].dt.normalize()

today_df = df[df["Date"] == today]
month_df = df[df["Date"].dt.month == today.month]

# ----------------------------------------------------
# KPI
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Today's Sales", f"{today_df['Total Sales'].sum():,.0f}")
col2.metric("Today's Units", f"{today_df['SOLD QTY'].sum():,}")
col3.metric("Monthly Sales", f"{month_df['Total Sales'].sum():,.0f}")
col4.metric("Total Units", f"{df['SOLD QTY'].sum():,}")

# ----------------------------------------------------
# TODAY SALES
# ----------------------------------------------------
today_branch = (
    today_df.groupby("Branch")[["SOLD QTY", "Total Sales"]]
    .sum()
    .sort_values("Total Sales", ascending=False)
    .reset_index()
)

today_category = (
    today_df.groupby("Category")[["SOLD QTY", "Total Sales"]]
    .sum()
    .sort_values("Total Sales", ascending=False)
    .reset_index()
)

# ----------------------------------------------------
# MONTHLY CONTRIBUTION (FAST)
# ----------------------------------------------------
monthly_branch = (
    month_df.groupby("Branch")[["Total Sales"]]
    .sum()
    .reset_index()
)
monthly_branch["Contribution %"] = (
    monthly_branch["Total Sales"] / monthly_branch["Total Sales"].sum() * 100
).round(2)

monthly_category = (
    month_df.groupby("Category")[["Total Sales"]]
    .sum()
    .reset_index()
)
monthly_category["Contribution %"] = (
    monthly_category["Total Sales"] / monthly_category["Total Sales"].sum() * 100
).round(2)

# ----------------------------------------------------
# DISPLAY TABLES
# ----------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.subheader("📌 Today's Sale")
    st.dataframe(today_branch, use_container_width=True)

with c2:
    st.subheader("Today's Category Sale")
    st.dataframe(today_category, use_container_width=True)

with c3:
    st.subheader("Monthly Sale")
    st.dataframe(monthly_branch, use_container_width=True)

with c4:
    st.subheader("Monthly Category Sale")
    st.dataframe(monthly_category, use_container_width=True)

# ----------------------------------------------------
# TODAY ALL PRODUCTS (SCROLL)
# ----------------------------------------------------
st.subheader("📦 Today's All Products")

today_products = (
    today_df.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
    .sum()
    .sort_values("Total Sales", ascending=False)
    .reset_index()
)

st.dataframe(today_products, height=400, use_container_width=True)

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

st.subheader("🏆 Top 10 Products (Revenue)")
st.dataframe(top_10_products, use_container_width=True)
