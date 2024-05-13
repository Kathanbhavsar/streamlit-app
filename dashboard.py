# dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pymysql
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database connection details
user = os.getenv("USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
database = os.getenv("DATABASE")
port = os.getenv("PORT")


@st.cache_data()
def read_px_data():
    conn = pymysql.connect(
        host="rocked-staging.csxxh3ec5twj.us-east-2.rds.amazonaws.com",
        user="mysql_dev",
        password="Y1xLx23LoFa9",
        database="rocked-staging",
        port=3306,
    )
    query = """
    SELECT * FROM partner_experience_report
    """
    px_data = pd.read_sql(query, conn)
    conn.close()
    return px_data


# Execute the query and load data
@st.cache_data()
def load_data():
    conn = pymysql.connect(
        host="rocked-staging.csxxh3ec5twj.us-east-2.rds.amazonaws.com",
        user="mysql_dev",
        password="Y1xLx23LoFa9",
        database="rocked-staging",
        port=3306,
    )
    query = """
    WITH dealership_mau AS (
      SELECT d.id AS dealership_id, d.name AS dealership_name,
      d.created_at,
             d.lead_pipeline,
             COUNT(DISTINCT e.id) AS total_employees
      FROM dealerships d
      LEFT JOIN employees e ON d.id = e.dealership_id
      LEFT JOIN employee_journeys ej ON e.hash = ej.employee_hash
      GROUP BY d.id, d.name, d.lead_pipeline
    ),
    dealership_content_consumption AS (
      SELECT d.id AS dealership_id,
             COUNT(DISTINCT ed.employee_hash) AS dose_views,
             COUNT(DISTINCT esv.id) AS story_views,
             COUNT(DISTINCT ejgd.id) AS guide_views,
             COUNT(DISTINCT ecav.id) AS capstone_activity_views
      FROM dealerships d
      LEFT JOIN employees e ON d.id = e.dealership_id
      LEFT JOIN employee_doses ed ON e.hash = ed.employee_hash
      LEFT JOIN employee_stories es ON e.hash = es.employee_hash
      LEFT JOIN employee_story_views esv ON es.id = esv.employee_story_id
      LEFT JOIN employee_journeys ej ON e.hash = ej.employee_hash
      LEFT JOIN employee_journey_guide_details ejgd ON ej.id = ejgd.employee_journey_id
      LEFT JOIN employee_guide_views egv ON ejgd.id = egv.employee_journey_guide_detail_id
      LEFT JOIN employee_journey_capstone_responses ejcr ON ej.id = ejcr.employee_journey_id
      LEFT JOIN employee_capstone_activity_views ecav ON ejcr.id = ecav.employee_journey_capstone_responses_id
      GROUP BY d.id
    )
    SELECT dm.dealership_id, dm.dealership_name, dm.total_employees, dm.lead_pipeline ,dm.created_at,
           dcc.dose_views, dcc.story_views, dcc.guide_views, dcc.capstone_activity_views,
           sps.title
    FROM dealership_mau dm
    INNER JOIN dealership_content_consumption dcc ON dm.dealership_id = dcc.dealership_id
    INNER JOIN sales_pipeline_status sps ON dm.lead_pipeline = sps.id;
    """
    total_views = pd.read_sql(query, conn)
    conn.close()

    total_views["lu"] = (
        total_views["dose_views"]
        + total_views["story_views"]
        + total_views["guide_views"]
        + total_views["capstone_activity_views"]
    )
    total_views["created_at"] = pd.to_datetime(total_views["created_at"])

    return total_views


def main():
    # Load the data
    total_views = load_data()
    px_data = read_px_data()

    # Create sidebar
    sidebar = st.sidebar

    # Sidebar style
    sidebar.markdown(
        """
        <style>
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        .sidebar .sidebar-content .widget-title {
            color: #2c3e50;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .sidebar .sidebar-content .widget-text {
            color: #34495e;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Filter by dealership
    @st.cache_data()
    def get_dealership_options():
        return ["All"] + list(total_views["dealership_name"].unique())

    selected_dealership = sidebar.selectbox(
        "🏢 Filter by Dealership",
        get_dealership_options(),
        index=0,
        key="dealership_filter",
    )

    # Filter by title
    @st.cache_data()
    def get_title_options():
        return ["All"] + list(total_views["title"].unique())

    selected_title = sidebar.selectbox(
        "🏷️ Filter by Title", get_title_options(), index=0, key="title_filter"
    )

    # Date range slider
    min_date = total_views["created_at"].min().date()
    max_date = total_views["created_at"].max().date()
    selected_date_range = sidebar.date_input(
        "📅 Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_range_slider",
    )

    # Apply filters
    @st.cache_data()
    def apply_filters(data, dealership, title, start_date, end_date):
        filtered_data = data[
            (data["created_at"].dt.date >= start_date)
            & (data["created_at"].dt.date <= end_date)
        ]

        if dealership != "All" and title != "All":
            filtered_data = filtered_data[
                (filtered_data["dealership_name"] == dealership)
                & (filtered_data["title"] == title)
            ]
        elif dealership != "All":
            filtered_data = filtered_data[
                filtered_data["dealership_name"] == dealership
            ]
        elif title != "All":
            filtered_data = filtered_data[filtered_data["title"] == title]

        return filtered_data

    filtered_data = apply_filters(
        total_views,
        selected_dealership,
        selected_title,
        selected_date_range[0],
        selected_date_range[1],
    )

    # Display key metrics
    st.subheader("🔑 Key Metrics")
    total_employees, total_views = calculate_totals(filtered_data)
    total_dealerships = filtered_data["dealership_name"].nunique()
    avg_views_per_dealership = round(total_views / total_dealerships, 2)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Employees", total_employees)
    with col2:
        st.metric("👀 Total Views (lu)", total_views)
    with col3:
        st.metric("🏢 Total Dealerships", total_dealerships)
    with col4:
        st.metric("📊 Avg. Views per Dealership", avg_views_per_dealership)

    st.write(
        "The key metrics provide a high-level overview of the dealership performance. The total number of employees and total views indicate the overall engagement and reach. The average views per dealership help identify the effectiveness of content consumption across dealerships."
    )

    # Month-on-Month Lu's Completed
    st.subheader("📈 Month-on-Month Lu's Completed")
    line_chart = create_line_chart(filtered_data)
    st.plotly_chart(line_chart)
    st.write(
        "The month-on-month Lu's completed chart shows the trend of content consumption over time. It helps identify patterns, seasonality, and growth in user engagement. By analyzing the trend, you can make informed decisions about resource allocation and marketing strategies."
    )
    top_n = 10
    # Top Dealerships by Total Views
    st.subheader(f"🏆 Top {top_n} Dealerships by Total Views (lu)")
    top_dealerships = get_top_dealerships(filtered_data, top_n)
    st.table(top_dealerships)
    st.write(
        f"The top {top_n} dealerships by total views highlight the best-performing dealerships in terms of content consumption. This information can be used to identify successful practices and strategies employed by these dealerships. You can engage with these dealerships to learn from their experiences and replicate their success in other dealerships."
    )

    # Top Titles by Total Employees
    st.subheader(f"🏅 Top {top_n} Titles by Total Employees")
    top_titles = get_top_titles(filtered_data, top_n)
    st.table(top_titles)
    st.write(
        f"The top {top_n} titles by total employees provide insights into the most common roles or positions within the dealerships. This information can help you tailor your sales approach and communication based on the specific needs and challenges faced by these roles."
    )

    # Distribution of Views across Dealerships

    # Assuming you have already created the 'dealership_views' DataFrame
    dealership_views = (
        filtered_data.groupby("dealership_name")["lu"].sum().reset_index()
    )
    dealership_views["lu"] = dealership_views["lu"] + 0.1
    fig = px.treemap(
        dealership_views,
        path=["dealership_name"],
        values="lu",
        color="lu",
        color_continuous_scale="Viridis",  # Using a more intuitive color scale
        title="Distribution of Views across Dealerships",
        hover_data={"lu": ":.0f"},  # Showing whole numbers for view counts
        branchvalues="total",
    )

    # Adjust layout and formatting
    fig.update_layout(
        font=dict(
            family="Arial", size=14, color="white"
        ),  # Increase font size and use white text
        coloraxis_colorbar=dict(
            title="Total Views (lu)",
            tickvals=[0, 500, 1000, 1500, 2000],  # Customize tick values
            ticktext=["0", "500", "1000", "1500", "2000"],  # Customize tick labels
        ),
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
    )

    # Increase the chart's height
    fig.update_layout(height=800)

    # Simplify dealership names
    fig.update_traces(
        textinfo="label+value",
        textfont=dict(size=12),  # Adjust text size as needed
    )

    # Add a legend
    fig.add_trace(
        px.scatter().data[0],
    )

    st.plotly_chart(fig)
    st.write(
        "The distribution of views across dealerships is presented as a treemap chart. Each rectangle represents a dealership, and the size of the rectangle corresponds to the total views for that dealership. The color gradient indicates the relative magnitude of views, with darker shades representing higher values. This chart provides a compact and visually appealing way to compare content consumption across dealerships, making it easier to identify top-performing dealerships and spot patterns or trends."
    )

    # Distribution of Employees across Titles
    st.subheader("👥 Distribution of Employees across Titles")
    title_employees_bar_chart = create_title_employees_bar_chart(filtered_data)
    st.plotly_chart(title_employees_bar_chart)
    st.write(
        "The distribution of employees across titles provides a breakdown of the workforce composition within the dealerships. It helps you understand the prevalent roles and their relative proportions. This information can assist in targeting your sales efforts and crafting messaging that resonates with specific roles."
    )

    # Content Consumption by Type
    st.subheader("📊 Content Consumption by Type")
    content_consumption_data = filtered_data[
        ["dose_views", "story_views", "guide_views", "capstone_activity_views"]
    ]
    content_consumption_sum = content_consumption_data.sum()
    content_types = [
        "💊 Dose Views",
        "📚 Story Views",
        "📖 Guide Views",
        "🎓 Capstone Activity Views",
    ]

    fig = go.Figure(data=[go.Pie(labels=content_types, values=content_consumption_sum)])
    fig.update_layout(
        title="Content Consumption by Type",
        font=dict(color="#2c3e50"),
    )
    st.plotly_chart(fig)
    st.write(
        "The content consumption by type chart provides a breakdown of the different types of content consumed by users. It helps identify the most popular and engaging content types, allowing you to prioritize and focus on creating more of such content to drive user engagement."
    )

    # Engagement Score Distribution
    st.subheader("📊 Engagement Score Distribution")
    engagement_score_data = px_data[
        ["management_score", "consistency_score", "activity_score", "total_score"]
    ]

    fig = go.Figure()
    for col in engagement_score_data.columns:
        fig.add_trace(go.Box(y=engagement_score_data[col], name=col.capitalize()))

    fig.update_layout(
        title="Engagement Score Distribution",
        xaxis_title="Engagement Score Type",
        yaxis_title="Score",
        font=dict(color="#2c3e50"),
    )
    st.plotly_chart(fig)
    st.write(
        "The engagement score distribution chart shows the spread and variability of different engagement scores (management score, consistency score, activity score, total score) across dealerships. It helps identify the range and median values of each score type, allowing you to benchmark dealership performance and set realistic targets."
    )

    # Correlation Matrix
    st.subheader("📊 Correlation Matrix")
    corr_data = px_data[
        [
            "total_users",
            "mau",
            "dau",
            "management_score",
            "consistency_score",
            "activity_score",
            "total_score",
            "guide_completed",
            "daily_completed",
            "capstone_completed",
            "guide_shared",
        ]
    ]
    corr_matrix = corr_data.corr()

    fig = px.imshow(corr_matrix, text_auto=True, aspect="auto")
    fig.update_layout(
        title="Correlation Matrix",
        font=dict(color="#2c3e50"),
    )
    st.plotly_chart(fig)
    st.write(
        "The correlation matrix visualizes the relationships between different metrics such as total users, MAU, DAU, engagement scores, guide completed, daily completed, capstone completed, and guide shared. It helps identify strong positive or negative correlations between metrics, providing insights into potential drivers of performance. For example, a strong positive correlation between MAU and guide completed suggests that increasing MAU can lead to higher completion rates of guides."
    )

    # Pagination for the dataframe
    page_size = 10
    current_page = st.sidebar.number_input(
        "📄 Page", min_value=1, value=1, step=1, key="pagination"
    )
    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size
    paginated_data = px_data.iloc[start_index:end_index]
    st.write(paginated_data)


@st.cache_data()
def calculate_totals(data):
    total_employees = data["total_employees"].sum()
    total_views = data["lu"].sum()
    return total_employees, total_views


@st.cache_data()
def create_line_chart(data):
    views_monthly = (
        data.groupby(pd.Grouper(key="created_at", freq="M"))["lu"].sum().reset_index()
    )
    views_monthly["created_at"] = views_monthly["created_at"].dt.strftime("%Y-%m")

    fig = go.Figure(
        data=[
            go.Scatter(
                x=views_monthly["created_at"],
                y=views_monthly["lu"],
                mode="lines+markers",
                name="Lu's Completed",
            )
        ]
    )
    fig.update_layout(
        title="Month-on-Month Lu's Completed",
        xaxis_title="Month",
        yaxis_title="Total Lu's",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50"),
    )
    return fig


@st.cache_data()
def get_top_dealerships(data, n):
    top_dealerships = (
        data.groupby("dealership_name")["lu"].sum().nlargest(n).reset_index()
    )
    return top_dealerships


@st.cache_data()
def get_top_titles(data, n):
    top_titles = (
        data.groupby("title")["total_employees"].sum().nlargest(n).reset_index()
    )
    return top_titles


@st.cache_data()
def create_dealership_views_bar_chart(data):
    dealership_views = data.groupby("dealership_name")["lu"].sum().reset_index()
    fig = px.bar(
        dealership_views,
        x="dealership_name",
        y="lu",
        title="Distribution of Views across Dealerships",
        labels={"dealership_name": "Dealership", "lu": "Total Views"},
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50"),
    )
    return fig


@st.cache_data()
def create_title_employees_bar_chart(data):
    title_employees = data.groupby("title")["total_employees"].sum().reset_index()
    fig = px.bar(
        title_employees,
        x="title",
        y="total_employees",
        title="Distribution of Employees across Titles",
        labels={"title": "Title", "total_employees": "Total Employees"},
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50"),
    )
    return fig
