import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pymysql
from urllib.request import urlopen
import json

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
    return px_data

def main():
    st.title("📊 Analysis Dashboard: Unlocking Insights")

    total_views = read_px_data()

    # Sidebar filters
    st.sidebar.title("🔍 Explore the Data")
    st.sidebar.markdown("---")

    # Filter by dealership
    @st.cache_data()
    def get_dealership_options():
        return ["All"] + list(total_views["dealership_name"].unique())

    selected_dealership = st.sidebar.selectbox(
        "🏢 Filter by Dealership", get_dealership_options()
    )

    # Filter by date range
    min_date = total_views["created_at"].min().date()
    max_date = total_views["created_at"].max().date()
    selected_date_range = st.sidebar.date_input(
        "📆 Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Filter by region
    @st.cache_data()
    def get_region_options():
        return ["All"] + list(total_views["region"].unique())

    selected_region = st.sidebar.selectbox("🌍 Filter by Region", get_region_options())

    # Filter by lead pipeline status
    @st.cache_data()
    def get_lead_pipeline_status_options():
        return ["All"] + list(total_views["lead_pipeline_status"].unique())

    selected_lead_pipeline_status = st.sidebar.selectbox(
        "🚥 Filter by Lead Pipeline Status", get_lead_pipeline_status_options()
    )

    st.sidebar.markdown("---")

    # Apply filters
    @st.cache_data()
    def apply_filters(
        data, dealership, start_date, end_date, region, lead_pipeline_status
    ):
        filtered_data = data[
            (data["created_at"].dt.date >= start_date)
            & (data["created_at"].dt.date <= end_date)
        ]

        if dealership != "All":
            filtered_data = filtered_data[
                filtered_data["dealership_name"] == dealership
            ]

        if region != "All":
            filtered_data = filtered_data[filtered_data["region"] == region]

        if lead_pipeline_status != "All":
            filtered_data = filtered_data[
                filtered_data["lead_pipeline_status"] == lead_pipeline_status
            ]

        return filtered_data

    filtered_data = apply_filters(
        total_views,
        selected_dealership,
        selected_date_range[0],
        selected_date_range[1],
        selected_region,
        selected_lead_pipeline_status,
    )

    # Display key metrics
    st.header("🔑 Key Metrics: At a Glance")
    total_mau = filtered_data["mau"].sum()
    total_dau = filtered_data["dau"].sum()
    total_users = filtered_data["total_users"].sum()
    total_guide_completed = filtered_data["guide_completed"].sum()
    total_capstone_completed = filtered_data["capstone_completed"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👥 Total MAU", total_mau, delta_color="inverse")
    col2.metric("👤 Total DAU", total_dau, delta_color="inverse")
    col3.metric("🧑‍🤝‍🧑 Total Users", total_users, delta_color="inverse")
    col4.metric("📖 Total Guide Completed", total_guide_completed, delta_color="inverse")
    col5.metric("🎓 Total Capstone Completed", total_capstone_completed, delta_color="inverse")

    st.markdown("""
                <p style='text-align: center; color: #34495e;'>These key metrics provide a quick overview of user engagement and content consumption across dealerships. They serve as the foundation for understanding the overall performance and identifying areas for improvement.</p>
                """, unsafe_allow_html=True)

    # Display MAU and DAU trend
    st.header("📈 MAU and DAU Trend: Tracking User Activity")
    mau_dau_trend = (
        filtered_data.groupby(pd.Grouper(key="created_at", freq="M"))[["mau", "dau"]]
        .sum()
        .reset_index()
    )
    mau_dau_trend["created_at"] = mau_dau_trend["created_at"].dt.strftime("%Y-%m")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=mau_dau_trend["created_at"],
            y=mau_dau_trend["mau"],
            mode="lines+markers",
            name="MAU",
            line=dict(color="#0072C6", width=3),
            marker=dict(color="#0072C6", size=8),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=mau_dau_trend["created_at"],
            y=mau_dau_trend["dau"],
            mode="lines+markers",
            name="DAU",
            line=dict(color="#EF476F", width=3),
            marker=dict(color="#EF476F", size=8),
        )
    )
    fig.update_layout(
        title="MAU and DAU Trend",
        xaxis_title="Month",
        yaxis_title="Count",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50", size=14),
        xaxis_tickangle=-45,
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12,
        hovermode="x unified",  # Add interactivity
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
                <p style='text-align: center; color: #34495e;'>The Monthly Active Users (MAU) and Daily Active Users (DAU) trend provides valuable insights into user engagement patterns over time. This chart allows you to identify seasonal fluctuations, growth trends, and potential areas for targeted marketing efforts.</p>
                """, unsafe_allow_html=True)

    # Display user engagement scores
    st.header("🏆 User Engagement Scores: Measuring Success")
    engagement_scores = filtered_data[
        [
            "dealership_name",
            "management_score",
            "consistency_score",
            "activity_score",
            "total_score",
        ]
    ]
    engagement_scores_avg = (
        engagement_scores.groupby("dealership_name").mean().reset_index()
    )

    fig = go.Figure()
    for score in [
        "management_score",
        "consistency_score",
        "activity_score",
        "total_score",
    ]:
        fig.add_trace(
            go.Bar(
                x=engagement_scores_avg["dealership_name"],
                y=engagement_scores_avg[score],
                name=score.replace("_", " ").capitalize(),
                marker_color=px.colors.qualitative.Plotly[
                    score.count("_")
                ],  # Assign unique colors
            )
        )
    fig.update_layout(
        title="Average User Engagement Scores",
        xaxis_title="Dealership",
        yaxis_title="Score",
        barmode="group",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50", size=14),
        xaxis_tickangle=-45,
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12,
        hovermode="x unified",  # Add interactivity
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
                <p style='text-align: center; color: #34495e;'>User engagement scores provide a comprehensive evaluation of how effectively dealerships are engaging their employees. These scores encompass various aspects, such as management, consistency, and activity levels, allowing you to identify areas of strength and opportunities for improvement.</p>
                """, unsafe_allow_html=True)

    # Display content consumption
    st.header("📚 Content Consumption: Driving Engagement")
    content_consumption = filtered_data[
        [
            "dealership_name",
            "guide_completed",
            "daily_completed",
            "capstone_completed",
            "guide_shared",
        ]
    ]
    content_consumption_sum = (
        content_consumption.groupby("dealership_name").sum().reset_index()
    )

    fig = go.Figure()
    for content in [
        "guide_completed",
        "daily_completed",
        "capstone_completed",
        "guide_shared",
    ]:
        fig.add_trace(
            go.Bar(
                x=content_consumption_sum["dealership_name"],
                y=content_consumption_sum[content],
                name=content.replace("_", " ").capitalize(),
                marker_color=px.colors.qualitative.Plotly[content.count("_")],
            )
        )
    fig.update_layout(
        title="Content Consumption by Dealership",
        xaxis_title="Dealership",
        yaxis_title="Count",
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50", size=14),
        xaxis_tickangle=-45,
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12,
        hovermode="x unified",  # Add interactivity
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
                <p style='text-align: center; color: #34495e;'>Content consumption is a crucial aspect of user engagement, as it directly influences the effectiveness of your training and learning initiatives. This chart provides insights into the various content types consumed by users across dealerships, helping you identify popular formats and tailor your content strategy accordingly.</p>
                """, unsafe_allow_html=True)

    # Display top users
    st.header("🏆 Top Users: Recognizing Achievers")
    top_users = (
        filtered_data[["dealership_name", "total_users", "mau", "dau"]]
        .groupby("dealership_name")
        .sum()
        .reset_index()
    )
    top_users = top_users.nlargest(10, "total_users")

    fig = px.bar(
        top_users,
        x="dealership_name",
        y="total_users",
        color="dealership_name",
        title="Top 10 Dealerships by Total Users",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(
        xaxis_title="Dealership",
        yaxis_title="Total Users",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50", size=14),
        xaxis_tickangle=-45,
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12,
        hovermode="x unified",  # Add interactivity
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
                <p style='text-align: center; color: #34495e;'>Recognizing top-performing dealerships based on total user engagement is essential for celebrating success and learning from their best practices. This chart highlights the top 10 dealerships with the highest number of total users, enabling you to identify potential role models and leverage their strategies across your organization.</p>
                """, unsafe_allow_html=True)

    # Display user distribution by region
    st.header("🌍 User Distribution by Region: A Geographical Perspective")
    user_distribution = (
        filtered_data.groupby("region")["total_users"].sum().reset_index()
    )

    fig = px.pie(
        user_distribution,
        values="total_users",
        names="region",
        title="User Distribution by Region",
        color_discrete_sequence=px.colors.sequential.Plasma,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=14)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50", size=14),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12),
        ),
        hovermode="closest",  # Add interactivity
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
                <p style='text-align: center; color: #34495e;'>Understanding the geographical distribution of users is crucial for tailoring your marketing and outreach efforts. This pie chart provides a visual representation of user engagement across different regions, enabling you to identify areas with high concentration and potential for growth.</p>
                """, unsafe_allow_html=True)

    # Display user activity heatmap
    st.header("🔥 User Activity Heatmap: Identifying Hotspots")
    user_activity = (
        filtered_data.groupby([pd.Grouper(key="created_at", freq="D"), "region"])[
            "total_users"
        ]
        .sum()
        .reset_index()
    )
    user_activity["created_at"] = user_activity["created_at"].dt.date

    fig = px.density_heatmap(
        user_activity,
        x="created_at",
        y="region",
        z="total_users",
        histfunc="sum",
        title="User Activity Heatmap",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Region",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50", size=14),
        xaxis_tickangle=-45,
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12,
        hovermode="closest",  # Add interactivity
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
                <p style='text-align: center; color: #34495e;'>The user activity heatmap provides a comprehensive view of user engagement across different regions and time periods. This visual representation helps identify hotspots of high activity, enabling you to allocate resources effectively and adapt your strategies to cater to specific regional dynamics.</p>
                """, unsafe_allow_html=True)

    # Display user engagement by lead pipeline status
    st.header("🚥 User Engagement by Lead Pipeline Status: Tracking Progress")
    engagement_by_lead_pipeline = (
        filtered_data.groupby("lead_pipeline_status")[
            ["management_score", "consistency_score", "activity_score", "total_score"]
        ]
        .mean()
        .reset_index()
    )

    fig = go.Figure()
    for score in [
        "management_score",
        "consistency_score",
        "activity_score",
        "total_score",
    ]:
        fig.add_trace(
            go.Bar(
                x=engagement_by_lead_pipeline["lead_pipeline_status"],
                y=engagement_by_lead_pipeline[score],
                name=score.replace("_", " ").capitalize(),
                marker_color=px.colors.qualitative.Plotly[score.count("_")],
            )
        )
    fig.update_layout(
        title="User Engagement by Lead Pipeline Status",
        xaxis_title="Lead Pipeline Status",
        yaxis_title="Score",
        barmode="group",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50", size=14),
        xaxis_tickangle=-45,
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12,
        hovermode="x unified",  # Add interactivity
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
                <p style='text-align: center; color: #34495e;'>Analyzing user engagement metrics across different lead pipeline stages provides valuable insights into the effectiveness of your sales and marketing efforts. This chart allows you to track progress, identify potential bottlenecks, and optimize your strategies to ensure a seamless journey for your customers.</p>
                """, unsafe_allow_html=True)

    # Display content consumption by lead pipeline status
    st.header("📚 Content Consumption by Lead Pipeline Status: Tailoring Your Approach")
    content_by_lead_pipeline = (
        filtered_data.groupby("lead_pipeline_status")[
            ["guide_completed", "daily_completed", "capstone_completed", "guide_shared"]
        ]
        .sum()
        .reset_index()
    )

    fig = go.Figure()
    for content in [
        "guide_completed",
        "daily_completed",
        "capstone_completed",
        "guide_shared",
    ]:
        fig.add_trace(
            go.Bar(
                x=content_by_lead_pipeline["lead_pipeline_status"],
                y=content_by_lead_pipeline[content],
                name=content.replace("_", " ").capitalize(),
                marker_color=px.colors.qualitative.Plotly[content.count("_")],
            )
        )
    fig.update_layout(
        title="Content Consumption by Lead Pipeline Status",
        xaxis_title="Lead Pipeline Status",
        yaxis_title="Count",
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50", size=14),
        xaxis_tickangle=-45,
        xaxis_tickfont_size=12,
        yaxis_tickfont_size=12,
        hovermode="x unified",  # Add interactivity
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
                <p style='text-align: center; color: #34495e;'>Understanding content consumption patterns across different lead pipeline stages is crucial for tailoring your content strategy and ensuring effective knowledge transfer. This chart provides insights into the types of content resonating with users at various stages, empowering you to optimize your content offerings and enhance engagement.</p>
                """, unsafe_allow_html=True)

    # Pagination for the dataframe
    st.header("📊 Explore the Data")
    st.markdown("""
                <p style='text-align: center; color: #34495e;'>Dive deeper into the data by exploring the raw dataset. Use the pagination controls to navigate through the records.</p>
                """, unsafe_allow_html=True)

    page_size = 10
    current_page = st.sidebar.number_input(
        "📄 Page", min_value=1, value=1, step=1, key="pagination"
    )
    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size
    paginated_data = total_views.iloc[start_index:end_index]
    st.write(paginated_data)
