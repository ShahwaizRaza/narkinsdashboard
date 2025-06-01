import streamlit as st
import pandas as pd
from main import fetch_api_data, latest_data
import plotly.express as px
import plotly.graph_objects as go
import time

# Set Streamlit page config
st.set_page_config(page_title="Retail Sales Dashboard", layout="wide", initial_sidebar_state='collapsed')

st.title("📊 Narkins / Narmins Monthly Sales Dashboard")

# Fetch data
fetch_api_data("ProductDateWiseSale")

if st.button("🔄 Refresh Now"):
    fetch_api_data("ProductDateWiseSale")  # Fetch fresh data
    st.cache_data.clear()  # Clear the cache so it re-runs the function
    st.rerun()  # Reload the script with updated data
    get_sales_dataframe()
    
def get_sales_dataframe():
    report_type = "ProductDateWiseSale"
    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        return df
    return pd.DataFrame()


df = get_sales_dataframe()


#######################
# CSS styling
st.markdown("""
<style>
        
[data-testid="stMetric"] {
    background-image: linear-gradient(to right, #0077C2 , #59a5f5);
    padding-top: 1.5rem;
    padding-bottom: 1.5rem;
    padding-left: 1.5rem;
    border-radius: .75rem;
}

[data-testid="stMetricLabel"] {
  font-size: 3rem;
  line-height: 1;
  color: white;
  font-weight: 500;
}

[data-testid="stMetricValue"] {
  font-size: 3rem;
  line-height: 1;
  color: white;
  font-weight: 500;
}

div[data-testid="stDataFrame"] .st-emotion-cache-1p5d0ke {
    background-color: #0077C2 !important;  /* Your desired fill color */
}

/* Optional: Change background track color */
div[data-testid="stDataFrame"] .st-emotion-cache-1dp5vir {
    background-color: #f0f0f0 !important;  /* Lighter track */
}


</style>
""", unsafe_allow_html=True)


if df.empty:
    st.warning("No data available to display.")
else:
    # KPI Calculations (No filtering)
    today = pd.Timestamp.today().normalize()
    df['Date'] = pd.to_datetime(df['Date']).dt.normalize()

    today_sales = df[df['Date'] == today]['Total Sales'].sum()
    today_units = df[df['Date'] == today]['SOLD QTY'].sum()
    month_sales = df[df['Date'].dt.month == today.month]['Total Sales'].sum()
    total_units = df['SOLD QTY'].sum()
    
    col1, col2, col3, col4= st.columns(4, gap='medium')
    col1.metric("Today's Sales", f"{today_sales:,.0f}")
    col2.metric("Today's Units Sold", f"{today_units:,}")
    col3.metric("Monthly Sales", f"{month_sales:,.0f}")
    col4.metric("Total Units Sold", f"{total_units:,}")
    
    # Aggregations
    today_sales_by_branch = (
        df[df['Date'] == today]
        .groupby('Branch')[['SOLD QTY', 'Total Sales']]
        .sum()
        .sort_values(by='Total Sales', ascending=False)
        .reset_index()
    )
    
    # Aggregations
    today_sales_by_category = (
        df[df['Date'] == today]
        .groupby('Category')[['SOLD QTY', 'Total Sales']]
        .sum()
        .sort_values(by='Total Sales', ascending=False)
        .reset_index()
    )
    
    sales_by_branch = (
        df[df['Date'].dt.month == today.month]
        .groupby('Branch')[['SOLD QTY', 'Total Sales']]
        .sum()
        .sort_values(by='Total Sales', ascending=False)
        .reset_index()
    )

    sales_by_category = (
        df.groupby('Category')[['SOLD QTY', 'Total Sales']]
        .sum()
        .sort_values(by='Total Sales', ascending=False)
        .reset_index()
    )

    # Create columns for side by side layout
    col1, col2 = st.columns(2, gap='medium')
    
    with col1:
        st.markdown("#### 📌 Sale by Branch Today's")
        st.dataframe(
            today_sales_by_branch,
            column_order=("Branch", "SOLD QTY", "Total Sales"),
            hide_index=True,
            column_config={
                "Branch": st.column_config.TextColumn("Branch"),
                "SOLD QTY": st.column_config.TextColumn("SOLD QTY"),
                "Total Sales": st.column_config.ProgressColumn(
                    "Sales",
                    format="PKR %.0f",
                    min_value=0,
                    max_value=sales_by_branch["Total Sales"].max()
                )
            },
            use_container_width=True
        )
        
    with col2:
        st.markdown("#### Sale by Product Category Today's")
        st.dataframe(
            today_sales_by_category,
            column_order=("Category", "SOLD QTY", "Total Sales"),
            hide_index=True,
            column_config={
                "Category": st.column_config.TextColumn("Category"),
                "SOLD QTY": st.column_config.TextColumn("SOLD QTY"),
                "Total Sales": st.column_config.ProgressColumn(
                    "Sales",
                    format="PKR %.0f",
                    min_value=0,
                    max_value=sales_by_category["Total Sales"].max()
                )
            },
            use_container_width=True
        )
    # Create columns for side by side layout
    col3, col4 = st.columns(2, gap='medium')
    with col3:
        st.markdown("#### Sale by Branch")
        st.dataframe(
            sales_by_branch,
            column_order=("Branch", "SOLD QTY", "Total Sales"),
            hide_index=True,
            column_config={
                "Branch": st.column_config.TextColumn("Branch"),
                "SOLD QTY": st.column_config.TextColumn("SOLD QTY"),
                "Total Sales": st.column_config.ProgressColumn(
                    "Sales",
                    format="PKR %.0f",
                    min_value=0,
                    max_value=sales_by_branch["Total Sales"].max()
                )
            },
            use_container_width=True
        )
        
    with col4:
        st.markdown("#### Sale by Product Category")
        st.dataframe(
            sales_by_category,
            column_order=("Category", "SOLD QTY", "Total Sales"),
            hide_index=True,
            column_config={
                "Category": st.column_config.TextColumn("Category"),
                "SOLD QTY": st.column_config.TextColumn("SOLD QTY"),
                "Total Sales": st.column_config.ProgressColumn(
                    "Sales",
                    format="PKR %.0f",
                    min_value=0,
                    max_value=sales_by_category["Total Sales"].max()
                )
            },
            use_container_width=True
        )
    
    # Top 10 Products by Revenue
    top_10_products = df.groupby('Product Name')['Total Sales'].sum().sort_values(ascending=False).head(10).reset_index()

    # Top 5 Branches by Sales
    top_5_branches = df.groupby('Branch')['Total Sales'].sum().sort_values(ascending=False).head(5).reset_index()

    # Display Side-by-Side
    col5, col6 = st.columns(2, gap='medium')

    with col5:
        st.subheader("Top 10 Products by Revenue")
        st.dataframe(top_10_products)

    with col6:
        st.subheader("Top 5 Branches by Sales")
        st.dataframe(top_5_branches)
