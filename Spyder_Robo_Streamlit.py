import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import random

# Core Function: Create Warehouse Graph
def create_warehouse_graph(num_aisles, num_levels, aisle_length, level_height, speed_x, speed_z, accel_x, accel_z):
    warehouse_graph = nx.DiGraph()
    for aisle in range(num_aisles):
        for level in range(num_levels):
            warehouse_graph.add_node((aisle, level))
    warehouse_graph.add_node("Retrieval")
    for aisle in range(num_aisles):
        for level in range(num_levels):
            travel_time = calculate_travel_time(
                aisle_length * (aisle / num_aisles),
                level_height * (level / num_levels),
                speed_x, speed_z, accel_x, accel_z
            )
            warehouse_graph.add_edge((aisle, level), "Retrieval", weight=travel_time)
    return warehouse_graph

# Core Function: Travel Time Calculation
def calculate_travel_time(distance_x, distance_z, speed_x, speed_z, accel_x, accel_z):
    horizontal_time = 2 * (distance_x / (2 * accel_x)) ** 0.5
    vertical_time = 2 * (distance_z / (2 * accel_z)) ** 0.5
    return horizontal_time + vertical_time

# Function: Simulate Transactions with Queueing
def simulate_transactions_with_queueing(warehouse_graph, num_robots, extraction_time, num_transactions):
    total_time = 0
    utilization = {node: 0 for node in warehouse_graph.nodes}
    robot_queue = [0] * num_robots
    for _ in range(num_transactions):
        storage_node = random.choice(list(warehouse_graph.nodes - {"Retrieval"}))
        travel_time = nx.shortest_path_length(warehouse_graph, source=storage_node, target="Retrieval", weight="weight")
        next_available_robot = min(robot_queue)
        delay = max(next_available_robot - total_time, 0)
        total_time += travel_time + extraction_time + delay
        utilization[storage_node] += 1
        robot_queue[robot_queue.index(next_available_robot)] = total_time
    avg_transaction_time = total_time / num_transactions
    return avg_transaction_time, utilization

# Cost per Transaction Calculation
def calculate_cost_per_transaction(num_robots, upgrade_cost, total_transactions):
    base_cost_per_robot = 20
    system_cost = num_robots * (base_cost_per_robot + upgrade_cost)
    return system_cost / total_transactions

# Dynamic Workload Simulation
def dynamic_workload_simulation(warehouse_graph, num_robots, extraction_time, workload_rates, upgrade_cost):
    results = []
    for workload_rate in workload_rates:
        avg_time, _ = simulate_transactions_with_queueing(
            warehouse_graph, num_robots, extraction_time, workload_rate
        )
        throughput = (3600 / avg_time) * num_robots
        cost_per_transaction = calculate_cost_per_transaction(num_robots, upgrade_cost, throughput * 8)
        results.append({
            "Workload Rate": workload_rate,
            "Throughput": throughput,
            "Avg Time": avg_time,
            "Cost per Transaction": cost_per_transaction
        })
    return pd.DataFrame(results)

# Optimal Configuration Suggestion
def suggest_optimal_configuration(results):
    optimal_config = results.loc[results["Cost per Transaction"].idxmin()]
    return optimal_config

# Streamlit App
st.title("Spyder Robot Optimization Tool")

# Sidebar Inputs
st.sidebar.header("Warehouse Parameters")
num_aisles = st.sidebar.slider("Number of Aisles", 10, 30, 10)
num_levels = st.sidebar.slider("Number of Levels", 3, 10, 5)
aisle_length = st.sidebar.slider("Aisle Length (m)", 30, 90, 30)
level_height = st.sidebar.slider("Level Height (m)", 5, 15, 5)
num_transactions = st.sidebar.number_input("Transactions per Hour", value=1000, step=100)

st.sidebar.header("Robot Parameters")
num_robots = st.sidebar.slider("Number of Robots", 1, 10, 1)
extraction_time = st.sidebar.selectbox("Extraction Time (s)", [2, 1])
upgrade_speed = st.sidebar.checkbox("Upgrade Speed (Add $5 per Robot)")

st.sidebar.header("Dynamic Workload Simulation")
workload_rates = st.sidebar.multiselect(
    "Workload Rates (Transactions per Hour)", [500, 1000, 1500, 2000], default=[1000, 1500]
)

# Robot Parameters
upgrade_cost = 5 if upgrade_speed else 0
speed_x = speed_z = 1.5 if upgrade_speed else 1
accel_x = accel_z = 0.5

# Create Warehouse Graph and Simulate Transactions
warehouse_graph = create_warehouse_graph(num_aisles, num_levels, aisle_length, level_height, speed_x, speed_z, accel_x, accel_z)
avg_transaction_time, utilization = simulate_transactions_with_queueing(
    warehouse_graph, num_robots, extraction_time, num_transactions
)
throughput = (3600 / avg_transaction_time) * num_robots
total_transactions = throughput * 8
cost_per_transaction = calculate_cost_per_transaction(num_robots, upgrade_cost, total_transactions)

# Dynamic Workload Simulation
workload_results = dynamic_workload_simulation(
    warehouse_graph, num_robots, extraction_time, workload_rates, upgrade_cost
)

# Optimal Configuration Suggestion
optimal_config = suggest_optimal_configuration(workload_results)

# KPI Dashboard
st.header("Key Business Metrics")
st.metric("Cost per Transaction ($)", f"{cost_per_transaction:.6f}")
st.metric("Total Cost ($)", f"{num_robots * (20 + upgrade_cost)}")
st.metric("Avg Transaction Time (s)", f"{avg_transaction_time:.2f}")
st.metric("Throughput (tx/hr)", f"{throughput:.2f}")
st.metric("Robots", f"{num_robots}")

# Queueing Visualization
st.subheader("Robot Utilization and Queueing Delays")
queue_fig = go.Figure()
for level in range(num_levels):
    level_utilization = [
        utilization.get((aisle, level), 0) for aisle in range(num_aisles)
    ]
    queue_fig.add_trace(go.Bar(
        x=[f"Aisle {aisle}" for aisle in range(num_aisles)],
        y=level_utilization,
        name=f"Level {level}"
    ))
queue_fig.update_layout(
    title="Queueing and Utilization per Aisle and Level",
    xaxis_title="Aisle",
    yaxis_title="Utilization Count",
    barmode="stack"
)
st.plotly_chart(queue_fig)

# Dynamic Workload Simulation Visualization
#st.subheader("Dynamic Workload Simulation")
workload_fig = go.Figure()
workload_fig.add_trace(go.Scatter(
    x=workload_results["Workload Rate"],
    y=workload_results["Throughput"],
    mode="lines+markers",
    name="Throughput"
))
workload_fig.add_trace(go.Scatter(
    x=workload_results["Workload Rate"],
    y=workload_results["Cost per Transaction"],
    mode="lines+markers",
    name="Cost per Transaction"
))
workload_fig.update_layout(
    title="Performance Under Workload Variations",
    xaxis_title="Workload Rate (Transactions per Hour)",
    yaxis_title="Metrics",
    legend_title="Metrics"
)
#st.plotly_chart(workload_fig)

# Optimal Configuration Visualization
st.subheader("Optimal Configuration Recommendation")
optimal_fig = go.Figure()
optimal_fig.add_trace(go.Scatter(
    x=workload_results["Throughput"],
    y=workload_results["Cost per Transaction"],
    mode="markers",
    marker=dict(
        size=12,
        color=workload_results["Workload Rate"],
        colorscale="Viridis",
        showscale=True
    ),
    name="Configurations"
))
optimal_fig.add_trace(go.Scatter(
    x=[optimal_config["Throughput"]],
    y=[optimal_config["Cost per Transaction"]],
    mode="markers+text",
    marker=dict(size=16, color="red", symbol="star"),
    text=["Optimal Config"],
    name="Optimal Config"
))
optimal_fig.update_layout(
    title="Cost vs Throughput: Optimal Configuration",
    xaxis_title="Throughput (Transactions per Hour)",
    yaxis_title="Cost per Transaction ($)"
)
st.plotly_chart(optimal_fig)

# Configuration Table
st.subheader("Configuration Comparison")
st.dataframe(workload_results)
