import streamlit as st
import pandas as pd
import numpy as np
import mysql.connector
import plotly.express as px
import plotly.graph_objects as go
import time
import sys
import textwrap

# Configure stdout to use UTF-8 to prevent console issues
sys.stdout.reconfigure(encoding='utf-8')

# --- Page Configuration ---
st.set_page_config(page_title="E-Commerce Power BI Dashboard", layout="wide", page_icon="📊")

# Power BI Classic Color Palette
PBI_COLORS = ['#118D95', '#1F4E79', '#F2C811', '#8064A2', '#4B6F96', '#D65D5B', '#2C9B6A']

# Custom CSS for Power BI Light Theme corporate report styling
st.markdown("""
<style>
    /* Segoe UI and clean corporate fonts */
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Force high contrast light theme canvas */
    .stApp {
        background-color: #f3f2f1 !important;
        color: #252423 !important;
    }
    
    /* Enforce dark charcoal color for all body texts to prevent dark mode blending issues */
    p, span, label, li, ul, ol, div[data-testid="stExpander"] details summary {
        color: #252423 !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Segoe UI', sans-serif !important;
        font-weight: 600 !important;
        color: #092a47 !important; /* Power BI dark corporate navy */
    }

    /* Left Sidebar Panel */
    section[data-testid="stSidebar"] {
        background-color: #faf9f8 !important; /* Power BI sidebar off-white */
        border-right: 1px solid #e1dfdd !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Sidebar text controls */
    section[data-testid="stSidebar"] .stText, 
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6 {
        color: #252423 !important;
        font-weight: 600;
    }

    /* Fix text input field and placeholder visibility */
    div[data-baseweb="input"] input, .stTextInput input, .stTextArea textarea {
        color: #252423 !important; /* Dark charcoal text */
        background-color: #ffffff !important;
        border: 1px solid #d2d0ce !important;
    }
    
    /* High visibility placeholders */
    input::placeholder, textarea::placeholder, .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #555555 !important; /* Dark visible gray */
        opacity: 1 !important;
    }
    
    /* Dropdown and Multi-select container styles */
    div[data-baseweb="select"] div {
        color: #252423 !important;
    }
    
    /* Selected items in multi-select */
    span[data-baseweb="tag"] {
        background-color: #e1dfdd !important;
        color: #252423 !important;
    }
    span[data-baseweb="tag"] span {
        color: #252423 !important;
    }

    /* Dropdown listbox items (rendered in portals) */
    div[role="listbox"] div, div[role="option"], [data-baseweb="popover"] div {
        color: #252423 !important;
        background-color: #ffffff !important;
    }
    div[role="listbox"] div:hover, div[role="option"]:hover {
        background-color: #f3f2f1 !important;
        color: #118D95 !important;
    }

    /* Sliders text styling */
    div[data-testid="stSlider"] p, div[data-testid="stSlider"] span {
        color: #252423 !important;
    }
    div[data-testid="stSlider"] div[data-presentation="tooltip"] {
        color: #ffffff !important;
        background-color: #118d95 !important;
    }

    /* Radio buttons text styling */
    div[data-testid="stRadio"] label, div[data-testid="stRadio"] span {
        color: #252423 !important;
    }

    /* Expander header styling */
    div[data-testid="stExpander"] details summary p {
        color: #092a47 !important;
        font-weight: 600 !important;
    }

    /* Streamlit dividers matching PBI gray borders */
    hr {
        border-color: #e1dfdd !important;
    }
    
    /* Form inputs and buttons styled for Excel/PBI grid style */
    .stButton>button {
        background-color: #118d95 !important;
        color: white !important;
        border-radius: 4px !important;
        border: none !important;
        font-weight: 600 !important;
    }
    
    .stButton>button:hover {
        background-color: #0d6e75 !important;
    }

    /* Styled Tab container mimicking Power BI report sheets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e1dfdd;
        padding: 6px 6px 0px 6px;
        border-radius: 6px 6px 0px 0px;
        border-bottom: 2px solid #118d95;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #faf9f8;
        border-radius: 4px 4px 0px 0px;
        padding: 8px 18px;
        color: #605e5c !important;
        font-weight: 600;
        border: 1px solid #d2d0ce;
        border-bottom: none;
        font-size: 0.92em;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important; 
        color: #118d95 !important; /* Active teal selection */
        border: 1px solid #118d95 !important;
        border-bottom: 3px solid #ffffff !important; /* Seamless merge with panel */
        transform: translateY(1px);
    }
</style>
""", unsafe_allow_html=True)

# --- 1. DATABASE CONNECTION ---
def get_db_connection():
    # Automatically pulls credentials from your secrets, enabling fast C extension
    return mysql.connector.connect(use_pure=False, **st.secrets["mysql"])

# --- 2. CACHED DATA LOADERS (Fast C Ingestion & 10x parsed Date formatting) ---
@st.cache_data(ttl=300, show_spinner=False)
def load_data_from_db():
    conn = get_db_connection()
    query = """
    SELECT OrderID, ProductID, ProductName, Quantity, OrderDate, Price, Sales, CustomerID, Region 
    FROM samplesuperstore
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Speed up datetime conversion 10x using explicit date-time formatting
    df['OrderDate'] = pd.to_datetime(df['OrderDate'], format='%m/%d/%y %H:%M', errors='coerce')
    df['Quantity'] = df['Quantity'].astype('int32')
    df['Price'] = df['Price'].astype('float32')
    df['Sales'] = df['Sales'].astype('float32')
    df['Region'] = df['Region'].astype('category')
    return df

@st.cache_data(ttl=3600, show_spinner=False)
def load_data_from_csv():
    dtypes = {
        'OrderID': str,
        'ProductID': str,
        'ProductName': str,
        'Quantity': 'int32',
        'OrderDate': str,
        'Price': 'float32',
        'Sales': 'float32',
        'CustomerID': str,
        'Region': str
    }
    df = pd.read_csv('samplesuperstore.csv', dtype=dtypes)
    df['OrderDate'] = pd.to_datetime(df['OrderDate'], format='%m/%d/%y %H:%M', errors='coerce')
    df['Region'] = df['Region'].astype('category')
    return df

def fetch_recent_suggestions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_name, feedback_text, suggestion_id FROM client_suggestions ORDER BY suggestion_id DESC LIMIT 5")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception:
        return []

# --- Header Banner ---
st.title("📊 E-Commerce Analytics Dashboard")
st.markdown("Corporate Reporting Canvas • Powered by In-Memory Engine & Remote Aiven Cloud Database")

# --- 3. SIDEBAR CONTROLS & DYNAMIC FILTER EXPANDERS ---
st.sidebar.header("🎛️ Page Filters")

# Connection Settings - check if CSV is present to adapt to local vs cloud environment
import os
csv_exists = os.path.exists('samplesuperstore.csv')
source_options = []
if csv_exists:
    source_options.append("Local High-Performance Cache (CSV)")
source_options.append("Live Cloud Database (MySQL)")

source_option = st.sidebar.radio(
    "Data Source Mode",
    options=source_options,
    help="CSV cache loads in milliseconds. Cloud DB pulls real-time transactions."
)

# Load data with robust fallback
df = None
data_load_method = ""
start_load_time = time.time()

if source_option == "Live Cloud Database (MySQL)":
    try:
        with st.spinner("Connecting to Aiven Cloud MySQL..."):
            df = load_data_from_db()
            data_load_method = "Aiven Cloud MySQL"
    except Exception as e:
        st.sidebar.error(f"Database connection failed: {e}")
        if csv_exists:
            st.sidebar.warning("⚠️ Automatically falling back to Local CSV...")
            df = load_data_from_csv()
            data_load_method = "Local CSV (Fallback)"
        else:
            st.error("❌ Critical Error: Database connection failed and local CSV cache is not available on the cloud server. Please check your Streamlit Secrets database credentials.")
            st.stop()
else:
    if csv_exists:
        df = load_data_from_csv()
        data_load_method = "Local CSV Cache"
    else:
        st.error("❌ Local CSV Cache not found. Please switch to Database mode.")
        st.stop()

load_elapsed = time.time() - start_load_time

# Display data source status
st.sidebar.info(f"⚡ Loaded {len(df):,} records via **{data_load_method}** in **{load_elapsed:.2f}s**.")
st.sidebar.divider()

# Filter Group 1: Timeframe
with st.sidebar.expander("📅 Timeframe Filters", expanded=True):
    min_date = df['OrderDate'].min()
    max_date = df['OrderDate'].max()
    if pd.isnull(min_date) or pd.isnull(max_date):
        min_date = pd.Timestamp('2010-12-01')
        max_date = pd.Timestamp('2011-12-09')
        
    date_range = st.date_input(
        "Order Date Range",
        value=[min_date.date(), max_date.date()],
        min_value=min_date.date(),
        max_value=max_date.date()
    )
    
    hour_range = st.slider(
        "Hour of Day (Purchase Time)",
        min_value=0,
        max_value=23,
        value=(0, 23)
    )

# Filter Group 2: Product & Transaction Values
with st.sidebar.expander("🏷️ Product & Sales Value Filters", expanded=True):
    regions_list = sorted(df['Region'].dropna().unique())
    selected_regions = st.multiselect(
        "Filter by Regions",
        options=regions_list,
        default=regions_list[:5] if len(regions_list) > 5 else regions_list
    )
    
    max_sales_val = float(df['Sales'].max())
    sales_range = st.slider(
        "Sales Order Value ($)",
        min_value=0.0,
        max_value=max_sales_val,
        value=(0.0, max_sales_val)
    )
    
    max_qty_val = int(df['Quantity'].max())
    qty_range = st.slider(
        "Quantity Range",
        min_value=0,
        max_value=max_qty_val,
        value=(0, max_qty_val)
    )
    
    max_price_val = float(df['Price'].max())
    price_range = st.slider(
        "Unit Price Range ($)",
        min_value=0.0,
        max_value=max_price_val,
        value=(0.0, max_price_val)
    )

# Filter Group 3: Text Search
with st.sidebar.expander("🔍 Advanced Text Search", expanded=False):
    product_search = st.text_input("Search Product Name", placeholder="e.g. T-LIGHT HOLDER")
    customer_search = st.text_input("Search Customer ID", placeholder="e.g. 17850")

# --- Apply Filters in Memory ---
df_filtered = df.copy()

# Hour of day column extraction
df_filtered['Hour'] = df_filtered['OrderDate'].dt.hour

if selected_regions:
    df_filtered = df_filtered[df_filtered['Region'].isin(selected_regions)]

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_filtered[(df_filtered['OrderDate'].dt.date >= start_date) & (df_filtered['OrderDate'].dt.date <= end_date)]

df_filtered = df_filtered[(df_filtered['Hour'] >= hour_range[0]) & (df_filtered['Hour'] <= hour_range[1])]
df_filtered = df_filtered[(df_filtered['Sales'] >= sales_range[0]) & (df_filtered['Sales'] <= sales_range[1])]
df_filtered = df_filtered[(df_filtered['Quantity'] >= qty_range[0]) & (df_filtered['Quantity'] <= qty_range[1])]
df_filtered = df_filtered[(df_filtered['Price'] >= price_range[0]) & (df_filtered['Price'] <= price_range[1])]

if product_search:
    df_filtered = df_filtered[df_filtered['ProductName'].str.contains(product_search, case=False, na=False)]

if customer_search:
    df_filtered = df_filtered[df_filtered['CustomerID'].astype(str).str.contains(customer_search, case=False, na=False)]

# --- 4. TOP METRICS & KPI CARDS ---
if len(df_filtered) == 0:
    st.warning("No records match the selected filters. Please adjust the sidebar controls.")
else:
    # Calculations
    total_records = len(df_filtered)
    total_revenue = df_filtered['Sales'].sum()
    avg_price = df_filtered['Price'].mean()
    total_units = df_filtered['Quantity'].sum()
    unique_cust = df_filtered['CustomerID'].nunique()
    
    # KPI Value Formatter for single line fit
    def format_kpi_value(val, prefix=""):
        if val >= 1_000_000_000:
            return f"{prefix}{val/1_000_000_000:.2f}B"
        elif val >= 1_000_000:
            return f"{prefix}{val/1_000_000:.2f}M"
        elif val >= 1_000:
            return f"{prefix}{val/1_000:.1f}K"
        else:
            if isinstance(val, float):
                return f"{prefix}{val:.2f}"
            return f"{prefix}{val}"

    # Styled Power BI / Excel Solid Card Generator with equal heights, responsive fonts, and hover tooltips
    def kpi_card(title, display_value, full_value, subtitle, icon="📈", border_color="#118D95"):
        return textwrap.dedent(f"""
        <div title="Exact Value: {full_value}" style="
            background: #ffffff;
            border-radius: 6px;
            padding: 12px 15px;
            border-left: 6px solid {border_color};
            border-top: 1px solid #e1dfdd;
            border-right: 1px solid #e1dfdd;
            border-bottom: 1px solid #e1dfdd;
            box-shadow: 0 1.6px 3.6px 0 rgba(0,0,0,0.1), 0 0.3px 0.9px 0 rgba(0,0,0,0.05);
            margin-bottom: 15px;
            height: 105px; /* Equal height and aligned */
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            cursor: help;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                <div style="font-size: 0.8em; color: #605e5c; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 80%;">{title}</div>
                <div style="font-size: 1.2em; opacity: 0.8;">{icon}</div>
            </div>
            <div>
                <div style="font-size: clamp(1.2em, 1.8vw, 1.6em); font-weight: 700; color: #252423; margin: 2px 0; font-family: 'Segoe UI', sans-serif; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{display_value}</div>
                <div style="font-size: 0.72em; color: #a19f9d; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{subtitle}</div>
            </div>
        </div>
        """)

    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(kpi_card("Total Revenue", format_kpi_value(total_revenue, "$"), f"${total_revenue:,.2f}", "Total sales volume", "💰", "#118D95"), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_card("Transactions", format_kpi_value(total_records), f"{total_records:,}", "Volume of completed purchases", "📦", "#1F4E79"), unsafe_allow_html=True)
    with col3:
        st.markdown(kpi_card("Units Sold", format_kpi_value(total_units), f"{total_units:,}", "Quantity of items delivered", "🛒", "#F2C811"), unsafe_allow_html=True)
    with col4:
        st.markdown(kpi_card("Average Price", f"${avg_price:.2f}", f"${avg_price:,.4f}", "Mean retail item price", "🏷️", "#4B6F96"), unsafe_allow_html=True)
    with col5:
        st.markdown(kpi_card("Active Clients", format_kpi_value(unique_cust), f"{unique_cust:,}", "Unique purchasing customers", "👥", "#8064A2"), unsafe_allow_html=True)

    # --- 5. TABBED GRID SYSTEM ---
    tab_overview, tab_product, tab_customer, tab_feedback = st.tabs([
        "📈 Executive Overview", 
        "🛍️ Product Insights", 
        "👥 Customer Analytics", 
        "💬 Client Suggestion Board"
    ])

    # Custom Plotly Theme Setup for Power BI Look
    def apply_pbi_theme(fig):
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_gridcolor='#e1dfdd',
            yaxis_gridcolor='#e1dfdd',
            font_color='#252423',
            font_family='Segoe UI',
            title_font_color='#092a47',
            title_font_family='Segoe UI',
            title_font_size=16,
            margin=dict(l=40, r=20, t=50, b=40)
        )
        return fig

    # --- TAB 1: EXECUTIVE OVERVIEW ---
    with tab_overview:
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            # Container 1: Monthly Sales Revenue Performance Trend
            with st.container(border=True):
                df_trend = df_filtered.set_index('OrderDate').resample('ME')['Sales'].sum().reset_index()
                df_trend['SalesText'] = df_trend['Sales'].apply(lambda x: f"${x/1000:.1f}K" if x > 0 else "")
                
                fig_trend = px.line(
                    df_trend, 
                    x='OrderDate', 
                    y='Sales', 
                    title="Monthly Sales Revenue Performance Trend ($)",
                    labels={'Sales': 'Revenue ($)', 'OrderDate': 'Month'},
                    template="plotly_white",
                    text='SalesText'
                )
                
                # Monthly Sales Average Line
                avg_monthly_sales = df_trend['Sales'].mean() if len(df_trend) > 0 else 0.0
                if avg_monthly_sales > 0:
                    fig_trend.add_hline(
                        y=avg_monthly_sales, 
                        line_dash="dash", 
                        line_color="#D65D5B", 
                        annotation_text=f"Monthly Avg: ${avg_monthly_sales/1000:.1f}K", 
                        annotation_position="bottom right"
                    )
                
                fig_trend.update_traces(
                    line_color='#1F4E79', 
                    line_width=3, 
                    mode="lines+markers+text", 
                    marker=dict(size=6, color='#118D95'),
                    textposition="top center"
                )
                st.plotly_chart(apply_pbi_theme(fig_trend), width="stretch")
            
        with row1_col2:
            # Container 2: Regional Revenue Donut
            with st.container(border=True):
                df_region = df_filtered.groupby('Region', observed=False)['Sales'].sum().reset_index()
                df_region = df_region.sort_values(by='Sales', ascending=False).head(8)
                fig_region = px.pie(
                    df_region, 
                    values='Sales', 
                    names='Region', 
                    hole=0.5, 
                    title="Regional Revenue Contribution Share (%)",
                    template="plotly_white",
                    color_discrete_sequence=PBI_COLORS
                )
                
                # Dynamic Center Value
                fig_region.update_layout(
                    annotations=[dict(
                        text=f"Total Sales<br><b>{format_kpi_value(total_revenue, '$')}</b>",
                        x=0.5, y=0.5, font_size=15, showarrow=False,
                        font_family='Segoe UI', font_color='#092a47'
                    )]
                )
                
                fig_region.update_traces(textposition='inside', textinfo='label+percent')
                st.plotly_chart(apply_pbi_theme(fig_region), width="stretch")

        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            # Container 3: Sales by Day of Week
            with st.container(border=True):
                df_filtered['DayOfWeek'] = df_filtered['OrderDate'].dt.day_name()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                df_day = df_filtered.groupby('DayOfWeek', observed=False)['Sales'].sum().reindex(day_order).reset_index()
                df_day['SalesText'] = df_day['Sales'].apply(lambda x: f"${x/1000:.1f}K" if x > 0 else "")
                
                if not df_day.dropna().empty:
                    peak_day_idx = df_day['Sales'].idxmax()
                    peak_day = df_day.loc[peak_day_idx]['DayOfWeek']
                else:
                    peak_day = None
                
                bar_colors = ['#1F4E79' if day == peak_day else '#118D95' for day in df_day['DayOfWeek']]
                
                fig_day = px.bar(
                    df_day,
                    x='DayOfWeek',
                    y='Sales',
                    title="Sales Revenue Distribution by Day of Week ($)",
                    labels={'Sales': 'Revenue ($)', 'DayOfWeek': 'Day of Week'},
                    template="plotly_white",
                    text='SalesText'
                )
                
                # Daily Average Reference Line
                avg_day_sales = df_day['Sales'].mean() if len(df_day) > 0 else 0.0
                if avg_day_sales > 0:
                    fig_day.add_hline(
                        y=avg_day_sales,
                        line_dash="dash",
                        line_color="#D65D5B",
                        annotation_text=f"Daily Avg: ${avg_day_sales/1000:.1f}K",
                        annotation_position="top right"
                    )
                
                fig_day.update_traces(marker_color=bar_colors, textposition='outside')
                st.plotly_chart(apply_pbi_theme(fig_day), width="stretch")
            
        with row2_col2:
            # Container 4 (NEW VISUAL): Cumulative Revenue Growth Over Time
            with st.container(border=True):
                df_trend_cum = df_filtered.set_index('OrderDate').resample('ME')['Sales'].sum().reset_index()
                df_trend_cum['CumulativeSales'] = df_trend_cum['Sales'].cumsum()
                df_trend_cum['CumSalesText'] = df_trend_cum['CumulativeSales'].apply(lambda x: f"${x/1000:.1f}K" if x > 0 else "")
                
                fig_cum = px.area(
                    df_trend_cum,
                    x='OrderDate',
                    y='CumulativeSales',
                    title="Cumulative Revenue Growth Over Time ($)",
                    labels={'CumulativeSales': 'Cumulative Revenue ($)', 'OrderDate': 'Month'},
                    template="plotly_white"
                )
                fig_cum.update_traces(
                    line_color='#2C9B6A',
                    fillcolor='rgba(44, 155, 106, 0.15)',
                    mode='lines+markers'
                )
                st.plotly_chart(apply_pbi_theme(fig_cum), width="stretch")

        row3_col1, row3_col2 = st.columns(2)
        
        with row3_col1:
            # Container 5 (NEW VISUAL): Monthly Average Order Value (AOV) Trend
            with st.container(border=True):
                df_monthly_grp = df_filtered.set_index('OrderDate').resample('ME').agg({'Sales': 'sum', 'OrderID': 'nunique'}).reset_index()
                df_monthly_grp['AOV'] = df_monthly_grp['Sales'] / df_monthly_grp['OrderID'].replace(0, 1)
                df_monthly_grp['AOVText'] = df_monthly_grp['AOV'].apply(lambda x: f"${x:.1f}" if x > 0 else "")
                
                fig_aov = px.line(
                    df_monthly_grp,
                    x='OrderDate',
                    y='AOV',
                    title="Monthly Average Order Value (AOV) Trend ($)",
                    labels={'AOV': 'Average Order Value ($)', 'OrderDate': 'Month'},
                    template="plotly_white",
                    text='AOVText'
                )
                
                # Add Average AOV Reference Line
                avg_aov_val = df_monthly_grp['AOV'].mean() if len(df_monthly_grp) > 0 else 0.0
                if avg_aov_val > 0:
                    fig_aov.add_hline(
                        y=avg_aov_val,
                        line_dash="dash",
                        line_color="#4B6F96",
                        annotation_text=f"AOV Avg: ${avg_aov_val:.2f}",
                        annotation_position="bottom right"
                    )
                
                fig_aov.update_traces(
                    line_color='#8064A2',
                    line_width=3,
                    mode="lines+markers+text",
                    marker=dict(size=6, color='#8064A2'),
                    textposition="top center"
                )
                st.plotly_chart(apply_pbi_theme(fig_aov), width="stretch")

        with row3_col2:
            # Container 6: Setup / Insights Panel
            with st.container(border=True):
                insights_html = """<div style="background: #ffffff; padding: 10px; height: 380px; display: flex; flex-direction: column; justify-content: center;">
<h4 style="color: #092a47; margin-top:0; border-bottom: 2px solid #118d95; padding-bottom: 8px;">📊 Report Insights & Setup</h4>
<p style="font-size: 0.9em; line-height: 1.6; color: #252423;">This dashboard implements corporate <strong>Power BI & Excel</strong> design guidelines. All KPI cards at the top are aligned via flexbox grids to occupy equal height, preventing text wrap breaks.</p>
<ul style="font-size: 0.88em; line-height: 1.6; color: #252423; padding-left: 20px; margin-bottom: 10px;">
<li><strong>Line Chart Labels</strong> display exact monthly totals inside the Overview.</li>
<li><strong>Day of Week Bar Chart</strong> highlights peak transactional revenue dates in deep navy.</li>
<li><strong>Sidebar Filters</strong> are collapsible to clean the analytical workspace.</li>
</ul>
<p style="font-size: 0.88em; color: #555555; font-style: italic; margin-top: 5px;">Use the sidebar connection selectors to switch dynamically between memory cache and live database links.</p>
</div>"""
                st.markdown(insights_html, unsafe_allow_html=True)

    # --- TAB 2: PRODUCT INSIGHTS ---
    with tab_product:
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            # Container 7: Top Products by Revenue
            with st.container(border=True):
                df_prod = df_filtered.groupby('ProductName')['Sales'].sum().reset_index()
                df_prod = df_prod.sort_values(by='Sales', ascending=False).head(10)
                df_prod['SalesText'] = df_prod['Sales'].apply(lambda x: f"${x/1000:.1f}K")
                
                fig_prod = px.bar(
                    df_prod, 
                    x='Sales', 
                    y='ProductName', 
                    orientation='h', 
                    title="Top 10 Selling Products by Revenue Contribution ($)",
                    labels={'Sales': 'Revenue ($)', 'ProductName': 'Product'},
                    template="plotly_white",
                    color='Sales',
                    color_continuous_scale='Teal',
                    text='SalesText'
                )
                fig_prod.update_layout(yaxis={'categoryorder':'total ascending', 'title': None}, coloraxis_showscale=False)
                fig_prod.update_traces(textposition='inside')
                st.plotly_chart(apply_pbi_theme(fig_prod), width="stretch")
            
        with row1_col2:
            # Container 8 (NEW VISUAL): Top 10 Products by Quantity Sold (Volume)
            with st.container(border=True):
                df_prod_qty = df_filtered.groupby('ProductName')['Quantity'].sum().reset_index()
                df_prod_qty = df_prod_qty.sort_values(by='Quantity', ascending=False).head(10)
                df_prod_qty['QtyText'] = df_prod_qty['Quantity'].apply(lambda x: f"{x:,}")
                
                fig_prod_qty = px.bar(
                    df_prod_qty,
                    x='Quantity',
                    y='ProductName',
                    orientation='h',
                    title="Top 10 Products by Quantity Sold (Volume)",
                    labels={'Quantity': 'Quantity Sold', 'ProductName': 'Product'},
                    template="plotly_white",
                    color='Quantity',
                    color_continuous_scale='Bluyl',
                    text='QtyText'
                )
                fig_prod_qty.update_layout(yaxis={'categoryorder':'total ascending', 'title': None}, coloraxis_showscale=False)
                fig_prod_qty.update_traces(textposition='inside')
                st.plotly_chart(apply_pbi_theme(fig_prod_qty), width="stretch")

        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            # Container 9: Unit Price Distribution (Histogram)
            with st.container(border=True):
                fig_price_dist = px.histogram(
                    df_filtered, 
                    x='Price', 
                    nbins=40, 
                    title="Transaction Frequency Distribution by Unit Price ($)",
                    labels={'Price': 'Unit Price ($)', 'count': 'Transaction Count'},
                    template="plotly_white",
                    color_discrete_sequence=['#4B6F96']
                )
                
                # Add Average and Median Price Lines
                if len(df_filtered) > 0:
                    fig_price_dist.add_vline(
                        x=avg_price, 
                        line_dash="dash", 
                        line_color="#1F4E79", 
                        annotation_text=f"Avg: ${avg_price:.2f}", 
                        annotation_position="top right"
                    )
                    median_price = df_filtered['Price'].median()
                    fig_price_dist.add_vline(
                        x=median_price,
                        line_dash="dot",
                        line_color="#D65D5B",
                        annotation_text=f"Med: ${median_price:.2f}",
                        annotation_position="top left"
                    )
                st.plotly_chart(apply_pbi_theme(fig_price_dist), width="stretch")

        with row2_col2:
            # Container 10: Price vs Qty Scatter & Elasticity
            with st.container(border=True):
                sample_size = min(len(df_filtered), 2000)
                df_sample = df_filtered.sample(sample_size, random_state=42)
                df_sample = df_sample.sort_values(by='Price')
                
                fig_scatter = px.scatter(
                    df_sample, 
                    x='Price', 
                    y='Quantity', 
                    color='Sales', 
                    size='Sales',
                    title=f"Price vs. Quantity Correlation (Sampled {sample_size:,} records)",
                    labels={'Price': 'Unit Price ($)', 'Quantity': 'Quantity Purchased'},
                    template="plotly_white",
                    color_continuous_scale='Viridis',
                    hover_data=['ProductName']
                )
                
                # Linear Trend Line calculated manually using numpy
                if len(df_sample) > 1:
                    m, b_coeff = np.polyfit(df_sample['Price'], df_sample['Quantity'], 1)
                    fig_scatter.add_trace(
                        go.Scatter(
                            x=df_sample['Price'],
                            y=m * df_sample['Price'] + b_coeff,
                            mode='lines',
                            name='Elasticity Trend',
                            line=dict(color='#D65D5B', width=2.5, dash='dash')
                        )
                    )
                    
                st.plotly_chart(apply_pbi_theme(fig_scatter), width="stretch")

    # --- TAB 3: CUSTOMER ANALYTICS ---
    with tab_customer:
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            # Container 11: Top Spending Customers
            with st.container(border=True):
                df_cust = df_filtered.groupby('CustomerID')['Sales'].sum().reset_index()
                df_cust = df_cust[df_cust['CustomerID'] != 'GUEST_CHECKOUT']
                df_cust = df_cust.sort_values(by='Sales', ascending=False).head(10)
                df_cust['SalesText'] = df_cust['Sales'].apply(lambda x: f"${x/1000:.1f}K")
                
                fig_cust = px.bar(
                    df_cust,
                    x='Sales',
                    y='CustomerID',
                    orientation='h',
                    title="Top 10 Purchasing Customers by Expenditure ($)",
                    labels={'Sales': 'Total Spend ($)', 'CustomerID': 'Customer Account ID'},
                    template="plotly_white",
                    color='Sales',
                    color_continuous_scale='Purples',
                    text='SalesText'
                )
                fig_cust.update_layout(yaxis={'categoryorder':'total ascending', 'type': 'category'}, coloraxis_showscale=False)
                fig_cust.update_traces(textposition='inside')
                st.plotly_chart(apply_pbi_theme(fig_cust), width="stretch")
            
        with row1_col2:
            # Container 12: Purchasing Hourly Activity Line/Area
            with st.container(border=True):
                df_hour = df_filtered.groupby('Hour')['Sales'].sum().reset_index()
                df_hour = df_hour.set_index('Hour').reindex(range(24), fill_value=0.0).reset_index()
                df_hour['SalesText'] = df_hour['Sales'].apply(lambda x: f"${x/1000:.1f}K" if x > 0 else "")
                
                fig_hour = px.area(
                    df_hour,
                    x='Hour',
                    y='Sales',
                    title="Purchasing Activity Trends by Hour of Day (24h Clock)",
                    labels={'Sales': 'Revenue ($)', 'Hour': 'Hour (24h Clock)'},
                    template="plotly_white"
                )
                fig_hour.update_traces(
                    line_color='#8064A2',
                    fillcolor='rgba(128, 100, 162, 0.15)',
                    mode='lines+markers'
                )
                fig_hour.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=2))
                
                # Highlight peak business window (10:00 AM - 3:00 PM)
                fig_hour.add_vrect(
                    x0=10, x1=15, 
                    fillcolor="rgba(17, 141, 149, 0.12)", 
                    layer="below", 
                    line_width=0,
                    annotation_text="Peak Window (10AM - 3PM)", 
                    annotation_position="top left"
                )
                st.plotly_chart(apply_pbi_theme(fig_hour), width="stretch")

        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            # Container 13 (NEW VISUAL): Customer Loyalty Repeat Order Cohort Frequency
            with st.container(border=True):
                df_cust_orders = df_filtered[df_filtered['CustomerID'] != 'GUEST_CHECKOUT'].groupby('CustomerID')['OrderID'].nunique().reset_index()
                df_freq = df_cust_orders.groupby('OrderID').size().reset_index(name='CustomerCount')
                df_freq = df_freq.sort_values(by='OrderID').head(10) # Show first 10 levels of loyalty
                df_freq['LabelText'] = df_freq['CustomerCount'].apply(lambda x: f"{x:,}")
                
                fig_freq = px.bar(
                    df_freq,
                    x='OrderID',
                    y='CustomerCount',
                    title="Customer Purchase Frequency (Repeat Loyalty Cohorts)",
                    labels={'OrderID': 'Number of Orders Placed', 'CustomerCount': 'Unique Customer Count'},
                    template="plotly_white",
                    color_discrete_sequence=['#4B6F96'],
                    text='LabelText'
                )
                fig_freq.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1))
                fig_freq.update_traces(textposition='outside')
                st.plotly_chart(apply_pbi_theme(fig_freq), width="stretch")

        with row2_col2:
            # Container 14: Customer Loyalty Insights Card
            with st.container(border=True):
                # Calculate repeat buyer metrics
                total_identifiable_cust = df_filtered[df_filtered['CustomerID'] != 'GUEST_CHECKOUT']['CustomerID'].nunique()
                repeat_buyers = len(df_cust_orders[df_cust_orders['OrderID'] > 1])
                repeat_rate = (repeat_buyers / total_identifiable_cust * 100) if total_identifiable_cust > 0 else 0.0
                
                loyalty_html = f"""<div style="background: #ffffff; padding: 10px; height: 380px; display: flex; flex-direction: column; justify-content: center;">
<h4 style="color: #092a47; margin-top:0; border-bottom: 2px solid #8064a2; padding-bottom: 8px;">👥 Customer Loyalty Profile</h4>
<p style="font-size: 0.9em; line-height: 1.6; color: #252423;">Customer lifecycle analysis shows that out of <strong>{total_identifiable_cust:,}</strong> identifiable buyers, <strong>{repeat_buyers:,}</strong> customer accounts have placed multiple transactions, representing a <strong>{repeat_rate:.2f}% Repeat Customer Rate</strong>.</p>
<ul style="font-size: 0.88em; line-height: 1.6; color: #252423; padding-left: 20px; margin-bottom: 10px;">
<li><strong>Single Transaction cohort</strong> accounts for the largest buyer share, suggesting potential for introductory coupons or first-purchase incentives.</li>
<li><strong>Wholesale Accounts</strong>: Cohorts placing 5 or more orders represent highly lucrative recurring business pipelines that should be engaged through VIP support.</li>
</ul>
<p style="font-size: 0.88em; color: #555555; font-style: italic; margin-top: 5px;">Use advanced filters in the sidebar to drill down on high-value transaction sizes and see how regions differ in loyalty.</p>
</div>"""
                st.markdown(loyalty_html, unsafe_allow_html=True)

    # --- TAB 4: SUGGESTION BOARD ---
    with tab_feedback:
        col_feed1, col_feed2 = st.columns([1, 1])
        
        with col_feed1:
            st.subheader("💬 Submit Suggestions")
            st.markdown("Feature requests are logged into the remote cloud database.")
            
            with st.form("feedback_form", clear_on_submit=True):
                client_name = st.text_input("Name / Department")
                feedback = st.text_area("What metrics or charts should be added next?")
                submitted = st.form_submit_button("Submit Suggestion")
                
                if submitted:
                    if client_name and feedback:
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            insert_query = "INSERT INTO client_suggestions (user_name, feedback_text) VALUES (%s, %s)"
                            cursor.execute(insert_query, (client_name, feedback))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success("✅ Suggestion successfully logged into Aiven Cloud Database!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to log: {e}. (Writes require live connection)")
                    else:
                        st.warning("Please fill out both fields.")
                        
        with col_feed2:
            st.subheader("📋 Recent Requests Feed")
            st.markdown("Timeline of feature requests from Aiven database:")
            
            recent_sugs = fetch_recent_suggestions()
            if recent_sugs:
                for sug in recent_sugs:
                    st.markdown(
                        textwrap.dedent(f"""
                        <div style="
                            background: #ffffff; 
                            padding: 14px 20px; 
                            border-radius: 6px; 
                            margin-bottom: 12px; 
                            border-left: 5px solid #118d95;
                            border-top: 1px solid #e1dfdd;
                            border-right: 1px solid #e1dfdd;
                            border-bottom: 1px solid #e1dfdd;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                        ">
                            <strong style="color: #252423; font-size: 0.95em;">👤 {sug['user_name']}</strong>
                            <div style="color: #605e5c; font-size: 0.88em; margin-top: 4px; line-height: 1.4;">
                                "{sug['feedback_text']}"
                            </div>
                        </div>
                        """),
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(textwrap.dedent("""
                <div style="background: #ffffff; padding: 14px 20px; border-radius: 6px; border: 1px solid #e1dfdd; color: #555555; text-align: center;">
                    No feedback logs found in remote database.
                </div>
                """), unsafe_allow_html=True)