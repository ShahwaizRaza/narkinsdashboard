import streamlit as st
import pandas as pd
from main import fetch_api_data, latest_data
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config - Mobile responsive
st.set_page_config(
    page_title="Sales Dashboard", 
    layout="wide", 
    initial_sidebar_state='auto'
)

# ----------------------------------------------------
# MOBILE-RESPONSIVE CSS
# ----------------------------------------------------
st.markdown("""
<style>
/* Mobile-first responsive design */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }
    
    .stApp h3 {
        font-size: 1.2rem !important;
    }
}

/* Optimized dataframe styling */
div[data-testid="stDataFrame"] {
    height: auto !important;
    max-height: 400px !important;
}

div[data-testid="stDataFrame"] table {
    table-layout: auto !important;
}

div[data-testid="stDataFrame"] th {
    position: sticky !important;
    top: 0;
    z-index: 3 !important;
    background-color: #1e3a5f !important;
    color: white !important;
    font-size: 0.9rem;
    padding: 0.5rem !important;
}

div[data-testid="stDataFrame"] td {
    font-size: 0.85rem;
    padding: 0.4rem !important;
}

/* Compact KPI boxes */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 0.75rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

[data-testid="stMetricLabel"] {
    font-size: 0.9rem !important;
    color: rgba(255, 255, 255, 0.95) !important;
    font-weight: 600 !important;
}

[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    color: white !important;
    font-weight: 700 !important;
}

/* Compact headers */
.stApp h3 {
    color: #1e3a5f;
    font-size: 1.1rem;
    border-bottom: 2px solid #667eea;
    padding-bottom: 0.3rem;
    margin-bottom: 0.5rem;
    margin-top: 0.5rem;
}

/* Hide Streamlit branding */
[data-testid="stToolbar"], [data-testid="stDecoration"], 
header, footer, .viewerBadge_container__r5tak {
    display: none !important;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.5rem 1rem;
    font-weight: 600;
}

/* Spinner */
.stSpinner > div {
    border-top-color: #667eea !important;
}

/* Compact spacing */
.element-container {
    margin-bottom: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# ULTRA-FAST CACHING
# ----------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)  # 10 min cache
def load_and_process_data():
    """Single function to load and pre-process all data"""
    report_type = "ProductDateWiseSale"
    if report_type not in latest_data or not isinstance(latest_data[report_type], list):
        return None
    
    df = pd.DataFrame(latest_data[report_type])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Date'] = df['Date'].dt.normalize()
    df["Main Product"] = df["Product Name"].astype(str).str.split("|").str[0].str.strip()
    
    return df

@st.cache_data(ttl=600, show_spinner=False)
def get_summary_metrics(df, today):
    """Get only essential metrics for dashboard header"""
    today_df = df[df['Date'] == today]
    month_df = df[df['Date'].dt.month == today.month]
    
    return {
        'today_sales': today_df['Total Sales'].sum(),
        'today_units': today_df['SOLD QTY'].sum(),
        'month_sales': month_df['Total Sales'].sum(),
        'total_units': df['SOLD QTY'].sum()
    }

@st.cache_data(ttl=600, show_spinner=False)
def get_aggregated_data(df, today, group_by, date_filter='today'):
    """Generic aggregation function"""
    if date_filter == 'today':
        df_filtered = df[df['Date'] == today]
    elif date_filter == 'month':
        df_filtered = df[df['Date'].dt.month == today.month]
    else:
        df_filtered = df
    
    result = (
        df_filtered.groupby(group_by)[['SOLD QTY', 'Total Sales']]
        .sum()
        .sort_values(by='Total Sales', ascending=False)
        .reset_index()
    )
    
    # Add contribution % for monthly data
    if date_filter == 'month':
        total = result['Total Sales'].sum()
        result['Contribution %'] = (result['Total Sales'] / total * 100).round(1)
    
    return result

@st.cache_data(ttl=600, show_spinner=False)
def get_top_n(df, group_by='Main Product', n=10, category_filter=None):
    """Get top N products with optional category filter"""
    if category_filter:
        df = df[df['Category'].str.contains(category_filter, case=False, na=False)]
    
    return (
        df.groupby(group_by)[['SOLD QTY', 'Total Sales']]
        .sum()
        .sort_values(by='Total Sales', ascending=False)
        .head(n)
        .reset_index()
    )

# ----------------------------------------------------
# LOAD DATA (Single API call)
# ----------------------------------------------------
if 'data_loaded' not in st.session_state:
    with st.spinner("🔄 Loading data..."):
        fetch_api_data("ProductDateWiseSale")
        st.session_state.data_loaded = True

df = load_and_process_data()

if df is None or df.empty:
    st.error("⚠️ No data available")
    st.stop()

# ----------------------------------------------------
# HEADER & CONTROLS
# ----------------------------------------------------
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📊 Sales Dashboard")
with col2:
    if st.button("🔄", help="Refresh data", use_container_width=True):
        st.cache_data.clear()
        fetch_api_data("ProductDateWiseSale")
        st.rerun()

today = pd.Timestamp.today().normalize()

# Quick date filter (mobile-friendly)
with st.expander("⚙️ Filters", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        view_option = st.selectbox(
            "View",
            ["Today", "This Week", "This Month", "All Time"],
            index=0
        )
    with col2:
        branches = st.multiselect(
            "Branches",
            options=df['Branch'].unique(),
            default=None,
            placeholder="All branches"
        )
    
    # Apply filters
    if view_option == "Today":
        df_filtered = df[df['Date'] == today]
    elif view_option == "This Week":
        week_start = today - timedelta(days=today.weekday())
        df_filtered = df[df['Date'] >= week_start]
    elif view_option == "This Month":
        df_filtered = df[df['Date'].dt.month == today.month]
    else:
        df_filtered = df
    
    if branches:
        df_filtered = df_filtered[df_filtered['Branch'].isin(branches)]

# Use filtered data for all calculations
df = df_filtered

# ----------------------------------------------------
# KPI CARDS (Always visible)
# ----------------------------------------------------
metrics = get_summary_metrics(df, today)

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Today", f"₨{metrics['today_sales']/1000:.0f}K")
col2.metric("📦 Units", f"{metrics['today_units']:,}")
col3.metric("📈 Month", f"₨{metrics['month_sales']/1000:.0f}K")
col4.metric("🎯 Total", f"{metrics['total_units']:,}")

st.divider()

# ----------------------------------------------------
# TABS (Lazy loading - only load active tab)
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏆 Top Products", "📁 Categories", "📈 Analytics"])

with tab1:
    # Today's summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Today - Branch")
        data = get_aggregated_data(df, today, 'Branch', 'today')
        st.dataframe(
            data.head(10),
            height=300,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Branch": "Branch",
                "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Sales", format="₨%.0f")
            }
        )
    
    with col2:
        st.subheader("Today - Category")
        data = get_aggregated_data(df, today, 'Category', 'today')
        st.dataframe(
            data.head(10),
            height=300,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Category": "Category",
                "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
                "Total Sales": st.column_config.NumberColumn("Sales", format="₨%.0f")
            }
        )
    
    st.subheader("Monthly - Branch Performance")
    monthly_branch = get_aggregated_data(df, today, 'Branch', 'month')
    st.dataframe(
        monthly_branch,
        height=300,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Branch": "Branch",
            "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
            "Total Sales": st.column_config.NumberColumn("Sales", format="₨%.0f"),
            "Contribution %": st.column_config.ProgressColumn(
                "Share", format="%.1f%%", min_value=0, max_value=100
            )
        }
    )
    
    # Today's products (compact view)
    with st.expander("📦 Today's Products (Click to expand)", expanded=False):
        today_products = get_aggregated_data(df, today, 'Main Product', 'today')
        st.dataframe(
            today_products,
            height=400,
            hide_index=True,
            use_container_width=True
        )

with tab2:
    # Top performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Overall")
        top_10 = get_top_n(df, n=10)
        st.dataframe(top_10, height=350, hide_index=True, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Narmin Unstitched")
        top_nu = get_top_n(df, n=10, category_filter="NARMIN UNSTITCHED")
        st.dataframe(top_nu, height=350, hide_index=True, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("👗 Narmin Stitched")
        top_ns = get_top_n(df, n=10, category_filter="NARMIN STITCHED")
        st.dataframe(top_ns, height=350, hide_index=True, use_container_width=True)
    
    with col4:
        st.subheader("🧵 Cotton")
        top_cotton = get_top_n(df, n=10, category_filter="COTTON")
        st.dataframe(top_cotton, height=350, hide_index=True, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎨 Blended")
        top_blend = get_top_n(df, n=10, category_filter="BLENDED")
        st.dataframe(top_blend, height=350, hide_index=True, use_container_width=True)
    
    with col2:
        st.subheader("❄️ Winter")
        top_winter = get_top_n(df, n=10, category_filter="WINTER")
        st.dataframe(top_winter, height=350, hide_index=True, use_container_width=True)
    
    # Category distribution
    st.subheader("Category Distribution")
    cat_sales = df.groupby('Category')['Total Sales'].sum().reset_index().nlargest(8, 'Total Sales')
    fig = px.bar(cat_sales, x='Category', y='Total Sales', 
                 color='Total Sales', color_continuous_scale='Viridis')
    fig.update_layout(height=350, showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    # Lightweight analytics
    st.subheader("📈 Daily Trend")
    daily = df.groupby('Date')['Total Sales'].sum().reset_index()
    fig = px.line(daily, x='Date', y='Total Sales', 
                  markers=True, line_shape='spline')
    fig.update_layout(height=300, showlegend=False)
    fig.update_traces(line_color='#667eea', line_width=3)
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Branch Split")
        branch_total = df.groupby('Branch')['Total Sales'].sum().reset_index()
        fig = px.pie(branch_total, values='Total Sales', names='Branch', 
                     hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(height=350, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Categories")
        cat_total = df.groupby('Category')['Total Sales'].sum().reset_index().nlargest(6, 'Total Sales')
        fig = px.pie(cat_total, values='Total Sales', names='Category',
                     hole=0.4, color_discrete_sequence=px.colors.sequential.Plasma)
        fig.update_layout(height=350, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.divider()
st.caption(f"🕐 Updated: {datetime.now().strftime('%I:%M %p')} | 📱 Mobile optimized | 🔄 Data cached for 10min")
