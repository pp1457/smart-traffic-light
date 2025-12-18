# AV-Informed Dynamic Signal Control and Phase Sequencing

Using **SUMO (Simulation of Urban MObility)**, this project implements and evaluates a **3-Layer Hybrid Architecture** for traffic signal control in mixed autonomy environments (Partial CAV Penetration). It fuses historical demand priors with real-time AV data to enable robust control even at low penetration rates.

## Features

- **Three-Layer Architecture**:
    1.  **Historical Demand Backbone**: Learns baseline demand from historical data.
    2.  **AV Voting & Fusion**: Fuses sparse AV data with historical priors.
    3.  **Dynamic Control**: Supports MPC (Model Predictive Control) and Hybrid Pressure algorithms.
- **Multiple Control Algorithms**:
    - `fixed_time`: Cyclic pre-timed control.
    - `max_pressure`: Standard Max Pressure control.
    - `mpc_dynamic`: AV-Informed Model Predictive Control with dynamic phase sequencing.
    - `hybrid_pressure_v2`: Heuristic-based pressure control with fairness safeguards.
- **Simulation Framework**: Built on SUMO with TraCI for real-time control.
- **Batched Experiments**: Automated experiment manager for sensitivity analysis, stress testing, and robustness checks.

## Requirements

- **OS**: macOS (tested), Linux, or Windows.
- **SUMO**: Version 1.21 or compatible. Ensure `SUMO_HOME` environment variable is set.
- **Python**: 3.8+

## Installation

1.  **Install SUMO**:
    Follow the official guide: [SUMO Installation](https://sumo.dlr.de/docs/Downloads.php).
    
    *macOS example via Homebrew:*
    ```bash
    brew install sumo
    export SUMO_HOME=$(brew --prefix sumo)/share/sumo
    ```

2.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd Smart_Traffic_Light
    ```

3.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Running Comprehensive Experiments

The `experiment_manager.py` script runs a defined set of scenarios (e.g., sensitivity analysis, stress tests) and logs results to `data/results/experiment_log.csv`.

```bash
python experiment_manager.py
```

*Note: You can modify the `scenarios_to_run` list in `experiment_manager.py` to select specific experiments.*

### 2. Running a Single Simulation

Use `runner.py` to execute a single simulation run with specific parameters.

```bash
# Run with GUI (Recommended for visualization)
python runner.py --gui --algorithm mpc_dynamic --penetration 0.15

# Run headless (Faster for data collection)
python runner.py --algorithm fixed_time --scale 1.5
```

**Common Arguments:**
- `--gui`: Enable SUMO GUI.
- `--algorithm`: Control strategy (`fixed_time`, `max_pressure`, `mpc_dynamic`, `hybrid_pressure_v2`).
- `--penetration`: AV Penetration rate (0.0 to 1.0).
- `--scale`: Traffic demand scale factor (e.g., 1.5 for stress test).
- `--horizon`: MPC prediction horizon (default: 10).

### 3. Generating Reports

After running experiments, use the reporting scripts to generate plots and statistics.

```bash
# Generate plots from experiment logs
python visualize_results.py
```

Plots are saved to `data/results/plots/`.

## Project Structure

```
Smart_Traffic_Light/
├── controllers/            # Control algorithm implementations
├── data/
│   ├── results/            # Experiment logs and output plots
│   └── ...
├── report/                 # LaTeX project report
├── experiment_manager.py   # Batch experiment runner
├── runner.py               # Main simulation entry point
├── signal_control_algorithm.py # Controller logic dispatcher
├── requirements.txt        # Python dependencies
├── *.xml / *.sumocfg       # SUMO network and config files
└── README.md
```

## Author

**Yun-Yang Liao**  
Dept. of Computer Science and Information Engineering, National Taiwan University
