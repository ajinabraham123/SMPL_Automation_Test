import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from queue import PriorityQueue
import random

# Generate SKU Heatmap (Demand Zones)
def generate_heatmap(num_aisles, num_levels):
    return {(aisle, level): random.uniform(1, 3) for aisle in range(num_aisles) for level in range(num_levels)}

# Adjust Travel Time with Traffic and Heatmap
def calculate_adjusted_travel_time(distance_x, distance_z, speed_x, speed_z, accel_x, accel_z, traffic_multiplier, heatmap_factor):
    horizontal_time = 2 * (distance_x / (2 * accel_x)) ** 0.5
    vertical_time = 2 * (distance_z / (2 * accel_z)) ** 0.5
    traffic_multiplier = max(1.0, traffic_multiplier)  # Ensure traffic multiplier is realistic
    heatmap_factor = max(1.0, heatmap_factor)  # Avoid unrealistic low values
    total_time = (horizontal_time + vertical_time) * traffic_multiplier * heatmap_factor
    return total_time

# Core Function: Create Warehouse Graph
def create_warehouse_graph(num_aisles, num_levels, aisle_length, level_height, speed_x, speed_z, accel_x, accel_z, heatmap):
    """
    Creates a graph representation of the warehouse with proper movement rules:
    - No diagonal movements.
    - Horizontal movements between aisles only occur at the first or last level.
    - Vertical movements occur only within the same aisle.
    """
    warehouse_graph = nx.DiGraph()
    fulfillment_zone = "Fulfillment Zone"

    # Add nodes for storage locations
    for aisle in range(num_aisles):
        for level in range(num_levels):
            warehouse_graph.add_node((aisle, level))

    # Add edges for robot movement
    for aisle in range(num_aisles):
        for level in range(num_levels):
            # Allow vertical movement within the same aisle
            if level + 1 < num_levels:
                warehouse_graph.add_edge((aisle, level), (aisle, level + 1), weight=level_height / speed_z)
                warehouse_graph.add_edge((aisle, level + 1), (aisle, level), weight=level_height / speed_z)

            # Allow horizontal movement only at the first or last level
            if aisle + 1 < num_aisles and (level == 0 or level == num_levels - 1):
                warehouse_graph.add_edge((aisle, level), (aisle + 1, level), weight=aisle_length / speed_x)
                warehouse_graph.add_edge((aisle + 1, level), (aisle, level), weight=aisle_length / speed_x)

    # Add fulfillment zone connections
    warehouse_graph.add_node(fulfillment_zone)
    for aisle in range(num_aisles):
        for level in (0, num_levels - 1):  # Allow connections only from level 0 and the topmost level
            heatmap_factor = heatmap.get((aisle, level), 1)
            travel_time = calculate_adjusted_travel_time(
                aisle_length * (aisle / num_aisles),
                level_height * (level / num_levels),
                speed_x, speed_z, accel_x, accel_z, 1.0, heatmap_factor
            )
            warehouse_graph.add_edge((aisle, level), fulfillment_zone, weight=travel_time)
            warehouse_graph.add_edge(fulfillment_zone, (aisle, level), weight=travel_time)

    return warehouse_graph




def batch_orders(warehouse_graph, orders, batch_size=3):
    batched_orders = []
    while orders:
        batch = [orders.pop(0)]
        while len(batch) < batch_size and orders:
            try:
                closest_order = min(
                    orders,
                    key=lambda o: nx.shortest_path_length(warehouse_graph, source=batch[-1], target=o)
                )
                batch.append(closest_order)
                orders.remove(closest_order)
            except nx.NetworkXNoPath:
                st.warning(f"Skipping node {orders[0]} due to no path found.")
                orders.pop(0)  # Remove the problematic order
        batched_orders.append(batch)
    return batched_orders


def validate_graph_connectivity(graph, num_aisles, num_levels, fulfillment_zone="Fulfillment Zone"):
    for aisle in range(num_aisles):
        for level in range(num_levels):
            try:
                # Check if a path exists between this node and the fulfillment zone
                nx.shortest_path_length(graph, source=(aisle, level), target=fulfillment_zone)
            except nx.NetworkXNoPath:
                raise ValueError(f"No path between {(aisle, level)} and '{fulfillment_zone}'. Check graph edges.")



def analyze_robot_overlaps(tracking_data, delay_cost_per_second=0.05):
    total_overlaps = 0
    total_delay = 0
    total_cost = 0
    overlap_summary = {}

    # Loop through the tracking data to extract overlaps and delays
    for entry in tracking_data:
        overlaps = entry.get("overlapping_robots", 0)
        delay = entry.get("delay", 0)
        cost = delay * delay_cost_per_second

        if overlaps > 0:
            total_overlaps += overlaps
            total_delay += delay
            total_cost += cost

            # Track overlaps per aisle
            aisle = entry["storage_node"][0]
            if aisle not in overlap_summary:
                overlap_summary[aisle] = {"Total Overlaps": 0, "Total Delay (s)": 0, "Total Cost ($)": 0}
            overlap_summary[aisle]["Total Overlaps"] += overlaps
            overlap_summary[aisle]["Total Delay (s)"] += delay
            overlap_summary[aisle]["Total Cost ($)"] += cost

    avg_delay = total_delay / total_overlaps if total_overlaps > 0 else 0

    return {
        "total_overlaps": total_overlaps,
        "total_delay": total_delay,
        "average_delay": avg_delay,
        "total_cost": total_cost,
        "overlap_summary": overlap_summary
    }

def validate_path(path, num_levels):
    for i in range(len(path) - 1):
        curr_node, next_node = path[i], path[i + 1]

        # Ignore fulfillment zone as it's not part of the aisle/level grid
        if not isinstance(curr_node, tuple) or not isinstance(next_node, tuple):
            continue

        aisle_diff = abs(curr_node[0] - next_node[0])
        level_diff = abs(curr_node[1] - next_node[1])

        # Rule: No diagonal movements
        if aisle_diff > 0 and level_diff > 0:
            return False

        # Rule: Horizontal movement allowed only at the first or last level
        if aisle_diff > 0 and curr_node[1] not in (0, num_levels - 1):
            return False

        # Rule: Vertical movement allowed only within the same aisle
        if level_diff > 0 and aisle_diff > 0:
            return False

    return True




# Simulate Transactions with Tracking and Overlap Handling
def simulate_transactions_with_tracking(
    warehouse_graph, num_robots, extraction_time, num_transactions, traffic_multiplier, fulfillment_zone="Fulfillment Zone"
):
    """
    Simulates transactions and ensures paths adhere to movement rules.
    """
    total_time = 0
    robot_positions = [fulfillment_zone] * num_robots  # All robots start at the fulfillment zone
    tracking_data = []
    log_issues = []
    robot_assignment_counter = 0

    # Get the number of levels dynamically
    num_levels = max(node[1] for node in warehouse_graph.nodes if isinstance(node, tuple)) + 1

    # Randomly generate orders for the simulation
    orders = random.choices(
        list(node for node in warehouse_graph.nodes if isinstance(node, tuple)),
        k=num_transactions
    )

    if not orders:
        log_issues.append("No orders generated for simulation.")
        return 0, tracking_data, log_issues

    for transaction_id, storage_node in enumerate(orders):
        try:
            chosen_robot = robot_assignment_counter % num_robots  # Assign robot in a round-robin manner
            robot_assignment_counter += 1

            start_node = robot_positions[chosen_robot]

            # Find paths to storage and back to fulfillment zone
            path_to_storage = nx.shortest_path(
                warehouse_graph, source=start_node, target=storage_node, weight="weight"
            )
            path_to_fulfillment = nx.shortest_path(
                warehouse_graph, source=storage_node, target=fulfillment_zone, weight="weight"
            )
            total_path = path_to_storage + path_to_fulfillment

            # Strict validation of the path
            if not validate_path(total_path, num_levels):
                log_issues.append(f"Invalid path detected for Robot {chosen_robot}: {total_path}")
                continue

            # Calculate transaction time
            transaction_time = (
                len(path_to_storage) * traffic_multiplier
                + extraction_time
                + len(path_to_fulfillment) * traffic_multiplier
            )
            total_time += transaction_time

            # Calculate overlaps and dynamic delay
            overlaps = 0
            delay = 0
            if num_robots > 1:
                overlaps = sum(
                    1 for entry in tracking_data if entry["storage_node"] == storage_node
                )
                # Dynamic delay: Factor in traffic multiplier and random variability
                delay = overlaps * random.uniform(1.5, 3.5) * traffic_multiplier

            # Add transaction details to tracking data
            tracking_data.append({
                "transaction_id": transaction_id,
                "robot_id": chosen_robot,
                "start_node": start_node,
                "storage_node": storage_node,
                "travel_time": transaction_time,
                "overlapping_robots": overlaps,
                "delay": delay,
                "total_transaction_time": transaction_time + delay,
            })

            # Update robot position back to fulfillment zone
            robot_positions[chosen_robot] = fulfillment_zone

        except nx.NetworkXNoPath as e:
            log_issues.append(f"No path found for transaction {transaction_id}: {e}")

    # Calculate average transaction time
    avg_transaction_time = total_time / num_transactions if num_transactions > 0 else 0

    return avg_transaction_time, tracking_data, log_issues



# Visual: Robot Tracking
# Improved robot path visualization
def display_robot_tracking(tracking_data, warehouse_graph, fulfillment_zone, num_robots):
    st.subheader("Robot Tracking from Racks to Fulfillment Zone")

    if not tracking_data:
        st.warning("No robot tracking data available for visualization.")
        return

    tracking_fig = go.Figure()

    # Get number of levels dynamically
    num_levels = max(node[1] for node in warehouse_graph.nodes if isinstance(node, tuple)) + 1

    for robot_id in range(num_robots):
        robot_path_x = []
        robot_path_y = []

        for entry in tracking_data:
            if entry["robot_id"] == robot_id:
                start_node = entry["start_node"]
                storage_node = entry["storage_node"]

                try:
                    # Generate paths
                    path_to_storage = nx.shortest_path(
                        warehouse_graph, source=start_node, target=storage_node, weight="weight"
                    )
                    path_to_fulfillment = nx.shortest_path(
                        warehouse_graph, source=storage_node, target=fulfillment_zone, weight="weight"
                    )
                    full_path = path_to_storage + path_to_fulfillment

                    # Strict validation of paths with num_levels
                    if not validate_path(full_path, num_levels):
                        st.warning(f"Invalid path for Robot {robot_id}: {full_path}")
                        continue

                    x_coords, y_coords = zip(*[node for node in full_path if isinstance(node, tuple)])
                    robot_path_x.extend(x_coords)
                    robot_path_y.extend(y_coords)

                except nx.NetworkXNoPath as e:
                    st.warning(f"Path issue for Robot {robot_id}: {e}")
                    continue

        if robot_path_x and robot_path_y:
            tracking_fig.add_trace(go.Scatter(
                x=robot_path_x,
                y=robot_path_y,
                mode="lines+markers",
                name=f"Robot {robot_id}",
                marker=dict(size=6, symbol="circle"),
                line=dict(width=2, dash="solid"),
            ))

    tracking_fig.update_layout(
        title="Robot Tracking from Racks to Fulfillment Zone",
        xaxis=dict(title="Aisle", dtick=1),
        yaxis=dict(title="Level", dtick=1),
        showlegend=True,
        height=600,
        width=900,
    )

    st.plotly_chart(tracking_fig)



# Visual: Delays and Costs Table
def display_delay_table(tracking_data):
    st.subheader("Delays and Costs Due to Overlaps")
    delay_data = pd.DataFrame(tracking_data)
    required_columns = [
        "transaction_id",
        "robot_id",
        "storage_node",
        "overlapping_robots",
        "delay",
        "travel_time",
    ]
    # Check if all required columns exist in the DataFrame
    missing_columns = [col for col in required_columns if col not in delay_data.columns]
    if missing_columns:
        st.error(f"Missing columns in tracking data: {missing_columns}")
    else:
        st.dataframe(delay_data[required_columns])


def analyze_robot_overlaps(tracking_data, delay_cost_per_second=0.05):
    total_overlaps = 0
    total_delay = 0
    total_cost = 0
    overlap_summary = {}

    for entry in tracking_data:
        overlaps = entry.get("overlapping_robots", 0)
        delay = entry.get("delay", 0)
        cost = delay * delay_cost_per_second

        if overlaps > 0:
            total_overlaps += overlaps
            total_delay += delay
            total_cost += cost

            # Track overlaps by aisle
            aisle = entry["storage_node"][0]
            if aisle not in overlap_summary:
                overlap_summary[aisle] = {"Total Overlaps": 0, "Total Delay (s)": 0, "Total Cost ($)": 0}
            overlap_summary[aisle]["Total Overlaps"] += overlaps
            overlap_summary[aisle]["Total Delay (s)"] += delay
            overlap_summary[aisle]["Total Cost ($)"] += cost

    avg_delay = total_delay / total_overlaps if total_overlaps > 0 else 0

    return {
        "total_overlaps": total_overlaps,
        "total_delay": total_delay,
        "average_delay": avg_delay,
        "total_cost": total_cost,
        "overlap_summary": overlap_summary,
    }


def display_overlap_summary(overlap_metrics):
    st.subheader("Robot Overlap Metrics and Costs")

    # Display key metrics
    st.write("### Key Metrics")
    st.metric("Total Overlaps", overlap_metrics.get("total_overlaps", 0))
    st.metric("Total Delay (s)", f"{overlap_metrics.get('total_delay', 0):.2f}")
    st.metric("Average Delay per Overlap (s)", f"{overlap_metrics.get('average_delay', 0):.2f}")
    #st.metric("Total Cost ($)", f"{overlap_metrics.get('total_cost', 0):.2f}")

    # Create a detailed summary table
    overlap_summary = overlap_metrics.get("overlap_summary", {})
    if overlap_summary:
        summary_data = pd.DataFrame.from_dict(overlap_summary, orient="index")
        summary_data.index.name = "Aisle"
        summary_data.reset_index(inplace=True)
        #summary_data.columns = ["Aisle", "Total Overlaps", "Total Delay (s)", "Total Cost ($)"]
        st.dataframe(summary_data)
    else:
        st.warning("No overlaps detected in the simulation.")


def display_overlap_bar_chart(overlap_metrics):
    st.subheader("Overlaps, Delays, and Costs Per Aisle")
    
    # Convert overlap summary to DataFrame
    summary_data = pd.DataFrame.from_dict(overlap_metrics["overlap_summary"], orient="index")
    summary_data.index.name = "Aisle"
    summary_data.reset_index(inplace=True)

    # Check if the required columns exist
    if "Total Overlaps" in summary_data.columns:
        bar_chart = go.Figure()
        bar_chart.add_trace(go.Bar(
            x=summary_data["Aisle"],
            y=summary_data["Total Overlaps"],  # Use the correct column name
            name="Overlaps",
        ))
        bar_chart.update_layout(
            title="Number of Overlaps Per Aisle",
            xaxis_title="Aisle",
            yaxis_title="Number of Overlaps",
            showlegend=False
        )
        st.plotly_chart(bar_chart)
    else:
        st.error("No data available for Overlaps Per Aisle.")



def prioritize_orders(orders):
    """
    Prioritize orders based on urgency or fragility.
    
    Args:
        orders (list): List of orders with attributes like (location, priority).
    
    Returns:
        list: Prioritized list of orders.
    """
    pq = PriorityQueue()
    for order in orders:
        location, priority = order
        pq.put((priority, location))  # Lower priority value indicates higher urgency
    
    # Extract orders in priority order
    prioritized_orders = []
    while not pq.empty():
        _, location = pq.get()
        prioritized_orders.append(location)
    
    return prioritized_orders


def dynamic_rerouting(graph, source, target, blocked_nodes=None):
    """
    Recalculates path dynamically, avoiding blocked nodes.
    
    Args:
        graph (nx.Graph): The warehouse graph.
        source (tuple): Current location of the robot.
        target (tuple): Target location.
        blocked_nodes (list): Nodes to avoid during pathfinding.
    
    Returns:
        list: The recalculated path or None if no path is found.
    """
    try:
        # Create a copy of the graph and remove blocked nodes
        temp_graph = graph.copy()
        if blocked_nodes:
            temp_graph.remove_nodes_from(blocked_nodes)

        # Find the shortest path
        path = nx.shortest_path(temp_graph, source=source, target=target, weight="weight")
        return path
    except nx.NetworkXNoPath:
        st.error(f"Dynamic rerouting failed: No path from {source} to {target} avoiding blocked nodes {blocked_nodes}.")
        return None



def display_heatmap(heatmap, num_aisles, num_levels):
    """
    Visualizes the SKU demand heatmap using Plotly.

    Args:
        heatmap (dict): Dictionary containing the heatmap values for each aisle and level.
        num_aisles (int): Number of aisles in the warehouse.
        num_levels (int): Number of levels in the warehouse.
    """
    st.subheader("SKU Demand Heatmap (By Aisle and Level)")
    
    # Create a bar chart for the heatmap
    heatmap_fig = go.Figure()
    for level in range(num_levels):
        level_heatmap = [
            heatmap.get((aisle, level), 0) for aisle in range(num_aisles)
        ]
        heatmap_fig.add_trace(go.Bar(
            x=[f"Aisle {aisle}" for aisle in range(num_aisles)],
            y=level_heatmap,
            name=f"Level {level}"
        ))

    # Update the layout of the heatmap
    heatmap_fig.update_layout(
        title="SKU Demand Heatmap (By Aisle and Level)",
        xaxis_title="Aisle",
        yaxis_title="Demand Factor",
        barmode="stack",
        legend_title="Levels",
    )

    # Display the heatmap in Streamlit
    st.plotly_chart(heatmap_fig)



def calculate_cost_per_transaction(
    num_robots, upgrade_cost, total_transactions, energy_consumption_per_meter, tracking_data, maintenance_cost
):
    base_cost_per_robot = 20  # Base operating cost per robot
    distance_traveled = sum(entry["travel_time"] for entry in tracking_data)  # Actual distance traveled
    energy_cost = energy_consumption_per_meter * distance_traveled
    system_cost = num_robots * (base_cost_per_robot + upgrade_cost) + energy_cost + maintenance_cost

    # Debugging system cost components
    #st.write(f"Debugging: Base Cost={base_cost_per_robot * num_robots}, Energy Cost={energy_cost}, Maintenance Cost={maintenance_cost}, Distance Traveled={distance_traveled}")

    if total_transactions > 0:
        return system_cost / total_transactions
    else:
        return 0


def main():
    st.title("Spyder Robot Overlap Analysis")

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
    traffic_multiplier = st.sidebar.slider("Traffic Multiplier", 1.0, 2.0, 1.0, 0.1)

    # Parameters for Robot Upgrades
    upgrade_cost = 5 if upgrade_speed else 0
    speed_x = speed_z = 1.5 if upgrade_speed else 1
    accel_x = accel_z = 0.5

    # Add Fulfillment Zone to Warehouse Graph
    fulfillment_zone = "Fulfillment Zone"

    # Heatmap and Graph Generation
    heatmap = generate_heatmap(num_aisles, num_levels)
    try:
        warehouse_graph = create_warehouse_graph(
            num_aisles, num_levels, aisle_length, level_height, speed_x, speed_z, accel_x, accel_z, heatmap
        )
        warehouse_graph.add_node(fulfillment_zone)  # Add fulfillment zone as a node
        validate_graph_connectivity(warehouse_graph, num_aisles, num_levels)

    except ValueError as e:
        st.error(f"Error in creating warehouse graph: {e}")
        return

    # Simulation
    avg_transaction_time, tracking_data, log_issues = simulate_transactions_with_tracking(
        warehouse_graph, num_robots, extraction_time, num_transactions, traffic_multiplier, fulfillment_zone
    )

    # Debugging Total Time
    if avg_transaction_time == 0:
        st.warning("Average transaction time is zero. Ensure transactions and simulation logic are functioning correctly.")

    # Analyze Overlaps
    overlap_metrics = analyze_robot_overlaps(tracking_data)

    # Additional Metrics
    if avg_transaction_time > 0:
        throughput = (3600 / avg_transaction_time) * num_robots  # Transactions per hour
        total_transactions = throughput * 8  # Total transactions in an 8-hour shift
    else:
        throughput = 0
        total_transactions = 0

    # Calculate total distance traveled
    distance_traveled = sum(
        len(nx.shortest_path(warehouse_graph, source=entry["start_node"], target=entry["storage_node"], weight="weight")) +
        len(nx.shortest_path(warehouse_graph, source=entry["storage_node"], target="Fulfillment Zone", weight="weight"))
        for entry in tracking_data
    )

    energy_consumption_per_meter = 0.1  # Assumed energy consumption
    maintenance_cost = num_robots * 2  # Assumed maintenance cost

    cost_per_transaction = calculate_cost_per_transaction(
        num_robots, upgrade_cost, total_transactions, energy_consumption_per_meter, tracking_data, maintenance_cost
    ) if total_transactions > 0 else 0

    # Debugging the cost per transaction
    #st.write(f"Debugging: Cost per Transaction={cost_per_transaction}, Total Transactions={total_transactions}")

    # Display Key Business Metrics
    st.header("Key Business Metrics")
    st.metric("Avg Transaction Time (s)", f"{avg_transaction_time:.2f}" if avg_transaction_time > 0 else "N/A")
    st.metric("Total Transactions (per hour)", f"{throughput:.2f}" if throughput > 0 else "N/A")
    st.metric("Cost per Transaction ($)", f"{cost_per_transaction:.6f}" if cost_per_transaction > 0 else "N/A")

    # Display Visualizations
    display_heatmap(heatmap, num_aisles, num_levels)  # SKU Demand Heatmap
    display_robot_tracking(tracking_data, warehouse_graph, fulfillment_zone, num_robots)  # Robot Tracking
    #display_overlap_summary(overlap_metrics)  # Overlap Metrics Summary
    display_overlap_bar_chart(overlap_metrics)  # Overlaps, Delays, and Costs Per Aisle
    #display_delay_table(tracking_data)  # Delays and Costs Table

    # Log Issues (Optional Display)
    if log_issues:
        with st.expander("Simulation Issues (Click to Expand)"):
            for issue in log_issues:
                st.write(f"- {issue}")



# Run Main
if __name__ == "__main__":
    main()
