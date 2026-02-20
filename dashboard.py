import streamlit as st
import pandas as pd
from main import fetch_api_data, latest_data
import plotly.express as px
import plotly.graph_objects as go
import time

# Page config
st.set_page_config(page_title="Retail Sales Dashboard", layout="wide", initial_sidebar_state='collapsed')

st.title("📊 Narkins / Narmin Monthly Sales Dashboard")


# ----------------------------------------------------
# FETCH DATA
# ----------------------------------------------------
fetch_api_data("ProductDateWiseSale")

def get_sales_dataframe():
    report_type = "ProductDateWiseSale"
    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        return df
    return pd.DataFrame()


# Refresh button
if st.button("🔄 Refresh Now"):
    fetch_api_data("ProductDateWiseSale")
    st.cache_data.clear()
    st.rerun()

df = get_sales_dataframe()


# ----------------------------------------------------
# GLOBAL CSS FIX (NO COLUMN JUMP)
# ----------------------------------------------------
st.markdown("""
<style>

/* ----- FIX COLUMN JUMP ----- */
div[data-testid="stDataFrame"] table {
    table-layout: fixed !important;
    width: 100% !important;
}

div[data-testid="stDataFrame"] th div {
    pointer-events: none !important;   /* Disable header click resizing */
}

/* Sticky header */
div[data-testid="stDataFrame"] th {
    position: sticky !important;
    top: 0;
    z-index: 3 !important;
    background-color: #f1f1f1 !important;
}

/* Fix scroll area height */
div[data-testid="stDataFrame"] > div {
    height: 400px !important;
    overflow: auto !important;
}

/* KPI Boxes */
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

/* Hide Streamlit UI buttons */
[data-testid="stToolbar"], [data-testid="stDecoration"], header, footer {
    visibility: hidden !important;
}

</style>
""", unsafe_allow_html=True)



# ----------------------------------------------------
# IF NO DATA
# ----------------------------------------------------
if df.empty:
    st.warning("No data available.")
    st.stop()


# ----------------------------------------------------
# KPI CALCULATIONS
# ----------------------------------------------------
today = pd.Timestamp.today().normalize()
df['Date'] = df['Date'].dt.normalize()

today_sales = df[df['Date'] == today]['Total Sales'].sum()
today_units = df[df['Date'] == today]['SOLD QTY'].sum()
month_sales = df[df['Date'].dt.month == today.month]['Total Sales'].sum()
total_units = df['SOLD QTY'].sum()

col1, col2, col3, col4 = st.columns(4, gap='medium')
col1.metric("Today's Sales", f"{today_sales:,.0f}")
col2.metric("Today's Units Sold", f"{today_units:,}")
col3.metric("Monthly Sales", f"{month_sales:,.0f}")
col4.metric("Total Units Sold", f"{total_units:,}")


# ----------------------------------------------------
# GROUPING
# ----------------------------------------------------
today_sales_by_branch = (
    df[df['Date'] == today]
    .groupby('Branch')[['SOLD QTY', 'Total Sales']]
    .sum()
    .sort_values(by='Total Sales', ascending=False)
    .reset_index()
)

today_sales_by_category = (
    df[df['Date'] == today]
    .groupby('Category')[['SOLD QTY', 'Total Sales']]
    .sum()
    .sort_values(by='Total Sales', ascending=False)
    .reset_index()
)

sales_by_branch = (
    df.groupby('Branch')[['SOLD QTY', 'Total Sales']]
    .sum()
    .sort_values(by='Total Sales', ascending=False)
    .reset_index()
)

# Calculate % contribution
total_month = sales_by_branch["Total Sales"].sum()
sales_by_branch["Contribution %"] = (sales_by_branch["Total Sales"] / total_month * 100).round(2)

sales_by_category = (
    df.groupby('Category')[['SOLD QTY', 'Total Sales']]
    .sum()
    .sort_values(by='Total Sales', ascending=False)
    .reset_index()
)

# Contribution calculation
total_month_cat = sales_by_category["Total Sales"].sum()
sales_by_category["Contribution %"] = (sales_by_category["Total Sales"] / total_month_cat * 100).round(2)

# ----------------------------------------------------
# LAYOUT 4 BOXES
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("📌 Today's Sale")
    st.dataframe(today_sales_by_branch, height=400, use_container_width=True)

with col2:
    st.subheader("Today's Category Sale")
    st.dataframe(today_sales_by_category, height=400, use_container_width=True)

with col3:
    st.subheader("Monthly Sale")
    st.dataframe(
        sales_by_branch,
        hide_index=True,
        column_config={
            "Branch": st.column_config.TextColumn("Branch"),
            "Total Sales": st.column_config.NumberColumn("Sale", format="%d"),
            "Contribution %": st.column_config.NumberColumn("Contribution (%)"),
        },
        use_container_width=True
    )

with col4:
    st.subheader("Monthly Category Sale")
    st.dataframe(
        sales_by_category,
        hide_index=True,
        column_config={
            "CATEGORY": st.column_config.TextColumn("Category"),
            "Total Sales": st.column_config.NumberColumn("Sale", format="%d"),
            "Contribution %": st.column_config.NumberColumn("Contribution (%)"),
        },
        use_container_width=True
    )


# ----------------------------------------------------
# TODAY'S ALL PRODUCTS SCROLLABLE
# ----------------------------------------------------
st.subheader("📦 Today's All Products")

df["Main Product"] = (
    df["Product Name"].astype(str).str.split("|").str[0].str.strip()
)

today_data = df[df["Date"] == today]

all_today_products = (
    today_data
    .groupby("Main Product")[["SOLD QTY", "Total Sales"]]
    .sum()
    .sort_values(by="Total Sales", ascending=False)
    .reset_index()
)

st.dataframe(
    all_today_products,
    height=400,
    use_container_width=True,
    hide_index=True
)


# ----------------------------------------------------
# TOP 10 MAIN PRODUCTS
# ----------------------------------------------------
top_10_products = (
    df.groupby("Main Product")["Total Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

col5, col6 = st.columns(2)

with col5:
    st.subheader("Top 10 Products (Revenue)")
    st.dataframe(top_10_products, height=400, use_container_width=True)


# ----------------------------------------------------
# TOP 10 NARMIN UNSTITCHED
# ----------------------------------------------------
narmin_un = df[df['Category'].str.contains("NARMIN UNSTITCHED", case=False, na=False)]
narmin_un["Product"] = narmin_un["Product Name"].str.split("|").str[0].str.strip()

top_10_nu = (
    narmin_un.groupby("Product")[["SOLD QTY", "Total Sales"]]
    .sum()
    .sort_values(by="Total Sales", ascending=False)
    .head(10)
    .reset_index()
)

with col6:
    st.subheader("Top 10 Narmin Unstitched")
    st.dataframe(top_10_nu, height=400, use_container_width=True)


# ----------------------------------------------------
# MORE CATEGORY TABLES
# ----------------------------------------------------
narmin_stitched = df[df['Category'].str.contains("NARMIN STITCHED", case=False, na=False)]
cotton = df[df['Category'].str.contains("COTTON", case=False, na=False)]

col7, col8 = st.columns(2)

with col7:
    st.subheader("Top 10 Narmin Stitched")
    narmin_stitched["Main Product"] = narmin_stitched["Product Name"].str.split("|").str[0].str.strip()

    top_10_ns = (
        narmin_stitched.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values(by="Total Sales", ascending=False)
        .head(10)
        .reset_index()
    )
    st.dataframe(top_10_ns, height=400, use_container_width=True)

with col8:
    st.subheader("Top 10 Cotton")
    cotton["Product Name"] = cotton["Product Name"].str.split("|").str[0].str.strip()

    top_10_cotton = (
        cotton.groupby("Product Name")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values(by="Total Sales", ascending=False)
        .head(10)
        .reset_index()
    )
    st.dataframe(top_10_cotton, height=400, use_container_width=True)


# ----------------------------------------------------
# BLENDED
# ----------------------------------------------------
blended = df[df['Category'].str.contains("BLENDED", case=False, na=False)]

col9 = st.columns(1)

with col9:
    st.subheader("Top 10 Blended")
    blended["Product Name"] = blended["Product Name"].str.split("|").str[0].str.strip()

    top_10_blend = (
        blended.groupby("Product Name")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values(by="Total Sales", ascending=False)
        .head(10)
        .reset_index()
    )
    st.dataframe(top_10_blend, height=400, use_container_width=True)

