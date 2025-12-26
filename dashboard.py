import streamlit as st
import pandas as pd
from main import fetch_api_data, latest_data
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Sales Dashboard", 
    layout="wide", 
    initial_sidebar_state='collapsed'
)

# ----------------------------------------------------
# MINIMAL CSS - NO HEAVY STYLES
# ----------------------------------------------------
st.markdown("""
<style>
/* Hide Streamlit branding */
[data-testid="stToolbar"], 
[data-testid="stDecoration"], 
header, 
footer {
    display: none !important;
}

/* Basic table styling */
div[data-testid="stDataFrame"] th {
    background-color: #2c3e50 !important;
    color: white !important;
}

/* KPI cards */
[data-testid="stMetric"] {
    background-color: #34495e;
    padding: 1rem;
    border-radius: 0.3rem;
    border-left: 4px solid #3498db;
}

[data-testid="stMetricLabel"] {
    color: #ecf0f1 !important;
}

[data-testid="stMetricValue"] {
    color: white !important;
}

/* Button */
.stButton button {
    background-color: #3498db;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# SHOW LOADING MESSAGE IMMEDIATELY
# ----------------------------------------------------
loading_placeholder = st.empty()
loading_placeholder.info("🔄 Loading sales data, please wait...")

# ----------------------------------------------------
# SIMPLE DATA LOADING - NO COMPLEX CACHING
# ----------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def load_data():
    """Load data with simple caching"""
    report_type = "ProductDateWiseSale"
    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
        df["Main Product"] = df["Product Name"].astype(str).str.split("|").str[0].str.strip()
        return df
    return pd.DataFrame()

# Fetch data
try:
    # Track current date to detect day change
    current_date = datetime.now().date()
    
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
        st.session_state.last_date = current_date
    
    # Auto-refresh if date has changed (new day)
    if st.session_state.last_date != current_date:
        fetch_api_data("ProductDateWiseSale")
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now()
        st.session_state.last_date = current_date
        st.rerun()
    
    fetch_api_data("ProductDateWiseSale")
    df = load_data()
    loading_placeholder.empty()  # Remove loading message
except Exception as e:
    loading_placeholder.error(f"Error loading data: {str(e)}")
    st.stop()

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
col1, col2 = st.columns([5, 1])
with col1:
    st.title("Narkins / Narmin Sales Dashboard")
    # Show current date
    st.caption(f"📅 Current Date: {datetime.now().strftime('%A, %B %d, %Y')}")
with col2:
    if st.button("Refresh", use_container_width=True, key="refresh_btn", type="primary"):
        # Clear cache and session state
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now()
        st.session_state.last_date = datetime.now().date()
        # Force fetch new data
        fetch_api_data("ProductDateWiseSale")
        st.rerun()

if df.empty:
    st.error("No data available. Please check your data source.")
    st.stop()

# ----------------------------------------------------
# CALCULATE DATA ONCE - BUT UPDATE TODAY DYNAMICALLY
# ----------------------------------------------------
# Get current date - this will update on each page load/refresh
today = pd.Timestamp.now().normalize()

# Filter dataframes
today_df = df[df['Date'] == today]
month_df = df[df['Date'].dt.month == today.month]

# ----------------------------------------------------
# KPI METRICS
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Today's Sales", f"Rs {today_df['Total Sales'].sum():,.0f}")
col2.metric("Today's Units", f"{today_df['SOLD QTY'].sum():,}")
col3.metric("Monthly Sales", f"Rs {month_df['Total Sales'].sum():,.0f}")
col4.metric("Total Units", f"{df['SOLD QTY'].sum():,}")

st.divider()

# ----------------------------------------------------
# TABS
# ----------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Top Products", "Categories", "Outlet Wise", "Trends"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("Today's Sale by Branch")
        today_branch = today_df.groupby('Branch')[['SOLD QTY', 'Total Sales']].sum().sort_values('Total Sales', ascending=False).reset_index()
        st.dataframe(today_branch, height=380, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Today's Category Sale")
        today_category = today_df.groupby('Category')[['SOLD QTY', 'Total Sales']].sum().sort_values('Total Sales', ascending=False).reset_index()
        st.dataframe(today_category, height=380, use_container_width=True, hide_index=True)
    
    with col3:
        st.subheader("Monthly Sale by Branch")
        month_branch = month_df.groupby('Branch')[['SOLD QTY', 'Total Sales']].sum().sort_values('Total Sales', ascending=False).reset_index()
        total_branch = month_branch["Total Sales"].sum()
        if total_branch > 0:
            month_branch["Contribution %"] = (month_branch["Total Sales"] / total_branch * 100).round(2)
        
        st.dataframe(
            month_branch,
            height=380,
            hide_index=True,
            column_config={
                "Branch": "Branch",
                "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Sales", format="Rs %d"),
                "Contribution %": st.column_config.ProgressColumn("Share %", format="%.1f", min_value=0, max_value=100),
            },
            use_container_width=True
        )
    
    with col4:
        st.subheader("Monthly Category Sale")
        month_category = month_df.groupby('Category')[['SOLD QTY', 'Total Sales']].sum().sort_values('Total Sales', ascending=False).reset_index()
        total_cat = month_category["Total Sales"].sum()
        if total_cat > 0:
            month_category["Contribution %"] = (month_category["Total Sales"] / total_cat * 100).round(2)
        
        st.dataframe(
            month_category,
            height=380,
            hide_index=True,
            column_config={
                "Category": "Category",
                "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Sales", format="Rs %d"),
                "Contribution %": st.column_config.ProgressColumn("Share %", format="%.1f", min_value=0, max_value=100),
            },
            use_container_width=True
        )
    
    st.subheader("Today's All Products")
    today_products = today_df.groupby("Main Product")[["SOLD QTY", "Total Sales"]].sum().sort_values("Total Sales", ascending=False).reset_index()
    st.dataframe(
        today_products,
        height=400,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Main Product": st.column_config.TextColumn("Product", width="large"),
            "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
            "Total Sales": st.column_config.NumberColumn("Sales", format="Rs %d"),
        }
    )

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Products (Overall)")
        top_10 = df.groupby("Main Product")[["SOLD QTY", "Total Sales"]].sum().sort_values("Total Sales", ascending=False).head(10).reset_index()
        st.dataframe(top_10, height=380, use_container_width=True, hide_index=True)
        
        fig = px.bar(top_10, x='Total Sales', y='Main Product', orientation='h', color_discrete_sequence=['#3498db'])
        fig.update_layout(height=380, yaxis={'categoryorder':'total ascending'}, showlegend=False, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top 10 Narmin Unstitched")
        narmin_un = df[df['Category'].str.contains("NARMIN UNSTITCHED", case=False, na=False)].copy()
        narmin_un["Product"] = narmin_un["Product Name"].str.split("|").str[0].str.strip()
        top_nu = narmin_un.groupby("Product")[["SOLD QTY", "Total Sales"]].sum().sort_values("Total Sales", ascending=False).head(10).reset_index()
        st.dataframe(top_nu, height=380, use_container_width=True, hide_index=True)
        
        fig = px.bar(top_nu, x='Total Sales', y='Product', orientation='h', color_discrete_sequence=['#e74c3c'])
        fig.update_layout(height=380, yaxis={'categoryorder':'total ascending'}, showlegend=False, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Narmin Stitched")
        narmin_st = df[df['Category'].str.contains("NARMIN STITCHED", case=False, na=False)].copy()
        narmin_st["Product"] = narmin_st["Product Name"].str.split("|").str[0].str.strip()
        top_ns = narmin_st.groupby("Product")[["SOLD QTY", "Total Sales"]].sum().sort_values("Total Sales", ascending=False).head(10).reset_index()
        st.dataframe(top_ns, height=380, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Top 10 Cotton")
        cotton = df[df['Category'].str.contains("COTTON", case=False, na=False)].copy()
        cotton["Product"] = cotton["Product Name"].str.split("|").str[0].str.strip()
        top_cotton = cotton.groupby("Product")[["SOLD QTY", "Total Sales"]].sum().sort_values("Total Sales", ascending=False).head(10).reset_index()
        st.dataframe(top_cotton, height=380, use_container_width=True, hide_index=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Top 10 Blended")
        blended = df[df['Category'].str.contains("BLENDED", case=False, na=False)].copy()
        blended["Product"] = blended["Product Name"].str.split("|").str[0].str.strip()
        top_blend = blended.groupby("Product")[["SOLD QTY", "Total Sales"]].sum().sort_values("Total Sales", ascending=False).head(10).reset_index()
        st.dataframe(top_blend, height=380, use_container_width=True, hide_index=True)
    
    with col4:
        st.subheader("Top 10 Winter")
        winter = df[df['Category'].str.contains("WINTER", case=False, na=False)].copy()
        winter["Product"] = winter["Product Name"].str.split("|").str[0].str.strip()
        top_winter = winter.groupby("Product")[["SOLD QTY", "Total Sales"]].sum().sort_values("Total Sales", ascending=False).head(10).reset_index()
        st.dataframe(top_winter, height=380, use_container_width=True, hide_index=True)

with tab4:
    # ----------------------------------------------------
    # OUTLET WISE ANALYSIS
    # ----------------------------------------------------
    st.subheader("Outlet Wise Analysis")
    
    # Get unique branches/outlets
    branches = sorted(df['Branch'].unique())
    
    selected_outlet = st.selectbox(
        "Select Outlet",
        options=["All Outlets"] + branches,
        key="outlet_select"
    )
    
    # Filter data based on outlet selection
    if selected_outlet != "All Outlets":
        outlet_df = df[df['Branch'] == selected_outlet]
        outlet_today = today_df[today_df['Branch'] == selected_outlet]
        outlet_month = month_df[month_df['Branch'] == selected_outlet]
    else:
        outlet_df = df
        outlet_today = today_df
        outlet_month = month_df
    
    st.divider()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Today's Sales", f"Rs {outlet_today['Total Sales'].sum():,.0f}")
    
    with col2:
        st.metric("Today's Units", f"{outlet_today['SOLD QTY'].sum():,}")
    
    with col3:
        st.metric("Monthly Sales", f"Rs {outlet_month['Total Sales'].sum():,.0f}")
    
    with col4:
        st.metric("Total Units", f"{outlet_df['SOLD QTY'].sum():,}")
    
    st.divider()
    
    # Detailed analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Categories")
        outlet_categories = (
            outlet_month.groupby('Category')[['SOLD QTY', 'Total Sales']]
            .sum().sort_values('Total Sales', ascending=False).head(10).reset_index()
        )
        st.dataframe(
            outlet_categories,
            height=380,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Category": "Category",
                "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Sales", format="Rs %d"),
            }
        )
    
    with col2:
        st.subheader("Top Products")
        outlet_products = (
            outlet_month.groupby('Main Product')[['SOLD QTY', 'Total Sales']]
            .sum().sort_values('Total Sales', ascending=False).head(10).reset_index()
        )
        st.dataframe(
            outlet_products,
            height=380,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Main Product": "Product",
                "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Sales", format="Rs %d"),
            }
        )
    
    # Daily trend for outlet
    st.subheader("Daily Sales Trend")
    outlet_daily = outlet_df.groupby('Date')['Total Sales'].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=outlet_daily['Date'],
        y=outlet_daily['Total Sales'],
        mode='lines+markers',
        line=dict(color='#e74c3c', width=2),
        fill='tozeroy',
        fillcolor='rgba(231, 76, 60, 0.2)'
    ))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Sales (Rs)",
        height=350,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Daily Sales Trend")
    daily_sales = df.groupby('Date')['Total Sales'].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_sales['Date'], 
        y=daily_sales['Total Sales'],
        mode='lines+markers',
        line=dict(color='#3498db', width=2),
        marker=dict(size=4),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.2)'
    ))
    fig.update_layout(xaxis_title="Date", yaxis_title="Sales (Rs)", height=380, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales by Branch")
        branch_sales = df.groupby('Branch')['Total Sales'].sum().reset_index()
        fig = px.pie(branch_sales, values='Total Sales', names='Branch', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=20, b=0))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Sales by Category")
        category_sales = df.groupby('Category')['Total Sales'].sum().reset_index().nlargest(8, 'Total Sales')
        fig = px.pie(category_sales, values='Total Sales', names='Category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=20, b=0))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

st.divider()
refresh_time = st.session_state.get('last_refresh', datetime.now())
st.caption(f"Last Updated: {refresh_time.strftime('%Y-%m-%d %I:%M %p')}")
