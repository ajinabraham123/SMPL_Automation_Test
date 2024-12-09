# Spyder Robot Overlap Analysis

This repository contains a simulation and analysis tool to model warehouse robot movements, analyze overlaps, and optimize transactions. It uses **Streamlit** for interactive visualization, **NetworkX** for graph-based pathfinding, and **Plotly** for data visualization.

---

## Table of Contents
1. [Steps to run the code](#steps)
1. [Overview](#overview)
2. [Mathematical Formulations](#mathematical-formulations)
    - [SKU Heatmap](#sku-heatmap)
    - [Travel Time Calculation](#travel-time-calculation)
    - [Warehouse Graph Representation](#warehouse-graph-representation)
    - [Transaction Time](#transaction-time)
    - [Cost per Transaction](#cost-per-transaction)
3. [Code Logic and Design](#code-logic-and-design)
    - [Graph Creation](#graph-creation)
    - [Simulation Workflow](#simulation-workflow)
    - [Overlap Analysis](#overlap-analysis)
4. [Visualizations](#visualizations)
5. [Usage Instructions](#usage-instructions)

---
## Steps to run the code - https://docs.google.com/document/d/1b5R7cknjQLW76Sl9WbwF-XivrzZ2Ku4-Avc3jBe_Mjw/edit?tab=t.2997js9j91rz

1. Set Up the Environment on VSCode
1. Create a virtual environment:
```bash
python3 -m venv env
```

2. Activate the virtual environment:
For macOS/Linux:
```bash
source env/bin/activate
```

For Windows:
```bash
.\env\Scripts\activate
```


2. Install Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit Application

Start the Streamlit app:
```bash
streamlit run Spyder_Robo_Streamlit.py
```

*Open your browser and navigate to:
```bash
http://localhost:8501
```

Run Using Docker
1. Build the Docker Image
Ensure Docker is installed and running on your machine.
Build the Docker image:
```bash
docker build -t smpl_automation_test .
```

2. Run the Docker Container
Start the Docker container:
```bash
docker run -p 8501:8501 smpl_automation_test
```

*Access the application in your browser at:
```bash
http://localhost:8501
```


## Overview

This project simulates robot movements in a warehouse, focusing on:
- Minimizing overlaps and delays.
- Optimizing robot paths.
- Visualizing demand heatmaps and robot tracking.
- Providing key business metrics such as transaction cost, throughput, and overlaps.

---

## Mathematical Formulations

### SKU Heatmap
The SKU demand heatmap assigns a random demand factor to each storage node:
$$
\text{Heatmap Factor} = \text{random.uniform}(1, 3)
$$

This factor influences travel times, simulating varying demands across storage zones.

---

### Travel Time Calculation
Robot travel time is calculated based on horizontal and vertical distances, speeds, accelerations, traffic, and demand factors:

- **Horizontal Time**:
$$
t_h = 2 \sqrt{\frac{\text{distance}_x}{2 \cdot \text{accel}_x}}
$$

- **Vertical Time**:
$$
t_v = 2 \sqrt{\frac{\text{distance}_z}{2 \cdot \text{accel}_z}}
$$

- **Total Travel Time**:
$$
t_{\text{total}} = (t_h + t_v) \cdot \text{traffic\_multiplier} \cdot \text{heatmap\_factor}
$$

---

### Warehouse Graph Representation
The warehouse is modeled as a **directed graph (DiGraph)**:
- **Nodes**: Represent storage locations and a "Fulfillment Zone".
- **Edges**:
  - Vertical movement (within aisles).
  - Horizontal movement (at the first or last levels).
  - Connections to the "Fulfillment Zone".

---

### Transaction Time
The total time for a transaction includes travel times and extraction delays:
$$
t_{\text{transaction}} = t_{\text{to\_storage}} + t_{\text{extraction}} + t_{\text{to\_fulfillment}}
$$

Where:
- \( t_{\text{to\_storage}} \): Time to reach the storage node.
- \( t_{\text{extraction}} \): Time to extract an item.
- \( t_{\text{to\_fulfillment}} \): Time to return to the fulfillment zone.

---

### Cost per Transaction
The cost of each transaction considers:

1. **Energy Cost**:
$$
\text{Energy Cost} = \text{distance traveled} \cdot \text{energy\_consumption\_per\_meter}
$$

2. **Maintenance Cost**:
$$
\text{Maintenance Cost} = \text{num\_robots} \cdot \text{fixed\_maintenance\_cost}
$$

3. **System Cost**:
$$
\text{System Cost} = \text{Base Cost} + \text{Upgrade Cost} + \text{Energy Cost} + \text{Maintenance Cost}
$$

4. **Cost per Transaction**:
$$
\text{Cost per Transaction} = \frac{\text{System Cost}}{\text{Total Transactions}}
$$
---

## Code Logic and Design : https://docs.google.com/document/d/1b5R7cknjQLW76Sl9WbwF-XivrzZ2Ku4-Avc3jBe_Mjw/edit?tab=t.0#heading=h.rhswl83t4ndo

### Graph Creation
The function `create_warehouse_graph` models the warehouse:
- Adds nodes for storage locations.
- Creates directed edges for robot movement rules:
  - Vertical edges between levels within aisles.
  - Horizontal edges only at specific levels (first or last).
  - Links to the "Fulfillment Zone".

### Simulation Workflow
The `simulate_transactions_with_tracking` function performs:
1. **Transaction Assignment**:
    - Assigns robots to tasks using a round-robin method.
2. **Pathfinding**:
    - Calculates paths to storage nodes and back to the fulfillment zone using NetworkX.
3. **Validation**:
    - Ensures paths adhere to movement rules (no diagonal or invalid moves).
4. **Metrics Calculation**:
    - Tracks overlaps, delays, and transaction times.

### Overlap Analysis
The function `analyze_robot_overlaps` calculates:
- **Total Overlaps**: Instances of robots accessing the same storage node.
- **Total Delay**: Time penalties due to overlaps.
- **Average Delay**: Mean delay per overlap.

---

## Visualizations

1. **SKU Demand Heatmap**:
    - Displays the demand factors across aisles and levels using a stacked bar chart.

2. **Robot Tracking**:
    - Visualizes robot paths from storage nodes to the fulfillment zone.
    - Highlights invalid movements or pathfinding issues.

3. **Overlap Metrics**:
    - Summarizes overlaps, delays, and costs per aisle.

---

## Usage Instructions

### Prerequisites
Install the required packages:
```bash
pip install streamlit pandas networkx plotly
```



# Analysis Based on Code and Questions

## How does the topology of the system impact our metric?

The topology of the system, defined by the number of aisles, levels, and the distances between nodes, significantly impacts metrics like transaction time, overlaps, and cost per transaction. For instance, increasing the number of aisles or levels introduces more nodes and potential pathways, which can either reduce or increase transaction times based on the demand heatmap and traffic multiplier.

The constraints, such as movement only at certain levels or avoiding diagonal movement, further shape how efficiently robots can traverse the warehouse. This is visible in the robot tracking visualizations where certain paths are densely interconnected, leading to potential overlaps.

---

## Is the metric driven purely by mechanical constraints, or will logical constraints impact it?

While mechanical constraints such as robot speed, acceleration, and extraction time are core factors in calculating metrics, logical constraints such as path validation (no diagonal movements), prioritization of orders, and batching logic significantly influence the overall performance. Logical constraints ensure the feasibility of routes and adherence to warehouse-specific rules, impacting metrics like transaction time and overlaps.

The heatmap introduces a demand-based logical adjustment that further modifies travel times, showing a direct dependency on logical constraints.

---

## How sensitive are we to assumptions about the customer's operation?

The model is sensitive to assumptions such as uniform traffic multipliers, extraction times, and demand heatmap factors. Any deviation in customer operations, such as uneven distribution of demand or peak operational hours, could lead to inaccuracies in transaction time and cost per transaction estimates.

For example, increasing the traffic multiplier dynamically affects the transaction time, as visible in the dashboards. Adjusting assumptions (e.g., higher demands on specific aisles) can lead to localized congestion, further impacting overlaps and delays.

---

## Do you think we could turn this model into a sizing tool for future opportunities? What amount of error should we assume?

The model has the potential to act as a sizing tool, allowing stakeholders to simulate different warehouse configurations and robot parameters to estimate costs and efficiency metrics. By adjusting inputs such as the number of aisles, levels, and robot speed, it can provide actionable insights for scaling operations.

However, to account for real-world variability, an error margin of 10–20% should be assumed. This margin would cover factors like unexpected delays, machine downtimes, and deviations from the assumed demand distribution in the heatmap.



## 🙏 Thank You!

Thank you for taking the time to explore this repository and follow the implementation of the **Spyder Robot Overlap Analysis** project. Your interest and engagement mean a lot, and I hope you found the code, documentation, and mathematical formulations insightful and useful.

If you have any feedback, suggestions, or encounter any issues, feel free to open an issue or contribute to the repository. I’d love to hear your thoughts and collaborate further!

Don’t forget to ⭐ star this repository if you found it helpful, and stay tuned for future updates!

Happy coding! 🚀
