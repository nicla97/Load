import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

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
        required_columns = ["Player Tag", "Session Date", "Total Player Load", "Tag ID"]
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
def aggregate_data(df, group_by):
    return df.groupby(group_by).agg({
        "Total Player Load": "sum",
        "Explosive [seconds]": "sum",
        "Explosive Actions": "sum",
        "Explosive Movements": "sum",
        "Very High [seconds]": "sum",
        "Very High Actions": "sum",
    }).reset_index().round(2)

# Function to filter data based on selection
def filter_data(data, date_filter, player_filter, drill_filter, session_filter):
    filtered_data = data.copy()

    # Apply filters
    if date_filter and "All" not in date_filter:
        filtered_data = filtered_data[filtered_data["Session Date"].dt.strftime("%Y-%m-%d").isin(date_filter)]
    if player_filter and "All" not in player_filter:
        filtered_data = filtered_data[filtered_data["Player Tag"].isin(player_filter)]
    if drill_filter and "All" not in drill_filter and "Drill Name" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["Drill Name"].isin(drill_filter)]
    if session_filter and "All" not in session_filter and "Session Name" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["Session Name"].isin(session_filter)]

    return filtered_data

# Function to plot data dynamically
def plot_data(data, x_axis, y_axis, chart_type, color, aggregated):
    st.subheader(f"{chart_type} Plot: {x_axis} vs {y_axis}")

    if x_axis in data.columns and y_axis in data.columns and not data.empty:
        fig, ax = plt.subplots(figsize=(20, 6))
        
        
        # Adjust x-axis labels based on aggregation state
        if aggregated:
            data["x_label"] = data["Tag ID"].astype(str)  # Only show Tag ID
            ax.set_xlabel("Tag ID")
        else:
            data["x_label"] = data["Tag ID"].astype(str) + " | " + data["Session Date"].dt.strftime("%Y-%m-%d")
            ax.set_xlabel("Tag ID | Session Date")


        if chart_type == "Bar":
            ax.bar(data["x_label"], data[y_axis], color=color)
        elif chart_type == "Line":
            ax.plot(data["x_label"], data[y_axis], marker="o", linestyle="-", color=color)
        elif chart_type == "Scatter":
            ax.scatter(data["x_label"], data[y_axis], color=color)

        if aggregated:
            ax.set_xlabel("Tag ID")
            ax.tick_params(axis='x', rotation=0)
        else:
            ax.set_xlabel("Tag ID | Session Date")
            ax.tick_params(axis='x', rotation=90)
        ax.set_ylabel(y_axis)

        st.pyplot(fig)
    else:
        st.warning("No data available for plotting.")

# Process file if uploaded
if uploaded_file is not None:
    data = process_file(uploaded_file)
    if data is not None:
        # ---- FILTERS FOR TABLE & PLOTTING ----
        st.sidebar.header("Filter Options")

        date_filter = st.sidebar.multiselect("Select Session Date", ["All"] + sorted(data["Session Date"].dt.strftime("%Y-%m-%d").unique().tolist()), default=["All"])
        player_filter = st.sidebar.multiselect("Select Player(s)", ["All"] + sorted(data["Player Tag"].unique().tolist()), default=["All"])
        drill_filter = st.sidebar.multiselect("Select Drill(s)", ["All"] + sorted(data["Drill Name"].unique().tolist()) if "Drill Name" in data.columns else ["All"], default=["All"])
        session_filter = st.sidebar.multiselect("Select Session(s)", ["All"] + sorted(data["Session Name"].unique().tolist()) if "Session Name" in data.columns else ["All"], default=["All"])

        # Apply filtering
        filtered_data = filter_data(data, date_filter, player_filter, drill_filter, session_filter)

        # ---- TOGGLE FOR AGGREGATION ----
        aggregate_toggle = st.sidebar.checkbox("Show Aggregated Data", value=True)
        
        # Aggregation logic
        if aggregate_toggle:
            grouped_data = aggregate_data(filtered_data, ["Player Tag", "Session Date", "Tag ID"])
        else:
            grouped_data = filtered_data.copy()

        # ---- DISPLAY TABLE ----
        st.subheader("Data Table")
        st.dataframe(grouped_data)

        # ---- PLOT SETTINGS ----
        st.sidebar.header("Plot Settings")

        chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar", "Line", "Scatter"])
        y_axis = st.sidebar.selectbox("Y-Axis", [col for col in grouped_data.columns if col not in ["Player Tag", "Session Date", "Tag ID", "Drill Name", "Session Name", "MD", "Load/Min", "Duration", "Start Timestamp", "End Timestamp"]])
        color = st.sidebar.text_input("Enter Hex Color Code", value="#007bff")  # Default blue

        # ---- GENERATE PLOT ----
        plot_data(grouped_data, "Tag ID", y_axis, chart_type, color, aggregate_toggle)
