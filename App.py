import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Streamlit UI
st.set_page_config(layout="wide", page_title="Player Load Analysis")
st.title("Player Load Analysis Dashboard")
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

data = pd.DataFrame()

# Function to process uploaded file
def process_file(uploaded_file):
    global data
    try:
        data = pd.read_excel(uploaded_file)
        required_columns = ["Player Tag", "Session Date", "Total Player Load"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            st.error(f"Missing columns: {missing_columns}")
            return None

        data["Session Date"] = pd.to_datetime(data["Session Date"], dayfirst=True)
        return data

    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

# Function to aggregate data
def aggregate_data(df):
    return df.groupby("Player Tag").agg({
        "Total Player Load": "sum",
        "Explosive [seconds]": "sum",
        "Explosive Actions": "sum",
        "Explosive Movements": "sum",
        "Very High [seconds]": "sum",
        "Very High Actions": "sum",
    }).reset_index().round(2)


# Function to filter data based on selection
def filter_data(data, time_span, date_filter, player_filter, drill_filter, session_filter):
    filtered_data = data.copy()
    today = datetime.today()

    # Apply time span filter
    if time_span != "All":
        if time_span == "Last Week":
            start_date = today - timedelta(weeks=1)
        elif time_span == "Last Two Weeks":
            start_date = today - timedelta(weeks=2)
        elif time_span == "Last Month":
            start_date = today - timedelta(days=30)

        filtered_data = filtered_data[filtered_data["Session Date"] >= start_date]

    # Apply other filters
    if date_filter != "All":
        filtered_data = filtered_data[filtered_data["Session Date"].dt.strftime("%Y-%m-%d") == date_filter]
    if player_filter != "All":
        filtered_data = filtered_data[filtered_data["Player Tag"] == player_filter]
    if drill_filter != "All" and "Drill Name" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["Drill Name"] == drill_filter]
    if session_filter != "All" and "Session Name" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["Session Name"] == session_filter]

    return filtered_data

# Function to plot data dynamically
def plot_data(data, y_axis, chart_type, color):
    st.subheader(f"{chart_type} Plot: {y_axis}")

    if "Player Tag" in data.columns and y_axis in data.columns and not data.empty:
        fig, ax = plt.subplots(figsize=(10, 5))

        if chart_type == "Bar":
            ax.bar(data["Player Tag"], data[y_axis], color=color)
        elif chart_type == "Line":
            ax.plot(data["Player Tag"], data[y_axis], marker="o", linestyle="-", color=color)
        elif chart_type == "Scatter":
            ax.scatter(data["Player Tag"], data[y_axis], color=color)

        ax.set_xlabel("Player Tag")
        ax.set_ylabel(y_axis)
        ax.tick_params(axis='x', rotation=90)

        st.pyplot(fig)
    else:
        st.warning("No data available for plotting.")

# Process file if uploaded
if uploaded_file is not None:
    data = process_file(uploaded_file)
    if data is not None:
        with st.sidebar:
            st.header("Filter Options")

            # Update filter values based on uploaded data
            time_span_options = ["All", "Last Week", "Last Two Weeks", "Last Month"]
            time_span_filter = st.selectbox("Select Time Span", time_span_options, index=0)

            date_filter = st.selectbox("Session Date", ["All"] + sorted(data["Session Date"].dt.strftime("%Y-%m-%d").unique().tolist()))
            player_filter = st.selectbox("Player Tag", ["All"] + sorted(data["Player Tag"].unique().tolist()))
            drill_filter = st.selectbox("Drill Name", ["All"] + sorted(data["Drill Name"].unique().tolist()) if "Drill Name" in data.columns else ["All"])
            session_filter = st.selectbox("Session Name", ["All"] + sorted(data["Session Name"].unique().tolist()) if "Session Name" in data.columns else ["All"])

        # Apply filtering
        filtered_data = filter_data(data, time_span_filter, date_filter, player_filter, drill_filter, session_filter)
        aggregated_data = aggregate_data(filtered_data)

        # Ensure only numerical columns (excluding "Player Tag") are selectable for plotting
        plot_columns = [col for col in aggregated_data.columns if col != "Player Tag"]
        
        with st.sidebar:
            st.header("Plot Settings")
            chart_type = st.selectbox("Select Chart Type", ["Bar", "Line", "Scatter"])
            y_axis = st.selectbox("Y-Axis", plot_columns)
            color = st.text_input("Enter Hex Color Code", value="#007bff")  # Default blue

        st.subheader("Filtered Table")
        st.dataframe(aggregated_data)

        plot_data(aggregated_data, y_axis, chart_type, color)
