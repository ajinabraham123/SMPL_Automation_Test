import networkx as nx
import random
import pandas as pd

# Step 1: Create Warehouse Graph
def create_warehouse_graph(num_aisles, num_levels, aisle_length, level_height, speed_x, speed_z, accel_x, accel_z):
    warehouse_graph = nx.DiGraph()
    
    # Add nodes for storage locations and a retrieval point
    for aisle in range(num_aisles):
        for level in range(num_levels):
            warehouse_graph.add_node((aisle, level))
    warehouse_graph.add_node("Retrieval")
    
    # Add edges with travel time weights
    for aisle in range(num_aisles):
        for level in range(num_levels):
            travel_time = calculate_travel_time(
                aisle_length * (aisle / num_aisles),  # horizontal distance
                level_height * (level / num_levels),  # vertical distance
                speed_x, speed_z, accel_x, accel_z
            )
            warehouse_graph.add_edge((aisle, level), "Retrieval", weight=travel_time)
    
    return warehouse_graph

# Step 2: Travel Time Calculation
def calculate_travel_time(distance_x, distance_z, speed_x, speed_z, accel_x, accel_z):
    horizontal_time = 2 * (distance_x / (2 * accel_x)) ** 0.5
    vertical_time = 2 * (distance_z / (2 * accel_z)) ** 0.5
    return horizontal_time + vertical_time

# Step 3: Metrics Calculation
def calculate_transaction_time(travel_time, extraction_time):
    return travel_time + extraction_time

def calculate_cost_per_transaction(num_robots, upgrade_cost, total_transactions):
    base_cost_per_robot = 20
    system_cost = num_robots * (base_cost_per_robot + upgrade_cost)
    return system_cost / total_transactions

# Step 4: Simulate Transactions
def simulate_transactions(warehouse_graph, num_robots, extraction_time, num_transactions):
    total_time = 0
    for _ in range(num_transactions):
        # Randomly pick a storage location
        storage_node = random.choice(list(warehouse_graph.nodes - {"Retrieval"}))
        travel_time = nx.shortest_path_length(warehouse_graph, source=storage_node, target="Retrieval", weight="weight")
        transaction_time = calculate_transaction_time(travel_time, extraction_time)
        total_time += transaction_time
    return total_time / num_transactions  # Average transaction time

# Step 5: Test Multiple Cases
def run_cases(warehouse_graph, scenarios):
    results = []
    for case_id, case in enumerate(scenarios, 1):
        print(f"Running Case {case_id}: {case}")
        num_robots = case['num_robots']
        extraction_time = case['extraction_time']
        num_transactions = case['num_transactions']
        
        # Upgrade cost
        upgrade_cost = 5 * (extraction_time < 2)  # $5 for faster extraction
        
        # Simulate average transaction time
        avg_transaction_time = simulate_transactions(warehouse_graph, num_robots, extraction_time, num_transactions)
        
        # Throughput and total transactions
        throughput = 3600 / avg_transaction_time  # transactions per hour
        total_transactions = throughput * 8  # assume 8-hour shift
        
        # Cost per transaction
        cost_per_transaction = calculate_cost_per_transaction(num_robots, upgrade_cost, total_transactions)
        
        results.append({
            "case_id": case_id,
            "num_robots": num_robots,
            "extraction_time": extraction_time,
            "num_transactions": num_transactions,
            "cost_per_transaction": cost_per_transaction,
            "avg_transaction_time": avg_transaction_time
        })
    
    return results

# Main Execution
if __name__ == "__main__":
    # Warehouse Parameters
    num_aisles = 10
    num_levels = 5
    aisle_length = 30  # meters
    level_height = 5  # meters
    
    # Robot Parameters
    speed_x = speed_z = 1  # m/s
    accel_x = accel_z = 0.5  # m/s^2
    
    # Simulation Parameters
    num_robots_range = range(1, 6)  # Test 1 to 5 robots
    extraction_times = [2, 1]  # Test base and upgraded extraction times
    num_transactions = 1000  # Simulate 1000 transactions
    
    # Create Warehouse Graph
    warehouse_graph = create_warehouse_graph(num_aisles, num_levels, aisle_length, level_height, speed_x, speed_z, accel_x, accel_z)
    
    # Define Scenarios
    scenarios = [
        {"num_robots": 1, "extraction_time": 2, "num_transactions": 1000},  # Base Case
        {"num_robots": 2, "extraction_time": 2, "num_transactions": 1000},  # Increasing Robots
        {"num_robots": 3, "extraction_time": 2, "num_transactions": 1000},  # Increasing Robots
        {"num_robots": 1, "extraction_time": 1, "num_transactions": 1000},  # Upgraded Extraction Time
        {"num_robots": 1, "extraction_time": 2, "num_transactions": 5000},  # Higher Workload
        {"num_robots": 2, "extraction_time": 2, "num_transactions": 5000},  # Higher Workload with More Robots
        {"num_robots": 2, "extraction_time": 1, "num_transactions": 5000},  # Combining Robots and Upgrades
        {"num_robots": 3, "extraction_time": 1, "num_transactions": 5000},  # Combining Robots and Upgrades
    ]
    
    # Run the scenarios
    results = run_cases(warehouse_graph, scenarios)
    
    # Output results in tabular form
    results_df = pd.DataFrame(results)
    print(results_df)
