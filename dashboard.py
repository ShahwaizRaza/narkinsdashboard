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
# CLEAN & SIMPLE CSS
# ----------------------------------------------------
st.markdown("""
<style>
@media (max-width: 768px) {
    .block-container { padding: 0.5rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
    .stApp h1 { font-size: 1.3rem !important; }
    .stApp h3 { font-size: 0.9rem !important; }
}

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
    background-color: #2c3e50 !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.6rem 0.4rem !important;
    font-size: 0.85rem !important;
}

div[data-testid="stDataFrame"] td {
    padding: 0.4rem !important;
    font-size: 0.8rem !important;
}

div[data-testid="stDataFrame"] > div {
    height: 380px !important;
    overflow: auto !important;
}

[data-testid="stMetric"] {
    background-color: #34495e;
    padding: 1.2rem 0.8rem;
    border-radius: 0.4rem;
    border-left: 4px solid #3498db;
}

[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    color: #ecf0f1 !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    color: white !important;
    font-weight: 600 !important;
}

.stApp h1 {
    color: #2c3e50;
    font-weight: 700;
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #3498db;
}

.stApp h3 {
    color: #2c3e50;
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.8rem;
    margin-top: 1rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.3rem;
    background-color: #ecf0f1;
    padding: 0.3rem;
    border-radius: 0.3rem;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    border-radius: 0.3rem;
    color: #2c3e50;
    background-color: transparent;
}

.stTabs [aria-selected="true"] {
    background-color: #3498db !important;
    color: white !important;
}

.stButton button {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
    border-radius: 0.3rem;
}

.stButton button:hover {
    background-color: #2980b9;
}

hr {
    margin: 1.2rem 0;
    border: none;
    height: 1px;
    background-color: #bdc3c7;
}

[data-testid="stToolbar"], 
[data-testid="stDecoration"], 
header, 
footer {
    display: none !important;
}

::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: #ecf0f1;
}

::-webkit-scrollbar-thumb {
    background: #95a5a6;
    border-radius: 3px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# OPTIMIZED CACHING - Cache everything separately
# ----------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def load_data():
    """Load and prepare base data"""
    report_type = "ProductDateWiseSale"
    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Date'] = df['Date'].dt.normalize()
        df["Main Product"] = df["Product Name"].astype(str).str.split("|").str[0].str.strip()
        return df
    return pd.DataFrame()

@st.cache_data(ttl=600, show_spinner=False)
def get_kpi_metrics(_df, today):
    """Cache KPI calculations"""
    today_df = _df[_df['Date'] == today]
    month_df = _df[_df['Date'].dt.month == today.month]
    
    return {
        'today_sales': today_df['Total Sales'].sum(),
        'today_units': today_df['SOLD QTY'].sum(),
        'month_sales': month_df['Total Sales'].sum(),
        'total_units': _df['SOLD QTY'].sum()
    }

@st.cache_data(ttl=600, show_spinner=False)
def get_today_summary(_df, today):
    """Cache today's summary tables"""
    today_df = _df[_df['Date'] == today]
    
    return {
        'by_branch': today_df.groupby('Branch')[['SOLD QTY', 'Total Sales']].sum().sort_values('Total Sales', ascending=False).reset_index(),
        'by_category': today_df.groupby('Category')[['SOLD QTY', 'Total Sales']].sum().sort_values('Total Sales', ascending=False).reset_index(),
        'all_products': today_df.groupby('Main Product')[['SOLD QTY', 'Total Sales']].sum().sort_values('Total Sales', ascending=False).reset_index()
    }

@st.cache_data(ttl=600, show_spinner=False)
def get_month_summary(_df, today):
    """Cache monthly summary tables"""
    month_df = _df[_df['Date'].dt.month == today.month]
    
    month_branch = month_df.groupby('Branch')[['SOLD QTY', 'Total Sales']].sum().sort_values('Total Sales', ascending=False).reset_index()
    total_branch = month_branch["Total Sales"].sum()
    if total_branch > 0:
        month_branch["Contribution %"] = (month_branch["Total Sales"] / total_branch * 100).round(2)
    
    month_category = month_df.groupby('Category')[['SOLD QTY', 'Total Sales']].sum().sort_values('Total Sales', ascending=False).reset_index()
    total_cat = month_category["Total Sales"].sum()
    if total_cat > 0:
        month_category["Contribution %"] = (month_category["Total Sales"] / total_cat * 100).round(2)
    
    return {
        'by_branch': month_branch,
        'by_category': month_category
    }

@st.cache_data(ttl=600, show_spinner=False)
def get_top_products(_df):
    """Cache top products calculation"""
    return _df.groupby("Main Product")[["SOLD QTY", "Total Sales"]].sum().sort_values("Total Sales", ascending=False).head(10).reset_index()

@st.cache_data(ttl=600, show_spinner=False)
def get_category_top(_df, category):
    """Cache category top 10"""
    filtered = _df[_df['Category'].str.contains(category, case=False, na=False)].copy()
    filtered["Product"] = filtered["Product Name"].str.split("|").str[0].str.strip()
    return filtered.groupby("Product")[["SOLD QTY", "Total Sales"]].sum().sort_values("Total Sales", ascending=False).head(10).reset_index()

@st.cache_data(ttl=600, show_spinner=False)
def get_trend_data(_df):
    """Cache trend calculations"""
    return {
        'daily': _df.groupby('Date')['Total Sales'].sum().reset_index(),
        'branch': _df.groupby('Branch')['Total Sales'].sum().reset_index(),
        'category': _df.groupby('Category')['Total Sales'].sum().reset_index().nlargest(8, 'Total Sales')
    }

# ----------------------------------------------------
# INITIALIZE - Fetch data only once
# ----------------------------------------------------
if 'data_fetched' not in st.session_state:
    fetch_api_data("ProductDateWiseSale")
    st.session_state.data_fetched = True

df = load_data()

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
col1, col2 = st.columns([5, 1])
with col1:
    st.title("Narkins / Narmin Sales Dashboard")
with col2:
    if st.button("Refresh", use_container_width=True):
        fetch_api_data("ProductDateWiseSale")
        st.cache_data.clear()
        st.session_state.data_fetched = False
        st.rerun()

if df.empty:
    st.error("No data available. Please check your data source.")
    st.stop()

# ----------------------------------------------------
# KPI METRICS - Load instantly
# ----------------------------------------------------
today = pd.Timestamp.today().normalize()
kpis = get_kpi_metrics(df, today)

col1, col2, col3, col4 = st.columns(4, gap='medium')
col1.metric("Today's Sales", f"Rs {kpis['today_sales']:,.0f}")
col2.metric("Today's Units", f"{kpis['today_units']:,}")
col3.metric("Monthly Sales", f"Rs {kpis['month_sales']:,.0f}")
col4.metric("Total Units", f"{kpis['total_units']:,}")

st.divider()

# ----------------------------------------------------
# TABS - Progressive loading
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Top Products", "Categories", "Trends"])

with tab1:
    # Use cached data
    today_data = get_today_summary(df, today)
    month_data = get_month_summary(df, today)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("Today's Sale by Branch")
        st.dataframe(today_data['by_branch'], height=380, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Today's Category Sale")
        st.dataframe(today_data['by_category'], height=380, use_container_width=True, hide_index=True)
    
    with col3:
        st.subheader("Monthly Sale by Branch")
        st.dataframe(
            month_data['by_branch'],
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
        st.dataframe(
            month_data['by_category'],
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
    st.dataframe(
        today_data['all_products'],
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
        top_10 = get_top_products(df)
        st.dataframe(top_10, height=380, use_container_width=True, hide_index=True)
        
        fig = px.bar(top_10, x='Total Sales', y='Main Product', orientation='h', color_discrete_sequence=['#3498db'])
        fig.update_layout(height=380, yaxis={'categoryorder':'total ascending'}, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top 10 Narmin Unstitched")
        top_nu = get_category_top(df, "NARMIN UNSTITCHED")
        st.dataframe(top_nu, height=380, use_container_width=True, hide_index=True)
        
        fig = px.bar(top_nu, x='Total Sales', y='Product', orientation='h', color_discrete_sequence=['#e74c3c'])
        fig.update_layout(height=380, yaxis={'categoryorder':'total ascending'}, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Narmin Stitched")
        st.dataframe(get_category_top(df, "NARMIN STITCHED"), height=380, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Top 10 Cotton")
        st.dataframe(get_category_top(df, "COTTON"), height=380, use_container_width=True, hide_index=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Top 10 Blended")
        st.dataframe(get_category_top(df, "BLENDED"), height=380, use_container_width=True, hide_index=True)
    
    with col4:
        st.subheader("Top 10 Winter")
        st.dataframe(get_category_top(df, "WINTER"), height=380, use_container_width=True, hide_index=True)

with tab4:
    trend_data = get_trend_data(df)
    
    st.subheader("Daily Sales Trend")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_data['daily']['Date'], 
        y=trend_data['daily']['Total Sales'],
        mode='lines+markers',
        line=dict(color='#3498db', width=2),
        marker=dict(size=5),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.2)'
    ))
    fig.update_layout(xaxis_title="Date", yaxis_title="Sales (Rs)", height=380, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales by Branch")
        fig = px.pie(trend_data['branch'], values='Total Sales', names='Branch', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=30, b=0))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Sales by Category")
        fig = px.pie(trend_data['category'], values='Total Sales', names='Category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=30, b=0))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')} | Data cached for 10 minutes")
