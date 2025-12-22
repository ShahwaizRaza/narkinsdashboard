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
/* === MOBILE RESPONSIVE === */
@media (max-width: 768px) {
    .block-container {
        padding: 0.5rem !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
    }
    
    .stApp h1 {
        font-size: 1.3rem !important;
    }
    
    .stApp h3 {
        font-size: 0.9rem !important;
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

/* === CLEAN KPI CARDS === */
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

/* === SIMPLE HEADERS === */
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

/* === CLEAN TABS === */
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

/* === SIMPLE BUTTON === */
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

/* === CLEAN DIVIDER === */
hr {
    margin: 1.2rem 0;
    border: none;
    height: 1px;
    background-color: #bdc3c7;
}

/* === HIDE STREAMLIT BRANDING === */
[data-testid="stToolbar"], 
[data-testid="stDecoration"], 
header, 
footer {
    display: none !important;
}

/* === SIMPLE SCROLLBAR === */
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

::-webkit-scrollbar-thumb:hover {
    background: #7f8c8d;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# FAST DATA LOADING
# ----------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def load_base_data():
    """Load raw data only"""
    report_type = "ProductDateWiseSale"
    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Date'] = df['Date'].dt.normalize()
        df["Main Product"] = df["Product Name"].astype(str).str.split("|").str[0].str.strip()
        return df
    return pd.DataFrame()

# ----------------------------------------------------
# LOAD DATA IMMEDIATELY
# ----------------------------------------------------
fetch_api_data("ProductDateWiseSale")
df = load_base_data()

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
        st.rerun()

# ----------------------------------------------------
# CHECK DATA
# ----------------------------------------------------
if df.empty:
    st.error("No data available. Please check your data source.")
    st.stop()

# ----------------------------------------------------
# CHUNK 1: KPI METRICS (LOAD FIRST)
# ----------------------------------------------------
today = pd.Timestamp.today().normalize()
today_df = df[df['Date'] == today]
month_df = df[df['Date'].dt.month == today.month]

col1, col2, col3, col4 = st.columns(4, gap='medium')
col1.metric("Today's Sales", f"Rs {today_df['Total Sales'].sum():,.0f}")
col2.metric("Today's Units", f"{today_df['SOLD QTY'].sum():,}")
col3.metric("Monthly Sales", f"Rs {month_df['Total Sales'].sum():,.0f}")
col4.metric("Total Units", f"{df['SOLD QTY'].sum():,}")

st.divider()

# ----------------------------------------------------
# TABS FOR PROGRESSIVE LOADING
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Top Products", "Categories", "Trends"])

with tab1:
    # CHUNK 2: Today's data (fast)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("Today's Sale by Branch")
        today_branch = (
            today_df.groupby('Branch')[['SOLD QTY', 'Total Sales']]
            .sum().sort_values(by='Total Sales', ascending=False).reset_index()
        )
        st.dataframe(today_branch, height=380, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Today's Category Sale")
        today_category = (
            today_df.groupby('Category')[['SOLD QTY', 'Total Sales']]
            .sum().sort_values(by='Total Sales', ascending=False).reset_index()
        )
        st.dataframe(today_category, height=380, use_container_width=True, hide_index=True)
    
    with col3:
        st.subheader("Monthly Sale by Branch")
        month_branch = (
            month_df.groupby('Branch')[['SOLD QTY', 'Total Sales']]
            .sum().sort_values(by='Total Sales', ascending=False).reset_index()
        )
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
                "Contribution %": st.column_config.ProgressColumn(
                    "Share %", format="%.1f", min_value=0, max_value=100
                ),
            },
            use_container_width=True
        )
    
    with col4:
        st.subheader("Monthly Category Sale")
        month_category = (
            month_df.groupby('Category')[['SOLD QTY', 'Total Sales']]
            .sum().sort_values(by='Total Sales', ascending=False).reset_index()
        )
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
                "Contribution %": st.column_config.ProgressColumn(
                    "Share %", format="%.1f", min_value=0, max_value=100
                ),
            },
            use_container_width=True
        )
    
    # CHUNK 3: Today's products
    st.subheader("Today's All Products")
    today_products = (
        today_df.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
        .sum().sort_values(by="Total Sales", ascending=False).reset_index()
    )
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
    # CHUNK 4: Top products (only loads when tab is clicked)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Products (Overall)")
        top_10 = (
            df.groupby("Main Product")[["SOLD QTY", "Total Sales"]]
            .sum().sort_values(by="Total Sales", ascending=False).head(10).reset_index()
        )
        st.dataframe(top_10, height=380, use_container_width=True, hide_index=True)
        
        fig = px.bar(
            top_10, 
            x='Total Sales', 
            y='Main Product', 
            orientation='h',
            color_discrete_sequence=['#3498db']
        )
        fig.update_layout(
            height=380, 
            yaxis={'categoryorder':'total ascending'},
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top 10 Narmin Unstitched")
        narmin_un = df[df['Category'].str.contains("NARMIN UNSTITCHED", case=False, na=False)].copy()
        narmin_un["Product"] = narmin_un["Product Name"].str.split("|").str[0].str.strip()
        top_nu = (
            narmin_un.groupby("Product")[["SOLD QTY", "Total Sales"]]
            .sum().sort_values(by="Total Sales", ascending=False).head(10).reset_index()
        )
        st.dataframe(top_nu, height=380, use_container_width=True, hide_index=True)
        
        fig = px.bar(
            top_nu, 
            x='Total Sales', 
            y='Product', 
            orientation='h',
            color_discrete_sequence=['#e74c3c']
        )
        fig.update_layout(
            height=380, 
            yaxis={'categoryorder':'total ascending'},
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    # CHUNK 5: Categories (only loads when tab is clicked)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Narmin Stitched")
        narmin_st = df[df['Category'].str.contains("NARMIN STITCHED", case=False, na=False)].copy()
        narmin_st["Product"] = narmin_st["Product Name"].str.split("|").str[0].str.strip()
        top_ns = (
            narmin_st.groupby("Product")[["SOLD QTY", "Total Sales"]]
            .sum().sort_values(by="Total Sales", ascending=False).head(10).reset_index()
        )
        st.dataframe(top_ns, height=380, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Top 10 Cotton")
        cotton = df[df['Category'].str.contains("COTTON", case=False, na=False)].copy()
        cotton["Product"] = cotton["Product Name"].str.split("|").str[0].str.strip()
        top_cotton = (
            cotton.groupby("Product")[["SOLD QTY", "Total Sales"]]
            .sum().sort_values(by="Total Sales", ascending=False).head(10).reset_index()
        )
        st.dataframe(top_cotton, height=380, use_container_width=True, hide_index=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Top 10 Blended")
        blended = df[df['Category'].str.contains("BLENDED", case=False, na=False)].copy()
        blended["Product"] = blended["Product Name"].str.split("|").str[0].str.strip()
        top_blend = (
            blended.groupby("Product")[["SOLD QTY", "Total Sales"]]
            .sum().sort_values(by="Total Sales", ascending=False).head(10).reset_index()
        )
        st.dataframe(top_blend, height=380, use_container_width=True, hide_index=True)
    
    with col4:
        st.subheader("Top 10 Winter")
        winter = df[df['Category'].str.contains("WINTER", case=False, na=False)].copy()
        winter["Product"] = winter["Product Name"].str.split("|").str[0].str.strip()
        top_winter = (
            winter.groupby("Product")[["SOLD QTY", "Total Sales"]]
            .sum().sort_values(by="Total Sales", ascending=False).head(10).reset_index()
        )
        st.dataframe(top_winter, height=380, use_container_width=True, hide_index=True)

with tab4:
    # CHUNK 6: Trends (only loads when tab is clicked)
    st.subheader("Daily Sales Trend")
    daily_sales = df.groupby('Date')['Total Sales'].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_sales['Date'], 
        y=daily_sales['Total Sales'],
        mode='lines+markers',
        line=dict(color='#3498db', width=2),
        marker=dict(size=5),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.2)'
    ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Sales (Rs)",
        height=380,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales by Branch")
        branch_sales = df.groupby('Branch')['Total Sales'].sum().reset_index()
        fig = px.pie(
            branch_sales, 
            values='Total Sales', 
            names='Branch',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=30, b=0))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Sales by Category")
        category_sales = df.groupby('Category')['Total Sales'].sum().reset_index().nlargest(8, 'Total Sales')
        fig = px.pie(
            category_sales, 
            values='Total Sales', 
            names='Category',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=30, b=0))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.divider()
st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')} | Data cached for 10 minutes")
