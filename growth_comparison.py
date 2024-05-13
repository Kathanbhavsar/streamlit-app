# growth_comparison.py
import streamlit as st
import pandas as pd
import plotly.express as px
import pymysql

"""
-- merge the px with the employees on the dealership_id and get the created_ at and the employee_hash from the employees table
SELECT
    px.*,
    employees.created_at,
    employees.employee_hash
FROM
    partner_experience_report px
JOIN    
    employees
ON  
    px.dealership_id = employees.dealership_id



    """


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

@st.cache_data()
def merged_px_data():
    conn = pymysql.connect(
        host="rocked-staging.csxxh3ec5twj.us-east-2.rds.amazonaws.com",
        user="mysql_dev",
        password="Y1xLx23LoFa9",
        database="rocked-staging",
        port=3306,
    )
    query = """
    SELECT
        px.*,
        employees.created_at as created_at,
        employees.hash
    FROM
        partner_experience_report px
    JOIN    
        employees
    ON  
        px.dealership_id = employees.dealership_id
    """
    employees_data = pd.read_sql(query, conn)
    return employees_data


@st.cache_data(experimental_allow_widgets=True)
def main():
    st.title("Month-on-Month Growth Comparison")

    # Load the data
    px_data = read_px_data()

    px_data_merged = merged_px_data()

    st.write(px_data_merged)

    # Calculate month-on-month growth for each dealership
    px_data["created_at"] = pd.to_datetime(px_data["created_at"])
    px_data["month"] = px_data["created_at"].dt.to_period("M")
    growth_data = (
        px_data.groupby(["dealership_name", "month"])[["total_users", "mau", "dau"]]
        .sum()
        .reset_index()
    )
    growth_data = growth_data.sort_values(["dealership_name", "month"])
    growth_data["total_users_growth"] = growth_data.groupby("dealership_name")[
        "total_users"
    ].pct_change()
    growth_data["mau_growth"] = growth_data.groupby("dealership_name")[
        "mau"
    ].pct_change()
    growth_data["dau_growth"] = growth_data.groupby("dealership_name")[
        "dau"
    ].pct_change()
    growth_data["month_number"] = growth_data.groupby("dealership_name").cumcount()

    # Display month-on-month growth comparison
    st.subheader("Month-on-Month Growth Comparison")
    selected_metric = st.selectbox("Select Metric", ["Total Users", "MAU", "DAU"])
    metric_mapping = {
        "Total Users": "total_users_growth",
        "MAU": "mau_growth",
        "DAU": "dau_growth",
    }
    selected_metric_column = metric_mapping[selected_metric]

    fig = px.line(
        growth_data,
        x="month_number",
        y=selected_metric_column,
        color="dealership_name",
        title=f"Month-on-Month {selected_metric} Growth Comparison",
        labels={
            "month_number": "Month Number",
            selected_metric_column: f"{selected_metric} Growth",
        },
    )
    st.plotly_chart(fig)
