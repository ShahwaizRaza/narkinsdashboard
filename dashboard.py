import streamlit as st
import pandas as pd
from main import fetch_api_data, latest_data
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Page config
st.set_page_config(
    page_title="Retail Sales Dashboard", 
    layout="wide", 
    initial_sidebar_state='collapsed'
)

# ----------------------------------------------------
# CACHING FOR PERFORMANCE
# ----------------------------------------------------
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_sales_dataframe():
    """Fetch and process sales data with caching"""
    report_type = "ProductDateWiseSale"
    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Date'] = df['Date'].dt.normalize()
        # Pre-process main product column once
        df["Main Product"] = df["Product Name"].astype(str).str.split("|").str[0].str.strip()
        return df
    return pd.DataFrame()

@st.cache_data(ttl=300)
def calculate_all_metrics(df, today):
    """Calculate all metrics at once to avoid repeated calculations"""
    today_df = df[df['Date'] == today]
    month_df = df[df['Date'].dt.month == today.month]
    
    metrics = {
        'today_sales': today_df['Total Sales'].sum(),
        'today_units': today_df['SOLD QTY'].sum(),
        'month_sales': month_df['Total Sales'].sum(),
        'total_units': df['SOLD QTY'].sum(),
        'today_by_branch': today_df.groupby('Branch')[['SOLD QTY', 'Total Sales']].sum().sort_values(by='Total Sales', ascending=False).reset_index(),
        'today_by_category': today_df.groupby('Category')[['SOLD QTY', 'Total Sales']].sum().sort_values(by='Total Sales', ascending=False).reset_index(),
        'month_by_branch': df.groupby('Branch')[['SOLD QTY', 'Total Sales']].sum().sort_values(by='Total Sales', ascending=False).reset_index(),
        'month_by_category': df.groupby('Category')[['SOLD QTY', 'Total Sales']].sum().sort_values(by='Total Sales', ascending=False).reset_index(),
        'today_all_products': today_df.groupby("Main Product")[["SOLD QTY", "Total Sales"]].sum().sort_values(by="Total Sales", ascending=False).reset_index()
    }
    
    # Add contribution percentages
    total_month = metrics['month_by_branch']["Total Sales"].sum()
    metrics['month_by_branch']["Contribution %"] = (metrics['month_by_branch']["Total Sales"] / total_month * 100).round(2)
    
    total_month_cat = metrics['month_by_category']["Total Sales"].sum()
    metrics['month_by_category']["Contribution %"] = (metrics['month_by_category']["Total Sales"] / total_month_cat * 100).round(2)
    
    return metrics

@st.cache_data(ttl=300)
def get_top_products(df, category_filter=None, limit=10):
    """Get top products with optional category filter"""
    if category_filter:
        df_filtered = df[df['Category'].str.contains(category_filter, case=False, na=False)]
    else:
        df_filtered = df
    
    return (
        df_filtered.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values(by="Total Sales", ascending=False)
        .head(limit)
        .reset_index()
    )

# ----------------------------------------------------
# ENHANCED CSS
# ----------------------------------------------------
st.markdown("""
<style>
/* Fix column jump */
div[data-testid="stDataFrame"] table {
    table-layout: fixed !important;
    width: 100% !important;
}

div[data-testid="stDataFrame"] th div {
    pointer-events: none !important;
}

/* Sticky header */
div[data-testid="stDataFrame"] th {
    position: sticky !important;
    top: 0;
    z-index: 3 !important;
    background-color: #1e3a5f !important;
    color: white !important;
}

/* Scrollable dataframes */
div[data-testid="stDataFrame"] > div {
    height: 380px !important;
    overflow: auto !important;
}

/* Enhanced KPI boxes with gradient */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

[data-testid="stMetricLabel"] {
    font-size: 1rem !important;
    color: rgba(255, 255, 255, 0.9) !important;
    font-weight: 600 !important;
}

[data-testid="stMetricValue"] {
    font-size: 2.5rem !important;
    color: white !important;
    font-weight: 700 !important;
}

/* Subheader styling */
.stApp h3 {
    color: #1e3a5f;
    border-bottom: 3px solid #667eea;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Hide Streamlit branding */
[data-testid="stToolbar"], [data-testid="stDecoration"], header, footer {
    visibility: hidden !important;
}

/* Loading spinner */
.stSpinner > div {
    border-top-color: #667eea !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# HEADER WITH AUTO-REFRESH
# ----------------------------------------------------
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.title("📊 Narkins / Narmin Sales Dashboard")
with col_refresh:
    auto_refresh = st.checkbox("Auto-refresh (5min)", value=False)
    if st.button("🔄 Refresh", use_container_width=True):
        fetch_api_data("ProductDateWiseSale")
        st.cache_data.clear()
        st.rerun()

# Auto-refresh logic
if auto_refresh:
    time.sleep(300)  # 5 minutes
    st.rerun()

# ----------------------------------------------------
# FETCH DATA
# ----------------------------------------------------
with st.spinner("Loading data..."):
    fetch_api_data("ProductDateWiseSale")
    df = get_sales_dataframe()

if df.empty:
    st.error("⚠️ No data available. Please check your data source.")
    st.stop()

# ----------------------------------------------------
# DATE FILTER (SIDEBAR)
# ----------------------------------------------------
with st.sidebar:
    st.header("⚙️ Filters")
    
    date_range = st.date_input(
        "Date Range",
        value=(df['Date'].min(), df['Date'].max()),
        min_value=df['Date'].min(),
        max_value=df['Date'].max()
    )
    
    if len(date_range) == 2:
        df = df[(df['Date'] >= pd.Timestamp(date_range[0])) & 
                (df['Date'] <= pd.Timestamp(date_range[1]))]
    
    selected_branches = st.multiselect(
        "Select Branches",
        options=df['Branch'].unique(),
        default=df['Branch'].unique()
    )
    
    if selected_branches:
        df = df[df['Branch'].isin(selected_branches)]

# ----------------------------------------------------
# KPI METRICS
# ----------------------------------------------------
today = pd.Timestamp.today().normalize()
metrics = calculate_all_metrics(df, today)

col1, col2, col3, col4 = st.columns(4, gap='medium')
col1.metric("💰 Today's Sales", f"₨ {metrics['today_sales']:,.0f}")
col2.metric("📦 Today's Units", f"{metrics['today_units']:,}")
col3.metric("📈 Monthly Sales", f"₨ {metrics['month_sales']:,.0f}")
col4.metric("🎯 Total Units", f"{metrics['total_units']:,}")

st.divider()

# ----------------------------------------------------
# TABS FOR BETTER ORGANIZATION
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏆 Top Products", "📁 Categories", "📈 Trends"])

with tab1:
    # Today's performance
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("📌 Today's Sale by Branch")
        st.dataframe(metrics['today_by_branch'], height=380, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("📊 Today's Category Sale")
        st.dataframe(metrics['today_by_category'], height=380, use_container_width=True, hide_index=True)
    
    with col3:
        st.subheader("🏪 Monthly Sale by Branch")
        st.dataframe(
            metrics['month_by_branch'],
            height=380,
            hide_index=True,
            column_config={
                "Branch": st.column_config.TextColumn("Branch"),
                "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Sales", format="₨%d"),
                "Contribution %": st.column_config.ProgressColumn("Contribution", format="%.2f%%", min_value=0, max_value=100),
            },
            use_container_width=True
        )
    
    with col4:
        st.subheader("📁 Monthly Category Sale")
        st.dataframe(
            metrics['month_by_category'],
            height=380,
            hide_index=True,
            column_config={
                "Category": st.column_config.TextColumn("Category"),
                "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Sales", format="₨%d"),
                "Contribution %": st.column_config.ProgressColumn("Contribution", format="%.2f%%", min_value=0, max_value=100),
            },
            use_container_width=True
        )
    
    st.divider()
    
    # Today's all products
    st.subheader("📦 Today's All Products")
    st.dataframe(
        metrics['today_all_products'],
        height=400,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Main Product": st.column_config.TextColumn("Product", width="large"),
            "SOLD QTY": st.column_config.NumberColumn("Units Sold", format="%d"),
            "Total Sales": st.column_config.NumberColumn("Revenue", format="₨%d"),
        }
    )

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Products (Overall)")
        top_10 = get_top_products(df)
        st.dataframe(top_10, height=400, use_container_width=True, hide_index=True)
        
        # Chart
        fig = px.bar(top_10, x='Total Sales', y='Main Product', orientation='h',
                     title="Top 10 Products Revenue",
                     labels={'Total Sales': 'Revenue (₨)', 'Main Product': 'Product'},
                     color='Total Sales', color_continuous_scale='Viridis')
        fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Top 10 Narmin Unstitched")
        top_10_nu = get_top_products(df, "NARMIN UNSTITCHED")
        st.dataframe(top_10_nu, height=400, use_container_width=True, hide_index=True)
        
        # Chart
        fig = px.bar(top_10_nu, x='Total Sales', y='Main Product', orientation='h',
                     title="Top 10 Narmin Unstitched Revenue",
                     labels={'Total Sales': 'Revenue (₨)', 'Main Product': 'Product'},
                     color='Total Sales', color_continuous_scale='Plasma')
        fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Category breakdown
    col1, col2 = st.columns(2)
    
    categories = [
        ("NARMIN STITCHED", "Narmin Stitched"),
        ("COTTON", "Cotton"),
        ("BLENDED", "Blended"),
        ("WINTER", "Winter")
    ]
    
    for i, (cat_filter, cat_name) in enumerate(categories):
        with col1 if i % 2 == 0 else col2:
            st.subheader(f"🏷️ Top 10 {cat_name}")
            top_cat = get_top_products(df, cat_filter)
            st.dataframe(top_cat, height=350, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("📈 Sales Trends")
    
    # Daily sales trend
    daily_sales = df.groupby('Date')['Total Sales'].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_sales['Date'], 
        y=daily_sales['Total Sales'],
        mode='lines+markers',
        name='Daily Sales',
        line=dict(color='#667eea', width=3),
        fill='tonexty'
    ))
    
    fig.update_layout(
        title="Daily Sales Trend",
        xaxis_title="Date",
        yaxis_title="Sales (₨)",
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Branch comparison
    col1, col2 = st.columns(2)
    
    with col1:
        branch_sales = df.groupby('Branch')['Total Sales'].sum().reset_index()
        fig = px.pie(branch_sales, values='Total Sales', names='Branch',
                     title='Sales Distribution by Branch',
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        category_sales = df.groupby('Category')['Total Sales'].sum().reset_index().head(10)
        fig = px.pie(category_sales, values='Total Sales', names='Category',
                     title='Sales Distribution by Top Categories',
                     color_discrete_sequence=px.colors.sequential.Viridis)
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data refreshes every 5 minutes when auto-refresh is enabled")
