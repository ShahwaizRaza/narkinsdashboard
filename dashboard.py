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


df = get_sales_dataframe()


#######################
# CSS styling
st.markdown("""
<style>

#MainMenu {visibility: hidden;}         /* Hides the hamburger menu */
footer {visibility: hidden;}            /* Hides the footer ("Made with Streamlit") */
header {visibility: hidden;}            /* Hides the main header */

/* Hide sidebar completely */
[data-testid="stSidebar"] {
    display: none;
}
    
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
    # Sidebar filters
    st.sidebar.header("Filter Options")
    
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    branches = df['Branch'].unique().tolist()
    selected_branch = st.sidebar.multiselect("Select Branch(es)", options=branches, default=branches)
    
    # Filter dataframe by date and branch
    start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)
    mask = (df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date)) & (df['Branch'].isin(selected_branch))
    filtered_df = df.loc[mask]
    
    # KPIs
    today = pd.Timestamp.today().normalize()
    today_sales = filtered_df[filtered_df['Date'] == today]['Total Sales'].sum()
    today_units = filtered_df[filtered_df['Date'] == today]['SOLD QTY'].sum()
    month_sales = filtered_df[filtered_df['Date'].dt.month == today.month]['Total Sales'].sum()
    total_units = filtered_df['SOLD QTY'].sum()
    
    col1, col2, col3, col4= st.columns(4, gap='medium')
    col1.metric("Today's Sales", f"{today_sales:,.0f}")
    col2.metric("Today's Units Sold", f"{today_units:,}")
    col3.metric("Monthly Sales", f"{month_sales:,.0f}")
    col4.metric("Total Units Sold", f"{total_units:,}")
    
    # Prepare data (make sure filtered_df is your dataframe with the data)
    # Prepare data
    sales_by_branch = (
        filtered_df.groupby('Branch')[['SOLD QTY', 'Total Sales']]
        .sum()
        .sort_values(by='Total Sales', ascending=False)
        .reset_index()
    )

    sales_by_category = (
        filtered_df.groupby('Category')[['SOLD QTY', 'Total Sales']]
        .sum()
        .sort_values(by='Total Sales', ascending=False)
        .reset_index()
    )

    # Create columns for side by side layout
    col1, col2 = st.columns(2, gap='medium')
    
    with col1:
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
        
    with col2:
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
    
    
    
    #with col1:
    #    st.subheader("Sales by Branch")
    #    fig_branch = px.bar(
    #        sales_by_branch, 
    #       x='Branch', y='Total Sales',
    #        labels={'Total Sales': 'Total Sales (PKR)', 'Branch': 'Branch'},
    #        #title="Sales by Branch",
    #        color='Total Sales',
    #        color_continuous_scale='Blues'
    #    )
    #    st.plotly_chart(fig_branch, use_container_width=True)

    #with col2:
    #    #st.subheader("Sales by Product Category")
    #    fig_category = px.bar(
    #        sales_by_category,
    #        x='Category', y='Total Sales',
    #        labels={'Total Sales': 'Total Sales (PKR)', 'Category': 'Category'},
    #        title="Sales by Product Category",
    #        color='Total Sales',
    #        color_continuous_scale='Oranges'
    #    )
    #    st.plotly_chart(fig_category, use_container_width=True)
    
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
