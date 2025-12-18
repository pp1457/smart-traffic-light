# AV-Informed Dynamic Signal Control and Phase Sequencing for Mixed Traffic Intersections

## Abstract

Adaptive traffic signal control in mixed autonomy environments faces significant challenges due to partial observability from sparse connected vehicle data. This proposal presents a hybrid controller that fuses stable historical demand patterns with real-time autonomous vehicle (AV) signals within a pressure-based framework. The system employs three coordinated layers: historical demand modeling using low-penetration trajectory data, AV voting with reliability scoring, and dynamic scheduling with fairness safeguards and spillback protection. Evaluation using microscopic traffic simulation will demonstrate improvements in average delay, throughput, and equity metrics compared to static timing, max-pressure control, and AV-only approaches across varying penetration rates and demand patterns. The approach offers robustness to communication outages and malicious inputs while providing a pathway for future adaptive learning and multi-intersection coordination.

## Project Overview

This project aims to develop a novel traffic management system that enables autonomous vehicles (AVs) to inform both the sequence and duration of traffic signal phases. Unlike traditional adaptive signal control that optimizes timing within fixed phase orders, our approach allows dynamic phase sequencing based on real-time AV coordination while ensuring safety and fairness for all traffic participants, including non-AVs and pedestrians.

The system addresses the critical challenge of integrating AV technology into existing traffic infrastructure without requiring complete replacement, providing a practical transition strategy for markets like Taiwan where legacy infrastructure investment must be preserved.

## Motivation
Adaptive traffic signal control in mixed autonomy environments faces significant challenges due to partial observability. Key issues include sparse detector coverage, low penetration rates of connected/autonomous vehicles (AVs), sensor occlusions, and biased queue estimates.

Traditional Max-Pressure (MP) control performs well under full-state visibility but becomes noisy and unfair when sensing is imbalanced. A 2024 Nature Communications study demonstrated that low-penetration trajectories (≈7%) can calibrate stochastic Newellian/Bernoulli queue models for offline fixed-time plans. However, this approach only re-optimizes every few weeks and cannot respond to daily disruptions or incorporate real-time AV data.

We propose a hybrid controller that fuses stable historical demand patterns, real-time AV voting, and spillback-aware pressure allocation. This approach delivers fairness, robustness, and responsiveness under partial observability conditions.

## Related Work
Adaptive traffic signal control has evolved through several generations:

**Traditional approaches** like SCATS and SCOOT use fixed detectors and historical patterns but struggle with sparse sensing. Max-Pressure (MP) control optimizes for queue lengths but requires full observability.

**AV-enabled methods** leverage connected vehicle data for trajectory-based control. Studies show that even 5-10% AV penetration can significantly improve signal timing. However, most approaches either rely solely on real-time AV data (vulnerable to low penetration) or historical patterns alone (insensitive to real-time conditions).

**Hybrid approaches** combine multiple data sources but often lack explicit fairness mechanisms or spillback protection. Our work builds on the Nature Communications study while extending it to real-time operation with AV fusion and equity safeguards.

Additional recent works include:
- Mo, Z., Li, W., Fu, Y., Ruan, K., & Di, X. (2023). CVLight: Decentralized learning for adaptive traffic signal control with connected vehicles. Transportation Research Part C: Emerging Technologies.
- Reyad, P. (2025). Advancing intersection safety with adaptive traffic signal control in evolving connected autonomous vehicle networks. University of British Columbia.
- Karbasi, A. H., Omidvar, A., & Patrick, J. (2025). Exploring the impact of traffic signal control and connected and automated vehicles on intersections safety: A deep reinforcement learning approach. Frontiers in Robotics and AI.
- Almasi, M. H., Moghaddam, M. P., & Haghifam, M. R. (2024). Assessing the performance of a hybrid max-weight traffic signal controller. IET Intelligent Transport Systems.
- Zhang, P., Chen, S., & Wang, L. (2024). Learning adaptive traffic signal control strategy through a hybrid agent. Complex & Intelligent Systems.
- Maadi, S., Stein, S., Hong, J., & Murray-Smith, R. (2022). Real-time adaptive traffic signal control in a connected and automated vehicle environment: optimisation of signal planning with reinforcement learning under uncertainty. Sensors, 22(19), 7501.
- Agrahari, A., Dhabu, M. M., Deshpande, P. S., & Tiwari, A. (2024). Artificial intelligence-based adaptive traffic signal control system: A comprehensive review. Electronics, 13(19), 3875.
- Almusawi, A., Albdairi, M., & Qadri, S. S. S. M. (2024). Integrating Autonomous Vehicles (AVs) into Urban Traffic: Simulating Driving and Signal Control. Applied Sciences, 14(19), 8851.
- Medvei, M. M., Bordei, A. V., Niță, Ș. L., & Țăpuș, N. (2025). DeepSIGNAL-ITS—Deep Learning Signal Intelligence for Adaptive Traffic Signal Control in Intelligent Transportation Systems. Applied Sciences, 15(17), 9396.
- Taghavifar, H., & Wei, C. (2024). Socially intelligent reinforcement learning for optimal automated vehicle control in traffic scenarios. IEEE Transactions on Intelligent Transportation Systems.

These studies highlight advancements in decentralized, RL-based, and hybrid MP systems for CV/AV environments, which our proposal extends with historical fusion and fairness.

## Proposed System Overview
The roadside unit (RSU) runs three coordinated layers:
1. **Historical demand backbone.** Builds per-movement baseline intensity $\lambda_{\text{hist},m}(t)$ from multi-week trajectories using penetration estimation and Newellian reconstruction; supports histogram, kernel, or richer density models (e.g., Gaussian mixtures) without changing control logic.
2. **AV voting layer.** Each AV reports movement ID, lane, position, speed, ETA, and confidence. Messages receive reliability scores (kinematic consistency, sensor health) and temporal damping to curb dominance.
3. **Dynamic scheduling layer.** Blends historical priors with AV arrivals, estimates upstream residuals and downstream spillback, and selects phases/green times with fairness safeguards.

**Data footprint.** Standard V2X telemetry (position, speed, ETA), archived connected trajectories (30-90 days retention), signal state logs, and optional neighbor RSU summaries. Estimated storage: 10-50 GB per intersection annually. Privacy-preserving through trajectory aggregation and no raw vehicle identification storage.

**Deployment considerations.** Integrates with existing V2X infrastructure using SAE J2735 messages. Fallback to historical-only mode during communication outages. Cybersecurity through message authentication and anomaly detection.

## Core Mandates & Novel Contributions

The system operates through a **Phase-Aware Hybrid Coordination** approach that integrates traditional traffic signals with advanced AV capabilities:

*   **Traffic Signal Coordination Layer:** Traditional traffic lights maintain base safety and provide predictable phases for non-AVs and pedestrians, with adaptive timing based on detected traffic composition.
*   **AV Coordination Layer:** Within green phase windows, AVs perform batch negotiation and slot allocation to optimize throughput while respecting phase constraints and non-AV flow predictions.
*   **Multi-Modal Detection Layer:** RSU sensors continuously monitor and predict non-AV vehicle movements and pedestrian requests to inform both signal timing and AV coordination decisions.
*   **Safety Arbitration Layer:** Final validation ensures all proposed AV trajectories maintain safety margins with predicted non-AV behavior and guarantee pedestrian phase integrity.

**Primary Innovation:**
*   **AV-Informed Dynamic Phase Sequencing:** Novel framework allowing autonomous vehicles to propose both signal phase sequences and durations based on real-time coordination potential. This moves beyond traditional fixed-phase adaptive timing to dynamic sequence optimization.

**Technical Contributions:**
*   **Generalized Intersection Model:** Support for N-way intersections (3-way to 7-way) with arbitrary geometries beyond traditional 4-way crossings.
*   **Dynamic Phase Generation:** Real-time generation of optimal movement combinations rather than pre-defined phase patterns.
*   **Complex Movement Coordination:** Advanced handling of overlapping phases, conditional phases, and multi-stage movements.
*   **Scalable MPC Formulation:** Mathematical framework that scales from simple intersections to complex multi-approach junctions using Model Predictive Control (MPC) for discrete sequence decisions alongside continuous duration optimization.

**System Contributions:**
*   **Fail-Safe Architecture:** Multi-layer safety system with traditional signal control as baseline.
*   **Emergency Integration:** Seamless preemption protocols maintaining safety during sequence optimization.
*   **Deployment Pathway:** Practical transition strategy for existing infrastructure enhancement, working from V2X-only to full sensor deployments.

## System Model & Architecture

The system runs on a roadside unit (RSU) with three coordinated layers:

- **Data Ingestion Layer**: Receives V2X messages from AVs and processes historical trajectory data
- **Demand Estimation Layer**: Fuses real-time AV signals with historical patterns using adaptive weighting
- **Control Layer**: Computes pressure-based phase selection with fairness constraints and spillback protection

Components communicate via a publish-subscribe pattern, with the control layer running at 1-5 second cycles to match typical traffic signal timing requirements.

### Components

*   **Autonomous Vehicles (AVs):** Execute phase-aware trajectory planning, participate in batch negotiation during green phases, and maintain safety protocols with non-AV traffic.
*   **Smart Traffic Light / RSU:**
    *   Maintains traditional signal phases with adaptive timing.
    *   Coordinates AV batch negotiations within green phase windows.
    *   **V2X-only operation as primary mode** - no additional sensors required.
    *   **Optional sensor integration** for enhanced performance when budget allows.
    *   Validates and approves AV coordination plans based on V2X data.
    *   Handles emergency preemption protocols.
*   **Non-AV Vehicles:** Detected and reported by nearby AVs through V2X communication, with collective AV sensing providing traffic state information to RSU for prediction and coordination decisions.
*   **Pedestrians:** Managed through traditional crossing button systems and AV-reported pedestrian detection, with dedicated crossing phases and priority enforcement.
*   **Emergency Vehicles:** Receive absolute priority through preemption protocols that override both AV coordination and normal signal timing.

### Generalized Intersection Model

The system supports N-Way Intersections (3-way, 4-way, 5-way, and complex multi-leg intersections) with various lane configurations and movement types (through, protected/permissive turns, U-turns, pedestrian crossings). It can handle variable intersection sizes, skewed angles, and irregular geometries.

**Generalized Phase Structure:**
Atomic Movement Units include:
*   Through Movements: `{approach}_through`
*   Protected Turns: `{from_approach}_to_{to_approach}_protected`
*   Permissive Turns: `{from_approach}_to_{to_approach}_permissive`
*   Pedestrian Crossings: `pedestrian_{approach1}_to_{approach2}`

The system dynamically generates compatible movement combinations and phases based on conflict matrices derived from geometric analysis, movement compatibility, and safety requirements.

## Key Notation
- $\lambda_{\text{hist},m}(t)$: Historical demand intensity for movement $m$ at time $t$
- $D_{\text{real},m}(\tau)$: Real-time arrival pulse from AVs for movement $m$
- $\Lambda_m$: Fused demand estimate for movement $m$
- $Q_{\text{up}}(m)$, $\bar{Q}_{\text{down}}(m)$: Upstream and downstream queue estimates
- $P_i$: Pressure for phase $i$, $G_i$: Green time for phase $i$
- $\alpha, \beta, \gamma$: Blending weights for demand fusion and queue updates
- $w_m, w_v$: Fairness weights for movements and vehicles
- $K$: Kernel function for smoothing arrival pulses
- $H$: Prediction horizon for demand integration
- $G_{\text{prev}}(m)$: Green time allocated to movement $m$ in previous cycle
- $C$: Total cycle length
- $r_m$: Historical turning ratio for movement $m$

## Algorithmic Workflow (per decision cycle Δt)
1. **Collect AV votes.** Construct arrival pulse  
   $D_{\text{real,m}}(\tau) = \sum_v w_v K(\tau - \text{ETA}_v)$  
   down-weight implausible ETAs or lane claims.
2. **Update historical prior.** Query $\lambda_{\text{hist},m}$ for current time-of-day/day-type and blend gently with recent served flow to track drift.
3. **Fuse demand.** Compute  

   $$\Lambda_m = \alpha \int_{t}^{t+H} D_{\text{real,m}}(\tau)\,d\tau + (1-\alpha) \int_{t}^{t+H} \lambda_{\text{hist,m}}(\tau)\,d\tau$$

   with tunable (future adaptive) weight $\alpha$.
4. **Estimate upstream queues.** Set $Q_{\text{up}}(m) = Q_{\text{residual}}(m) + \Lambda_m$, updating residuals via past departures, saturation flow, and clearance times.
5. **Predict downstream spillback.** Maintain  

$$\bar{Q}_{\text{down}}(m) \leftarrow \gamma \bar{Q}_{\text{down}}(m) + (1-\gamma)(\mathrm{ProjectedInflow} - \mathrm{ProjectedOutflow})$$

using previous green allocations and historical turning ratios.

**ProjectedInflow and ProjectedOutflow Calculation:**

- **ProjectedInflow** for movement $m$: Estimated as $\lambda_{\text{hist,m}}(t) \times \frac{G_{\text{prev}}(m)}{C}$, where $G_{\text{prev}}(m)$ is the green time allocated to movement $m$ in the previous cycle and $C$ is the cycle length. This represents expected traffic flow into downstream queues based on recent green allocations.

- **ProjectedOutflow** for movement $m$: Estimated as $\lambda_{\text{hist,m}}(t) \times r_m$, where $r_m$ is the historical turning ratio for movement $m$. This represents expected traffic exiting downstream queues based on long-term turning patterns.

The downstream queue estimate uses exponential smoothing with parameter $\gamma$ to blend previous estimates with current net flow predictions, preventing over-reaction to single-cycle variations while enabling round-by-round queue propagation.

6. **Apply fairness weights.** Normalize base weight $w_{\text{m,0}} \propto \sum_v w_v$, then adjust with starvation boosts $\phi_{\text{m}}$, dominance penalties $\psi_{\text{m}}$, and anomaly attenuations to get $w_{\text{m}}$.

7. **Select phase and green.** For phase $i$, compute  
   
   $$P_i = \sum_{m \in M_i} w_m \left[ Q_{\text{up}}(m) - \beta \bar{Q}_{\text{down}}(m) \right]$$
   
   Serve the highest positive pressure; otherwise trigger fairness rotation. Set  
   
   $$G_i = \text{clip}\left( G_{\text{min}}, G_{\text{max}},\, k_1 \sum \Lambda_m + k_2 \sum Q_{\text{residual}} + k_3\, \text{fairness terms} \right)$$
   
   and terminate early once queues clear.

8. **Log and recalibrate.** Record flows, fairness counters, anomalies, and arrivals to refresh $\lambda_{\text{hist},m}$ and audit decisions.

## Pseudocode Implementation

The detailed pseudocode implementation is available in `signal_control_algorithm.py`. This file contains the complete algorithm with data structures, fairness counters, dominance tracking, and round-by-round queue propagation.

## Fairness & Anti-Cheating Safeguards
- Reliability scoring on ETAs and kinematics; flagged AVs contribute less weight or enter quarantine.
- Starvation counters lift underserviced movements until cleared; dominance penalties curb repeated priority.
- Spillback protection suppresses pressure when $\bar{Q}_{\text{down}}$ approaches storage limits, preventing blocked exits.
- Cycle-level audit trail captures competing pressures, chosen phase, and fairness adjustments to support validation and adaptive learning.

## Evaluation Plan
We will evaluate the system using microscopic traffic simulation (SUMO or VISSIM) with real-world calibrated networks:

- **Baselines**
  - Static timing
  - Max-Pressure control
  - AV-only control
  - History-only control

- **Performance Metrics**
  - Average delay and delay variance
  - Queue lengths and throughput
  - Fairness (Gini coefficient of movement delays)

- **Test Scenarios**
  - Varying AV penetration rates (0-50%)
  - Different demand patterns
  - Incident response and recovery
  - Corridor coordination

- **Robustness Testing**
  - Communication failures and outages
  - Sensor malfunctions
  - Malicious AV behavior and cyber attacks

## Simulation Environment & Implementation

The system will be evaluated using **SUMO (Simulation of Urban MObility)**, a microscopic traffic simulation package. SUMO's strengths in large-scale traffic flow analysis, V2X communication simulation, and its TraCI API for dynamic control make it an ideal choice for implementing and testing our custom traffic signal control algorithms.

### Focused Performance Metrics

**Primary Evaluation Metrics:**
*   **Intersection Throughput:** Total vehicles processed per hour (vehicles/hour).
*   **Average Delay:** Mean vehicle delay compared to traditional signal operation (seconds/vehicle).
*   **Safety Conflicts:** Number of potential collision situations per hour (conflicts/hour).
*   **Fairness Index:** Coefficient of variation of delay across vehicle types (dimensionless).

**Implementation Metrics:**
*   **Computational Efficiency:** Algorithm execution time for real-time feasibility (seconds).
*   **Communication Overhead:** V2X message volume per vehicle per cycle (messages/vehicle/cycle).
*   **Infrastructure ROI:** Throughput improvement per infrastructure investment dollar (%/$1000).

**Taiwan-Specific Metrics:**
*   **Motorcycle Integration:** Specialized handling of high-density motorcycle traffic.
*   **Mixed Compliance:** Performance under varying traffic rule adherence levels.
*   **Multi-Way Intersection Performance:** Efficiency gains at complex 3-way, 5-way, and 6-way junctions where traditional timing struggles most.
*   **Geometric Adaptability:** Performance across irregular intersection layouts common in Taiwan urban areas.

### Implementation Roadmap (SUMO-focused)

**Phase 1: Algorithm Development (Months 1-4)**
*   Implement MPC-based sequence optimization algorithm.
*   Develop mathematical formulation for discrete-continuous optimization.
*   Create simulation framework integration with SUMO using TraCI.
*   Validate algorithm convergence and computational feasibility.

**Phase 2: System Integration (Months 3-7)**
*   Extend current V2X communication framework for sequence coordination within SUMO.
*   Implement AV collective sensing algorithms for non-AV detection and tracking within SUMO.
*   Develop safety monitoring and emergency override protocols based on V2X data in SUMO.
*   Create Taiwan-specific traffic behavior models for SUMO.
*   Multi-way intersection geometry modeling for 3-way, 5-way, and 6-way configurations in SUMO.

**Phase 3: Comprehensive Evaluation (Months 6-10)**
*   Execute 48-scenario evaluation matrix with statistical validation in SUMO.
*   Multi-way intersection performance analysis across varying geometric complexity.
*   Compare against baseline methods across all intersection types.
*   Analyze scalability and real-time performance for complex geometries.
*   Document deployment requirements and cost analysis for different intersection types.

**Phase 4: Analysis and Dissemination (Months 9-12)**
*   Comprehensive results analysis and interpretation.
*   Paper writing and submission to target venues.
*   Prepare demonstration materials and potential pilot deployment plans.
*   Document lessons learned and future research directions.

## Research Value & Expected Outcomes
**Novel contributions.** Hybrid fusion of offline low-penetration demand estimation with live AV signals inside a pressure controller; robustness to sparse sensing; explicit fairness and integrity layer; modular demand model upgrades without controller redesign.

**Expected outcomes.** Lower mean and variance of delay versus static timing and vanilla MP; improved equity metrics (e.g., lower Gini of movement delays); faster recovery after incidents without oscillation; deployable pathway using existing V2X plus historical logs and enabling future adaptive α learning and corridor coordination.

## Future Work & Potential Improvements

The project identifies several areas for future enhancement and research:

*   **Adaptive Demand Fusion Weight ($\alpha$):** Implement penetration-adaptive, confidence-weighted, and time-variant weighting for $\alpha$.
*   **Historical Demand Update Mechanism:** Introduce anomaly-triggered recalibration, multi-timescale decomposition, and event detection for historical priors.
*   **Downstream Spillback Prediction Enhancement:** Develop multi-link queue propagation, storage capacity constraints, and neighbor RSU coordination protocols.
*   **Fairness Mechanism Formalization:** Formalize fairness objectives (e.g., max-min fairness, budget-based fairness, temporal guarantees) and monitor Gini coefficient.
*   **Green Time Calculation Refinement:** Use queue-clearing based formulas, learning-based coefficient tuning, and cycle-length constraint awareness.
*   **Reliability Scoring Specification:** Detail kinematic consistency checks, sensor health indicators, behavioral anomaly detection, and cryptographic authentication.
*   **Adaptive Prediction Horizon:** Implement penetration-adaptive, congestion-adaptive, and confidence-weighted prediction horizons.
*   **Edge Case Handling:** Address communication timeout fallback, sensor occlusion modeling, pedestrian/cyclist integration, emergency vehicle preemption, and actuator constraint handling.
*   **Computational Efficiency Optimization:** Explore incremental updates, phase pruning, parallel computation, and lazy evaluation.
*   **Enhanced Evaluation Metrics:** Include delay variance, equity metrics beyond Gini, robustness metrics, energy/emissions, and safety surrogate measures.

**Current limitations**: Requires minimum AV penetration for reliable operation; computational complexity may limit very dense networks; parameter tuning needed for different intersection geometries.

**Future extensions**: Adaptive parameter learning, multi-intersection coordination, integration with emerging C-V2X standards, privacy-preserving trajectory sharing, and reinforcement learning for optimal control policies. Specifically, explore integration with 5G-V2X for ultra-low latency (as low as 1 ms) AV communications, enabling enhanced real-time data fusion, cooperative traffic management, and improved safety through shared AV perceptions. This could reduce congestion via dynamic signal adjustments and support advanced applications like cooperative adaptive cruise control.

**Reference**  
[1] Wang, Y., et al. "Traffic light optimization with low penetration rate vehicle trajectory data." Nature Communications 15, 47866 (2024). https://doi.org/10.1038/s41467-024-45427-4

[2] Mo, Z., Li, W., Fu, Y., Ruan, K., & Di, X. (2023). CVLight: Decentralized learning for adaptive traffic signal control with connected vehicles. Transportation Research Part C: Emerging Technologies. https://doi.org/10.1016/j.trc.2022.103728

[3] Reyad, P. (2025). Advancing intersection safety with adaptive traffic signal control in evolving connected autonomous vehicle networks. University of British Columbia. https://doi.org/10.2139/ssrn.5312561

[4] Karbasi, A. H., Omidvar, A., & Patrick, J. (2025). Exploring the impact of traffic signal control and connected and automated vehicles on intersections safety: A deep reinforcement learning approach. Frontiers in Robotics and AI. https://doi.org/10.3390/futuretransp2010002

[5] Almasi, M. H., Moghaddam, M. P., & Haghifam, M. R. (2024). Assessing the performance of a hybrid max-weight traffic signal controller. IET Intelligent Transport Systems. https://doi.org/10.5703/1288284316024

[6] Zhang, P., Chen, S., & Wang, L. (2024). Learning adaptive traffic signal control strategy through a hybrid agent. Complex & Intelligent Systems. https://doi.org/10.2139/ssrn.4830117

[7] Maadi, S., Stein, S., Hong, J., & Murray-Smith, R. (2022). Real-time adaptive traffic signal control in a connected and automated vehicle environment: optimisation of signal planning with reinforcement learning under uncertainty. Sensors, 22(19), 7501. https://doi.org/10.3390/s22197501

[8] Agrahari, A., Dhabu, M. M., Deshpande, P. S., & Tiwari, A. (2024). Artificial intelligence-based adaptive traffic signal control system: A comprehensive review. Electronics, 13(19), 3875. https://doi.org/10.3390/electronics13193875

[9] Almusawi, A., Albdairi, M., & Qadri, S. S. S. M. (2024). Integrating Autonomous Vehicles (AVs) into Urban Traffic: Simulating Driving and Signal Control. Applied Sciences, 14(19), 8851. https://doi.org/10.3390/app14198851

[10] Medvei, M. M., Bordei, A. V., Niță, Ș. L., & Țăpuș, N. (2025). DeepSIGNAL-ITS—Deep Learning Signal Intelligence for Adaptive Traffic Signal Control in Intelligent Transportation Systems. Applied Sciences, 15(17), 9396. https://doi.org/10.3390/app15179396

[11] Taghavifar, H., & Wei, C. (2024). Socially intelligent reinforcement learning for optimal automated vehicle control in traffic scenarios. IEEE Transactions on Intelligent Transportation Systems. https://doi.org/10.1109/tase.2023.3347264