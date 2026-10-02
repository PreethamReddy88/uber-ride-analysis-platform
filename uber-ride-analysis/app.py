"""
Uber Ride Analysis Dashboard
=============================
A beginner-friendly Streamlit dashboard that analyses 10,000 Uber rides.
Run with:  streamlit run app.py
"""

import os
import warnings

import numpy as np
import pandas as pd
import streamlit as st

# Try importing Plotly for interactive charts; fall back to matplotlib/seaborn
try:
    import plotly.express as px
    import plotly.graph_objects as go

    USE_PLOTLY = True
except ImportError:
    import matplotlib.pyplot as plt
    import seaborn as sns

    USE_PLOTLY = False

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Uber Ride Analysis Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CUSTOM CSS – KPI cards & general polish
# ──────────────────────────────────────────────
st.markdown(
    """
<style>
/* KPI card styling */
.kpi-card {
    background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
    border-radius: 14px;
    padding: 18px 12px;
    text-align: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    border: 1px solid rgba(255,255,255,0.06);
    box-sizing: border-box;
}
.kpi-card h3 {
    color: #a0a0b8;
    font-size: 0.85rem;
    margin-bottom: 6px;
    font-weight: 500;
    letter-spacing: 0.5px;
    white-space: nowrap;
}
.kpi-card h2 {
    color: #ffffff;
    font-size: 1.35rem;
    margin: 0;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Section dividers */
.section-header {
    font-size: 1.35rem;
    font-weight: 700;
    margin-top: 2.2rem;
    margin-bottom: 0.6rem;
    padding-bottom: 6px;
    border-bottom: 3px solid #636efa;
    display: inline-block;
}

/* Insight boxes */
.insight-box {
    background: linear-gradient(135deg, #1e1e2f 0%, #252538 100%);
    border-left: 4px solid #636efa;
    padding: 13px 16px;
    border-radius: 8px;
    margin-bottom: 12px;
    font-size: 0.95rem;
    line-height: 1.5;
    color: #e2e8f0;
    box-sizing: border-box;
    display: block;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
.insight-box strong {
    color: #ffffff;
    font-weight: 600;
}
.insight-icon {
    margin-right: 6px;
    display: inline-block;
}
</style>
""",
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────
# DATA LOADING & PREPROCESSING
# ──────────────────────────────────────────────
@st.cache_data
def load_and_preprocess(path: str) -> pd.DataFrame:
    """Load the CSV, clean it, and engineer useful features."""

    # --- Load -----------------------------------------------------------
    df = pd.read_csv(path)

    # --- Remove exact duplicate rows ------------------------------------
    df = df.drop_duplicates()

    # --- Parse date & time ----------------------------------------------
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    if "Time" in df.columns:
        df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S", errors="coerce").dt.time

    # --- Convert numeric columns ----------------------------------------
    for col in ["Distance_KM", "Trip_Duration_Min", "Fare_INR", "Driver_Rating", "Customer_Rating"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- Handle obviously invalid values --------------------------------
    # Distance and duration must be positive
    if "Distance_KM" in df.columns:
        df.loc[df["Distance_KM"] <= 0, "Distance_KM"] = np.nan
    if "Trip_Duration_Min" in df.columns:
        df.loc[df["Trip_Duration_Min"] <= 0, "Trip_Duration_Min"] = np.nan
    if "Fare_INR" in df.columns:
        df.loc[df["Fare_INR"] <= 0, "Fare_INR"] = np.nan

    # --- Fill missing numeric values with median (safe, preserves data) -
    for col in ["Distance_KM", "Trip_Duration_Min", "Fare_INR"]:
        if col in df.columns:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

    # --- Drop rows where Date could not be parsed -----------------------
    if "Date" in df.columns:
        df = df.dropna(subset=["Date"])

    # --- Feature engineering --------------------------------------------
    if "Date" in df.columns:
        df["Hour"] = df["Date"].dt.hour  # will be 0 since Date has no time
        df["Day_of_Week"] = df["Date"].dt.day_name()
        df["Month"] = df["Date"].dt.month_name()
        df["Month_Num"] = df["Date"].dt.month

    # If Time column exists, use it for Hour instead
    if "Time" in df.columns:
        df["Hour"] = df["Time"].apply(lambda t: t.hour if pd.notnull(t) else 0)

    return df


# Locate the CSV automatically
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_DIR, "uber_rides.csv")

if not os.path.exists(CSV_PATH):
    st.error("❌  CSV file not found at `data/uber_rides.csv`. Please place the dataset there.")
    st.stop()

df_raw = load_and_preprocess(CSV_PATH)

if df_raw.empty:
    st.warning("⚠️  The dataset is empty after preprocessing.")
    st.stop()

# ──────────────────────────────────────────────
# SIDEBAR FILTERS
# ──────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/c/cc/Uber_logo_2018.png",
    width=160,
)
st.sidebar.markdown("## 🔍 Filters")

# Date range
if "Date" in df_raw.columns:
    min_date = df_raw["Date"].min().date()
    max_date = df_raw["Date"].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

# Pickup location
if "Pickup_Location" in df_raw.columns:
    all_pickups = sorted(df_raw["Pickup_Location"].dropna().unique())
    selected_pickups = st.sidebar.multiselect("Pickup Location", all_pickups, default=[])

# Dropoff location
if "Dropoff_Location" in df_raw.columns:
    all_dropoffs = sorted(df_raw["Dropoff_Location"].dropna().unique())
    selected_dropoffs = st.sidebar.multiselect("Dropoff Location", all_dropoffs, default=[])

# Payment type
if "Payment_Type" in df_raw.columns:
    all_payments = sorted(df_raw["Payment_Type"].dropna().unique())
    selected_payments = st.sidebar.multiselect("Payment Type", all_payments, default=[])

# ──────────────────────────────────────────────
# APPLY FILTERS
# ──────────────────────────────────────────────
df = df_raw.copy()

# Date filter
if "Date" in df.columns:
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        df = df[(df["Date"] >= start) & (df["Date"] <= end)]

# Location filters
if selected_pickups:
    df = df[df["Pickup_Location"].isin(selected_pickups)]
if selected_dropoffs:
    df = df[df["Dropoff_Location"].isin(selected_dropoffs)]
if selected_payments:
    df = df[df["Payment_Type"].isin(selected_payments)]

if df.empty:
    st.warning("⚠️  No rides match the selected filters. Try adjusting the sidebar filters.")
    st.stop()

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown("# 🚗 Uber Ride Analysis Dashboard")
st.markdown("*Interactive analysis of Uber ride data — powered by Streamlit*")
st.markdown("---")

# ──────────────────────────────────────────────
# KPI CARDS
# ──────────────────────────────────────────────
total_rides = len(df)
total_revenue = df["Fare_INR"].sum() if "Fare_INR" in df.columns else 0
avg_fare = df["Fare_INR"].mean() if "Fare_INR" in df.columns else 0
avg_distance = df["Distance_KM"].mean() if "Distance_KM" in df.columns else 0
avg_duration = df["Trip_Duration_Min"].mean() if "Trip_Duration_Min" in df.columns else 0

# Clean readable format for total revenue on one line
if total_revenue >= 1_000_000:
    revenue_display = f"₹{total_revenue / 1_000_000:.2f}M"
elif total_revenue >= 1_000:
    revenue_display = f"₹{total_revenue / 1_000:.1f}K"
else:
    revenue_display = f"₹{total_revenue:,.0f}"

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(
        f'<div class="kpi-card"><h3>🚕 Total Rides</h3><h2>{total_rides:,}</h2></div>',
        unsafe_allow_html=True,
    )
with kpi2:
    st.markdown(
        f'<div class="kpi-card" title="Total Revenue: ₹{total_revenue:,.2f}">'
        f'<h3>💰 Total Revenue</h3><h2>{revenue_display}</h2></div>',
        unsafe_allow_html=True,
    )
with kpi3:
    st.markdown(
        f'<div class="kpi-card"><h3>📊 Avg Fare</h3><h2>₹{avg_fare:,.2f}</h2></div>',
        unsafe_allow_html=True,
    )
with kpi4:
    st.markdown(
        f'<div class="kpi-card"><h3>📏 Avg Distance</h3><h2>{avg_distance:,.2f} km</h2></div>',
        unsafe_allow_html=True,
    )
with kpi5:
    st.markdown(
        f'<div class="kpi-card"><h3>⏱ Avg Duration</h3><h2>{avg_duration:,.1f} min</h2></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ──────────────────────────────────────────────
# HELPER: Chart rendering
# ──────────────────────────────────────────────


def plotly_bar(data, x, y, title, xlabel, ylabel, color=None, orientation="v"):
    """Render a bar chart with Plotly (or fall back to matplotlib)."""
    if USE_PLOTLY:
        fig = px.bar(
            data,
            x=x,
            y=y,
            title=title,
            labels={x: xlabel, y: ylabel},
            color=color,
            text_auto=True,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            title_font_size=16,
            margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=data, x=x, y=y, ax=ax, palette="viridis")
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig)


def plotly_histogram(series, title, xlabel, nbins=30):
    """Render a histogram."""
    if USE_PLOTLY:
        fig = px.histogram(series, nbins=nbins, title=title, labels={"value": xlabel})
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            title_font_size=16,
            showlegend=False,
            margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(series.dropna(), bins=nbins, color="#636efa", edgecolor="white")
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Count")
        plt.tight_layout()
        st.pyplot(fig)


def plotly_pie(data, names, values, title):
    """Render a pie / donut chart."""
    if USE_PLOTLY:
        fig = px.pie(data, names=names, values=values, title=title, hole=0.4)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            title_font_size=16,
            margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(data[values], labels=data[names], autopct="%1.1f%%", startangle=140)
        ax.set_title(title)
        plt.tight_layout()
        st.pyplot(fig)


# ──────────────────────────────────────────────
# VISUALISATIONS
# ──────────────────────────────────────────────

st.markdown('<p class="section-header">📊 Ride Trends</p>', unsafe_allow_html=True)

# 1. Rides by Hour
col1, col2 = st.columns(2)
with col1:
    if "Hour" in df.columns:
        hourly = df.groupby("Hour").size().reset_index(name="Rides")
        plotly_bar(hourly, "Hour", "Rides", "Rides by Hour of Day", "Hour", "Number of Rides")

# 2. Rides by Day of Week
with col2:
    if "Day_of_Week" in df.columns:
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily = df.groupby("Day_of_Week").size().reset_index(name="Rides")
        daily["Day_of_Week"] = pd.Categorical(daily["Day_of_Week"], categories=day_order, ordered=True)
        daily = daily.sort_values("Day_of_Week")
        plotly_bar(daily, "Day_of_Week", "Rides", "Rides by Day of Week", "Day", "Number of Rides")

# 3. Rides by Month
if "Month" in df.columns:
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    monthly = df.groupby(["Month", "Month_Num"]).size().reset_index(name="Rides")
    monthly = monthly.sort_values("Month_Num")
    plotly_bar(monthly, "Month", "Rides", "Rides by Month", "Month", "Number of Rides")

st.markdown("---")

# ──────────────────────────────────────────────
st.markdown('<p class="section-header">📍 Location Analysis</p>', unsafe_allow_html=True)

col3, col4 = st.columns(2)

# 4. Top 10 Pickup Locations
with col3:
    if "Pickup_Location" in df.columns:
        top_pickups = df["Pickup_Location"].value_counts().head(10).reset_index()
        top_pickups.columns = ["Location", "Rides"]
        plotly_bar(top_pickups, "Location", "Rides", "Top 10 Pickup Locations", "Location", "Rides")

# 5. Top 10 Dropoff Locations
with col4:
    if "Dropoff_Location" in df.columns:
        top_dropoffs = df["Dropoff_Location"].value_counts().head(10).reset_index()
        top_dropoffs.columns = ["Location", "Rides"]
        plotly_bar(top_dropoffs, "Location", "Rides", "Top 10 Dropoff Locations", "Location", "Rides")

st.markdown("---")

# ──────────────────────────────────────────────
st.markdown('<p class="section-header">💵 Fare & Distance Analysis</p>', unsafe_allow_html=True)

col5, col6 = st.columns(2)

# 6. Fare Distribution
with col5:
    if "Fare_INR" in df.columns:
        plotly_histogram(df["Fare_INR"], "Fare Distribution (₹)", "Fare (₹)")

# 7. Distance Distribution
with col6:
    if "Distance_KM" in df.columns:
        plotly_histogram(df["Distance_KM"], "Distance Distribution (km)", "Distance (km)")

col7, col8 = st.columns(2)

# 8. Average Fare by Hour
with col7:
    if "Hour" in df.columns and "Fare_INR" in df.columns:
        avg_fare_hour = df.groupby("Hour")["Fare_INR"].mean().reset_index()
        avg_fare_hour.columns = ["Hour", "Avg_Fare"]
        plotly_bar(avg_fare_hour, "Hour", "Avg_Fare", "Average Fare by Hour (₹)", "Hour", "Avg Fare (₹)")

# 9. Average Fare by Pickup Location (Top 10)
with col8:
    if "Pickup_Location" in df.columns and "Fare_INR" in df.columns:
        avg_fare_loc = (
            df.groupby("Pickup_Location")["Fare_INR"]
            .mean()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        avg_fare_loc.columns = ["Location", "Avg_Fare"]
        plotly_bar(avg_fare_loc, "Location", "Avg_Fare", "Avg Fare by Pickup Location (₹)", "Location", "Avg Fare (₹)")

# 10. Payment Type Distribution
if "Payment_Type" in df.columns:
    pay_dist = df["Payment_Type"].value_counts().reset_index()
    pay_dist.columns = ["Payment_Type", "Count"]
    plotly_pie(pay_dist, "Payment_Type", "Count", "Payment Type Distribution")

st.markdown("---")

# ──────────────────────────────────────────────
# KEY INSIGHTS
# ──────────────────────────────────────────────
st.markdown('<p class="section-header">💡 Key Business Insights</p>', unsafe_allow_html=True)

insights = []

# Busiest hour
if "Hour" in df.columns:
    busiest_hour = df["Hour"].value_counts().idxmax()
    busiest_hour_count = df["Hour"].value_counts().max()
    insights.append(("🕐", "Busiest Hour", f"{busiest_hour}:00 ({busiest_hour_count:,} rides)"))

# Busiest day
if "Day_of_Week" in df.columns:
    busiest_day = df["Day_of_Week"].value_counts().idxmax()
    busiest_day_count = df["Day_of_Week"].value_counts().max()
    insights.append(("📅", "Busiest Day", f"{busiest_day} ({busiest_day_count:,} rides)"))

# Busiest month
if "Month" in df.columns:
    busiest_month = df["Month"].value_counts().idxmax()
    busiest_month_count = df["Month"].value_counts().max()
    insights.append(("📆", "Busiest Month", f"{busiest_month} ({busiest_month_count:,} rides)"))

# Most popular pickup
if "Pickup_Location" in df.columns:
    top_pickup = df["Pickup_Location"].value_counts().idxmax()
    top_pickup_count = df["Pickup_Location"].value_counts().max()
    insights.append(("📍", "Most Popular Pickup", f"{top_pickup} ({top_pickup_count:,} rides)"))

# Most popular dropoff
if "Dropoff_Location" in df.columns:
    top_dropoff = df["Dropoff_Location"].value_counts().idxmax()
    top_dropoff_count = df["Dropoff_Location"].value_counts().max()
    insights.append(("🏁", "Most Popular Dropoff", f"{top_dropoff} ({top_dropoff_count:,} rides)"))

# Average fare
if "Fare_INR" in df.columns:
    insights.append(("💰", "Average Fare", f"₹{df['Fare_INR'].mean():,.2f}"))

# Average distance
if "Distance_KM" in df.columns:
    insights.append(("📏", "Average Distance", f"{df['Distance_KM'].mean():,.2f} km"))

# Average trip duration
if "Trip_Duration_Min" in df.columns:
    insights.append(("⏱", "Average Trip Duration", f"{df['Trip_Duration_Min'].mean():,.1f} minutes"))

# Highest-demand period (hour + day combo)
if "Hour" in df.columns and "Day_of_Week" in df.columns:
    peak = df.groupby(["Day_of_Week", "Hour"]).size().idxmax()
    insights.append(("🔥", "Highest-Demand Period", f"{peak[0]} at {peak[1]}:00"))

# Most common payment type
if "Payment_Type" in df.columns:
    top_pay = df["Payment_Type"].value_counts().idxmax()
    insights.append(("💳", "Most Common Payment", f"{top_pay}"))

# Display insights cleanly in two columns without overlap or duplicated text
col_a, col_b = st.columns(2)
half = (len(insights) + 1) // 2
left_insights = insights[:half]
right_insights = insights[half:]

with col_a:
    for icon, label, val in left_insights:
        st.markdown(
            f'<div class="insight-box"><span class="insight-icon">{icon}</span><strong>{label}:</strong> {val}</div>',
            unsafe_allow_html=True,
        )

with col_b:
    for icon, label, val in right_insights:
        st.markdown(
            f'<div class="insight-box"><span class="insight-icon">{icon}</span><strong>{label}:</strong> {val}</div>',
            unsafe_allow_html=True,
        )

st.markdown("---")

# ──────────────────────────────────────────────
# RAW DATA PREVIEW
# ──────────────────────────────────────────────
with st.expander("📋 View Raw Data"):
    st.dataframe(df.head(100), use_container_width=True)
    st.caption(f"Showing first 100 of {len(df):,} filtered rides.")

# Footer
st.markdown(
    """
<div style="text-align:center; color:#666; padding:20px 0 10px 0; font-size:0.85rem;">
    Uber Ride Analysis Dashboard &nbsp;|&nbsp; Built with ❤️ using Streamlit
</div>
""",
    unsafe_allow_html=True,
)
