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
# MOBILE-RESPONSIVE & ENHANCED CSS
# ----------------------------------------------------
st.markdown("""
<style>
/* === MOBILE RESPONSIVE === */
@media (max-width: 768px) {
    .block-container {
        padding: 0.5rem !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
    }
    
    .stApp h1 {
        font-size: 1.5rem !important;
    }
    
    .stApp h3 {
        font-size: 1rem !important;
    }
    
    div[data-testid="stDataFrame"] {
        font-size: 0.75rem !important;
    }
}

/* === DATAFRAME STYLING === */
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
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8f 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 0.5rem !important;
    font-size: 0.9rem !important;
}

div[data-testid="stDataFrame"] td {
    padding: 0.5rem !important;
    font-size: 0.85rem !important;
}

div[data-testid="stDataFrame"] > div {
    height: 380px !important;
    overflow: auto !important;
}

/* === ENHANCED KPI CARDS === */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem 1rem;
    border-radius: 1rem;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    transition: all 0.3s ease;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

[data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

[data-testid="stMetricLabel"] {
    font-size: 0.95rem !important;
    color: rgba(255, 255, 255, 0.95) !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

[data-testid="stMetricValue"] {
    font-size: 2.5rem !important;
    color: white !important;
    font-weight: 700 !important;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

/* === SECTION HEADERS === */
.stApp h3 {
    color: #1e3a5f;
    border-bottom: 3px solid #667eea;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
    margin-top: 1.5rem;
    font-weight: 700;
    font-size: 1.2rem;
}

/* === TABS STYLING === */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: linear-gradient(90deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 0.5rem;
    border-radius: 0.75rem;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    border-radius: 0.5rem;
    color: #1e3a5f;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: rgba(102, 126, 234, 0.1);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
}

/* === REFRESH BUTTON === */
.stButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    border-radius: 0.5rem;
    transition: all 0.3s ease;
    box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
}

.stButton button:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.5);
}

/* === DIVIDER === */
hr {
    margin: 1.5rem 0;
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, #667eea, transparent);
}

/* === HIDE STREAMLIT BRANDING === */
[data-testid="stToolbar"], 
[data-testid="stDecoration"], 
header, 
footer,
.viewerBadge_container__r5tak {
    display: none !important;
}

/* === LOADING SPINNER === */
.stSpinner > div {
    border-top-color: #667eea !important;
}

/* === SCROLLBAR STYLING === */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #764ba2;
}

/* === TITLE STYLING === */
.stApp h1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800;
    text-align: center;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# OPTIMIZED CACHING
# ----------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def load_data():
    """Load and process data once"""
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
def calculate_metrics(df, today):
    """Calculate all metrics in one go"""
    today_df = df[df['Date'] == today]
    month_df = df[df['Date'].dt.month == today.month]
    
    # All aggregations
    metrics = {
        'today_sales': today_df['Total Sales'].sum(),
        'today_units': today_df['SOLD QTY'].sum(),
        'month_sales': month_df['Total Sales'].sum(),
        'total_units': df['SOLD QTY'].sum(),
        'today_by_branch': today_df.groupby('Branch')[['SOLD QTY', 'Total Sales']].sum().sort_values(by='Total Sales', ascending=False).reset_index(),
        'today_by_category': today_df.groupby('Category')[['SOLD QTY', 'Total Sales']].sum().sort_values(by='Total Sales', ascending=False).reset_index(),
        'month_by_branch': month_df.groupby('Branch')[['SOLD QTY', 'Total Sales']].sum().sort_values(by='Total Sales', ascending=False).reset_index(),
        'month_by_category': month_df.groupby('Category')[['SOLD QTY', 'Total Sales']].sum().sort_values(by='Total Sales', ascending=False).reset_index(),
        'today_all_products': today_df.groupby("Main Product")[["SOLD QTY", "Total Sales"]].sum().sort_values(by="Total Sales", ascending=False).reset_index(),
        'top_10_overall': df.groupby("Main Product")[["SOLD QTY", "Total Sales"]].sum().sort_values(by="Total Sales", ascending=False).head(10).reset_index()
    }
    
    # Contribution %
    total_branch = metrics['month_by_branch']["Total Sales"].sum()
    metrics['month_by_branch']["Contribution %"] = (metrics['month_by_branch']["Total Sales"] / total_branch * 100).round(2)
    
    total_cat = metrics['month_by_category']["Total Sales"].sum()
    metrics['month_by_category']["Contribution %"] = (metrics['month_by_category']["Total Sales"] / total_cat * 100).round(2)
    
    return metrics

@st.cache_data(ttl=600, show_spinner=False)
def get_category_top_10(df, category_name):
    """Get top 10 for specific category"""
    filtered = df[df['Category'].str.contains(category_name, case=False, na=False)]
    return (
        filtered.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
        .sum()
        .sort_values(by="Total Sales", ascending=False)
        .head(10)
        .reset_index()
    )

# ----------------------------------------------------
# LOAD DATA
# ----------------------------------------------------
if 'loaded' not in st.session_state:
    with st.spinner("🔄 Loading dashboard..."):
        fetch_api_data("ProductDateWiseSale")
        st.session_state.loaded = True

df = load_data()

if df is None or df.empty:
    st.error("⚠️ No data available")
    st.stop()

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
col1, col2 = st.columns([5, 1])
with col1:
    st.title("📊 Narkins / Narmin Sales Dashboard")
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        fetch_api_data("ProductDateWiseSale")
        st.rerun()

# ----------------------------------------------------
# KPI METRICS
# ----------------------------------------------------
today = pd.Timestamp.today().normalize()
metrics = calculate_metrics(df, today)

col1, col2, col3, col4 = st.columns(4, gap='medium')
col1.metric("💰 Today's Sales", f"₨ {metrics['today_sales']:,.0f}")
col2.metric("📦 Today's Units", f"{metrics['today_units']:,}")
col3.metric("📈 Monthly Sales", f"₨ {metrics['month_sales']:,.0f}")
col4.metric("🎯 Total Units", f"{metrics['total_units']:,}")

st.divider()

# ----------------------------------------------------
# TABS
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏆 Top Products", "📁 Categories", "📈 Trends"])

with tab1:
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
    
    st.subheader("📦 Today's All Products")
    st.dataframe(
        metrics['today_all_products'],
        height=400,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Main Product": st.column_config.TextColumn("Product", width="large"),
            "SOLD QTY": st.column_config.NumberColumn("Units", format="%d"),
            "Total Sales": st.column_config.NumberColumn("Sales", format="₨%d"),
        }
    )

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Products (Overall)")
        st.dataframe(metrics['top_10_overall'], height=400, use_container_width=True, hide_index=True)
        
        fig = px.bar(metrics['top_10_overall'], x='Total Sales', y='Main Product', orientation='h',
                     title="Revenue Distribution",
                     color='Total Sales', color_continuous_scale='Viridis')
        fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Top 10 Narmin Unstitched")
        top_nu = get_category_top_10(df, "NARMIN UNSTITCHED")
        st.dataframe(top_nu, height=400, use_container_width=True, hide_index=True)
        
        fig = px.bar(top_nu, x='Total Sales', y='Main Product', orientation='h',
                     title="Revenue Distribution",
                     color='Total Sales', color_continuous_scale='Plasma')
        fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    
    categories = [
        ("NARMIN STITCHED", "🧵 Narmin Stitched"),
        ("COTTON", "🌿 Cotton"),
        ("BLENDED", "🎨 Blended"),
        ("WINTER", "❄️ Winter")
    ]
    
    for i, (cat_filter, cat_name) in enumerate(categories):
        with col1 if i % 2 == 0 else col2:
            st.subheader(cat_name)
            top_cat = get_category_top_10(df, cat_filter)
            st.dataframe(top_cat, height=380, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("📈 Daily Sales Trend")
    daily_sales = df.groupby('Date')['Total Sales'].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_sales['Date'], 
        y=daily_sales['Total Sales'],
        mode='lines+markers',
        name='Daily Sales',
        line=dict(color='#667eea', width=3),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.3)'
    ))
    
    fig.update_layout(
        title="",
        xaxis_title="Date",
        yaxis_title="Sales (₨)",
        hovermode='x unified',
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏪 Sales by Branch")
        branch_sales = df.groupby('Branch')['Total Sales'].sum().reset_index()
        fig = px.pie(branch_sales, values='Total Sales', names='Branch',
                     hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(height=400, showlegend=True)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📁 Sales by Category")
        category_sales = df.groupby('Category')['Total Sales'].sum().reset_index().nlargest(8, 'Total Sales')
        fig = px.pie(category_sales, values='Total Sales', names='Category',
                     hole=0.4, color_discrete_sequence=px.colors.sequential.Viridis)
        fig.update_layout(height=400, showlegend=True)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.divider()
st.caption(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')} | 📱 Optimized for Mobile & Desktop")
