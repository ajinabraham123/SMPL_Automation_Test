# SMPL_Automation_Test

Addressing the Leading Questions
1. How does the topology of the system impact the metric?
Findings:

Longer aisles (higher X distance) and taller racks (higher Z distance) result in increased travel time, which directly impacts the average transaction time and cost per transaction.
More levels and aisles also increase the time robots spend navigating to storage nodes, increasing delays.
However, adding more robots or increasing speed reduces queuing delays, mitigating the impact of complex topology.
Conclusion: The system topology significantly impacts cost per transaction. Higher complexity requires either faster robots or additional robots to maintain efficiency.

2. Is the metric driven purely by mechanical constraints, or will logical constraints impact it?
Findings:

Mechanical constraints (speed, acceleration, aisle length, and level height) dominate the cost per transaction.
Logical constraints, such as robot queueing delays and the number of robots available, also influence the metric. If logical constraints are not addressed, queuing can lead to bottlenecks, regardless of mechanical improvements.
Conclusion: Both mechanical and logical constraints play crucial roles. Logical constraints, such as efficient robot scheduling, can become a bottleneck even with faster robots.

3. How sensitive are we to assumptions about the customer's operation?
Findings:

Assumptions like transaction rates (workload rates) heavily influence cost per transaction. High workloads expose bottlenecks in both speed and queuing delays.
Sensitivity to extraction time upgrades depends on workload levels. At high workloads, reducing extraction time significantly lowers costs.
Conclusion: The model is moderately sensitive to operational assumptions. Transaction volume and required throughput are critical variables.

4. Can this model become a sizing tool for future opportunities? What amount of error should we assume?
Findings:

The dynamic workload simulation and configurability make this model highly scalable as a sizing tool for different warehouse setups.
Error margins could stem from the assumptions on robot behavior, queuing dynamics, and uniform workload distributions.
A 5-10% error margin is reasonable, accounting for variability in real-world conditions.
Conclusion: This model can serve as a sizing tool, with error margins depending on how accurately customer-specific constraints are captured.


Reference Materials used:
1) chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://annals.fih.upt.ro/pdf-full/2013/ANNALS-2013-1-26.pdf
2) Multi-Robot Routing with Time Windows: A Column Generation Approach
Naveed Haghani, Jiaoyang Li, Sven Koenig, Gautam Kunapuli, Claudio Contardo, Amelia Regan, Julian Yarkony

plotly urls: 
https://plotly.com/python/line-and-scatter/
https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart
https://plotly.com/python/colorscales/
