import streamlit as st
import pandas as pd
from main import fetch_api_data, latest_data
import plotly.express as px
import plotly.graph_objects as go
import time


# Set Streamlit page config
st.set_page_config(page_title="Retail Sales Dashboard", layout="wide", initial_sidebar_state='collapsed')

st.title("📊 Narkins / Narmin Monthly Sales Dashboard")

# Fetch data
fetch_api_data("ProductDateWiseSale")

def get_sales_dataframe():
    report_type = "ProductDateWiseSale"
    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        return df
    return pd.DataFrame()

if st.button("🔄 Refresh Now"):
    fetch_api_data("ProductDateWiseSale")  # Fetch fresh data
    st.cache_data.clear()  # Clear the cache so it re-runs the function
    st.rerun()  # Reload the script with updated data
    get_sales_dataframe()


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

/* Hide the top-right icons and manage app button */
[data-testid="stDecoration"],   /* top-right buttons like Share, GitHub */
[data-testid="stSidebarNav"] {  /* "Manage app" button */
    display: none !important;
}

/* Optional: hide Streamlit menu */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Hide top right buttons: Share, GitHub, Edit */
[data-testid="stToolbar"],
[data-testid="stDecoration"],
header, footer {
    visibility: hidden !important;
}

/* Hide "Manage app" sidebar */
[data-testid="stSidebarNav"] {
    display: none !important;
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
        df.groupby('Branch')[['SOLD QTY', 'Total Sales']]
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
    col1, col2, col3, col4 = st.columns(4, gap='medium')
    
    
        
    with col1:
        st.subheader("📌 Today's Sale")
        st.dataframe(today_sales_by_branch)
    with col2:
        st.subheader("Today's Category Sale")
        st.dataframe(today_sales_by_category)
    with col3:
        st.subheader("Monthly Sale")
        st.dataframe(sales_by_branch)
    with col4:
        st.subheader("Monthly Category Sale")
        st.dataframe(sales_by_category)
    
    # Top 10 Products by Revenue (PRODUCT only)
    df["Main Product"] = (
        df["Product Name"].astype(str)
        .str.split("|")
        .str[0]
        .str.strip()
    )

    top_10_products = (
        df.groupby("Main Product")["Total Sales"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    
    # Filter the DataFrame for Narmin Unstitched category
    narmin_unstitched_df = df[df['Category'].str.contains("NARMIN UNSTITCHED", case=False, na=False)]

    # Display Side-by-Side
    col5, col6 = st.columns(2, gap='medium')

    with col5:
        st.subheader("Top 10 Products by Revenue")
        st.dataframe(top_10_products)
        
    with col6:
        st.subheader("Top 10 Narmin Unstitched (Product Only)")

        # Extract product only
        narmin_unstitched_df["Product"] = (
            narmin_unstitched_df["Product Name"]
            .astype(str)
            .str.split("|")
            .str[0]
            .str.strip()
        )

        # Group and sort by Main Product
        top_10_narmin = (
            narmin_unstitched_df
            .groupby("Product")[["SOLD QTY", "Total Sales"]]
            .sum()
            .sort_values(by="Total Sales", ascending=False)
            .head(10)
            .reset_index()
        )

        # Show table
        st.dataframe(
            top_10_narmin,
            column_order=["Product", "SOLD QTY", "Total Sales"],
            hide_index=True,
            column_config={
                "Main Product": st.column_config.TextColumn("Product"),
                "SOLD QTY": st.column_config.NumberColumn("Quantity", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Amount"),
            },
            use_container_width=True
        )
        
    # Filter the DataFrame for Narmin Unstitched category
    narmin_stitched_df = df[df['Category'].str.contains("NARMIN STITCHED", case=False, na=False)]
    cotton_df = df[df['Category'].str.contains("COTTON", case=False, na=False)]

    # Display Side-by-Side
    col7, col8 = st.columns(2, gap='medium')

    with col7:
        st.subheader("Top 10 Narmin Stitched (Product Only)")

        # Extract product only
        narmin_stitched_df["Main Product"] = (
            narmin_stitched_df["Product Name"]
            .astype(str)
            .str.split("|")
            .str[0]
            .str.strip()
        )

        # Group and sort
        top_10_narmin = (
            narmin_stitched_df
            .groupby("Main Product")[["SOLD QTY", "Total Sales"]]
            .sum()
            .sort_values(by="Total Sales", ascending=False)
            .head(10)
            .reset_index()
        )

        # Show table
        st.dataframe(
            top_10_narmin,
            column_order=["Main Product", "SOLD QTY", "Total Sales"],
            hide_index=True,
            column_config={
                "Main Product": st.column_config.TextColumn("Product"),
                "SOLD QTY": st.column_config.NumberColumn("Quantity", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Amount"),
            },
            use_container_width=True
        )
        
    with col8:
        st.subheader("Top 10 Cotton Products")
        
        # Extract product only
        cotton_df["Product Name"] = (
            cotton_df["Product Name"]
            .astype(str)
            .str.split("|")
            .str[0]
            .str.strip()
        )
        
        # Group and sort
        top_10_cotton = (
            cotton_df
            .groupby('Product Name')[['SOLD QTY', 'Total Sales']]
            .sum()
            .sort_values(by='Total Sales', ascending=False)
            .head(10)
            .reset_index()
        )

        # Show table
        st.dataframe(
            top_10_cotton,
            column_order=["Product Name", "SOLD QTY", "Total Sales"],
            hide_index=True,
            column_config={
                "Product Name": st.column_config.TextColumn("Product"),
                "SOLD QTY": st.column_config.NumberColumn("Quantity", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Amount"   ),
            },
            use_container_width=True
        )
        
        # Filter the DataFrame for Narmin Unstitched category
    blended_df = df[df['Category'].str.contains("BLENDED", case=False, na=False)]
    winter_df = df[df['Category'].str.contains("WINTER", case=False, na=False)]

    # Display Side-by-Side
    col9, col10 = st.columns(2, gap='medium')

    with col9:
        st.subheader("Top 10 Blended Products")
        
        # Extract product only
        blended_df["Product Name"] = (
            blended_df["Product Name"]
            .astype(str)
            .str.split("|")
            .str[0]
            .str.strip()
        )
        
        # Group and sort
        top_10_blended = (
            blended_df
            .groupby('Product Name')[['SOLD QTY', 'Total Sales']]
            .sum()
            .sort_values(by='Total Sales', ascending=False)
            .head(10)
            .reset_index()
        )

        # Show table
        st.dataframe(
            top_10_blended,
            column_order=["Product Name", "SOLD QTY", "Total Sales"],
            hide_index=True,
            column_config={
                "Product Name": st.column_config.TextColumn("Product"),
                "SOLD QTY": st.column_config.NumberColumn("Quantity", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Amount"   ),
            },
            use_container_width=True
        )
        
    with col10:
        st.subheader("Top 10 Winter Products")
        
        # Extract product only
        winter_df["Product Name"] = (
            winter_df["Product Name"]
            .astype(str)
            .str.split("|")
            .str[0]
            .str.strip()
        )
        
        # Group and sort
        top_10_winter = (
            winter_df
            .groupby('Product Name')[['SOLD QTY', 'Total Sales']]
            .sum()
            .sort_values(by='Total Sales', ascending=False)
            .head(10)
            .reset_index()
        )

        # Show table
        st.dataframe(
            top_10_winter,
            column_order=["Product Name", "SOLD QTY", "Total Sales"],
            hide_index=True,
            column_config={
                "Product Name": st.column_config.TextColumn("Product"),
                "SOLD QTY": st.column_config.NumberColumn("Quantity", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Amount"   ),
            },
            use_container_width=True
        )

