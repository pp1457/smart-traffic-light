import os
import subprocess
import pandas as pd
import xml.etree.ElementTree as ET
import datetime
import shutil
import time

# Configuration
RESULTS_DIR = "data/results"
EXPERIMENT_LOG = os.path.join(RESULTS_DIR, "experiment_log.csv")
PYTHON_EXEC = ".venv/bin/python" 

# Optimal Parameters
HORIZON = 60.0
SWITCHING_COST = 50.0
FAIRNESS = 0.1
PENETRATION = 0.15 # Default penetration for standard/stress tests

# Scenarios
SCENARIOS = {
    "standard_week": {
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "day_types": {
            "Monday": "weekday", "Tuesday": "weekday", "Wednesday": "weekday", 
            "Thursday": "weekday", "Friday": "weekday", 
            "Saturday": "weekend", "Sunday": "weekend"
        },
        "scales": {"weekday": 1.0, "weekend": 0.6},
        "penetration": 0.15
    },
    "stress_test": {
        "days": ["Peak_Hour"],
        "day_types": {"Peak_Hour": "weekday"},
        "scales": {"weekday": 1.5}, # 1.5x Demand
        "penetration": 0.15
    },
    "comparative_study": {
        "days": ["Monday"], # Single day for comparison
        "day_types": {"Monday": "weekday"}, # Added day_types for consistency
        "algorithms": ["fixed_time", "max_pressure", "offline_optimized", "hybrid_pressure", "hybrid_pressure_v2", "mpc_dynamic"],
        "penetration": 0.15,
        "scales": {"weekday": 1.0, "weekend": 0.6}
    },
    "robustness_test": {
        "days": ["Low_Pen", "Med_Pen"],
        "day_types": {"Low_Pen": "weekday", "Med_Pen": "weekday"},
        "scales": {"weekday": 1.0},
        "penetration_override": {"Low_Pen": 0.05, "Med_Pen": 0.20}
    },
    "sensitivity_analysis": {
        "days": ["Pen_05", "Pen_15", "Pen_30", "Pen_50", "Pen_80", "Pen_100"],
        "day_types": {
            "Pen_05": "weekday", "Pen_15": "weekday", "Pen_30": "weekday", 
            "Pen_50": "weekday", "Pen_80": "weekday", "Pen_100": "weekday"
        },
        "scales": {"weekday": 1.0},
        "penetration_override": {
            "Pen_05": 0.05, "Pen_15": 0.15, "Pen_30": 0.30, 
            "Pen_50": 0.50, "Pen_80": 0.80, "Pen_100": 1.0
        },
        "algorithms": ["fixed_time", "hybrid_pressure_v2", "mpc_dynamic"]
    },
    "calibration_test": [
       {"scenario": "calibration_test", "day": "Calibration_Day", "scale": 1.5, "penetration": 0.15, "algo": "fixed_time"},
       {"scenario": "calibration_test", "day": "Calibration_Day", "scale": 1.5, "penetration": 0.15, "algo": "fixed_time_misconfigured"},
       {"scenario": "calibration_test", "day": "Calibration_Day", "scale": 1.5, "penetration": 0.15, "algo": "mpc_dynamic"},
    ],
    "split_sensitivity": [
       {"scenario": "split_sensitivity", "day": "Split_Test", "scale": 1.5, "penetration": 0.15, "algo": "fixed_time_45_15"},
       {"scenario": "split_sensitivity", "day": "Split_Test", "scale": 1.5, "penetration": 0.15, "algo": "fixed_time_40_20"},
       {"scenario": "split_sensitivity", "day": "Split_Test", "scale": 1.5, "penetration": 0.15, "algo": "fixed_time_30_30"},
       {"scenario": "split_sensitivity", "day": "Split_Test", "scale": 1.5, "penetration": 0.15, "algo": "fixed_time_20_40"},
       # MPC reference to show robustness
       {"scenario": "split_sensitivity", "day": "Split_Test", "scale": 1.5, "penetration": 0.15, "algo": "mpc_dynamic"},
    ]
}

ALGORITHMS = [
    {"name": "fixed_time", "args": []},
    {"name": "max_pressure", "args": []},
    {"name": "mpc_static", "args": ["--algorithm", "hybrid", "--disable_dynamic"]},
    {"name": "mpc_dynamic", "args": ["--algorithm", "hybrid"]},
    {"name": "hybrid_pressure_v2", "args": ["--algorithm", "hybrid_pressure_v2"]}
]

def ensure_results_dir():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    
    if not os.path.exists(EXPERIMENT_LOG):
        df = pd.DataFrame(columns=[
            "timestamp", "run_id", "scenario", "day", "algorithm", "scale", "penetration",
            "throughput", "avg_delay", "avg_waiting_time", "fairness_gini"
        ])
        df.to_csv(EXPERIMENT_LOG, index=False)

def parse_tripinfo(xml_file):
    """Parses tripinfo.xml to calculate metrics."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        durations = []
        time_losses = []
        waiting_times = []
        
        for trip in root.findall('tripinfo'):
            durations.append(float(trip.get('duration')))
            time_losses.append(float(trip.get('timeLoss')))
            waiting_times.append(float(trip.get('waitingTime')))
            
        if not durations:
            return 0, 0, 0, 0
            
        throughput = len(durations) 
        avg_delay = sum(time_losses) / len(time_losses)
        avg_waiting_time = sum(waiting_times) / len(waiting_times)
        
        # Calculate Gini
        if len(time_losses) > 1:
            # Sort for simpler Gini calculation
            sorted_delays = sorted(time_losses)
            n = len(sorted_delays)
            cumulative_delays = sum(sorted_delays)
            if cumulative_delays > 0:
                # Gini formula: (2 * sum(i * xi) - (n + 1) * sum(xi)) / (n * sum(xi))
                # where i is 1-based index
                numerator = 2 * sum((i+1) * xi for i, xi in enumerate(sorted_delays))
                denominator = n * cumulative_delays
                gini = (numerator - (n + 1) * cumulative_delays) / denominator
            else:
                gini = 0.0
        else:
            gini = 0.0
        
        return throughput, avg_delay, avg_waiting_time, gini
        
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return 0, 0, 0, 0

def modify_demand(scale):
    """
    Modifies hello.rou.xml to scale demand.
    """
    # Backup original
    if not os.path.exists("hello.rou.xml.bak"):
        shutil.copy("hello.rou.xml", "hello.rou.xml.bak")
    
    # Read from backup to get base values
    tree = ET.parse("hello.rou.xml.bak")
    root = tree.getroot()
    
    for flow in root.findall('flow'):
        if 'probability' in flow.attrib:
            original_prob = float(flow.get('probability'))
            new_prob = original_prob * scale
            flow.set('probability', f"{new_prob:.4f}")
        elif 'period' in flow.attrib:
            original_period = float(flow.get('period'))
            new_period = original_period / scale
            flow.set('period', f"{new_period:.2f}")
    
    # Write the modified XML to hello.rou.xml
    tree.write("hello.rou.xml")

def restore_demand():
    """Restores hello.rou.xml from backup."""
    if os.path.exists("hello.rou.xml.bak"):
        shutil.copy("hello.rou.xml.bak", "hello.rou.xml")
        # os.remove("hello.rou.xml.bak") # Optionally remove backup after restoring

def run_experiment(scenario_name, day, day_type, scale, penetration, algo_config, run_id):
    """
    Executes a single SUMO simulation run and logs results.
    """
    print(f"--- Running {scenario_name}/{day} with {algo_config['name']} (Scale: {scale}, Pen: {penetration}) ---")
    
    # Generate a unique output directory for this run
    output_dir = os.path.join(RESULTS_DIR, run_id, scenario_name, day, algo_config['name'])
    os.makedirs(output_dir, exist_ok=True)
    
    # Modify demand based on scale
    modify_demand(scale)
    
    # Construct command for main.py
    command = [
        PYTHON_EXEC, "runner.py",
        "--horizon", str(HORIZON),
        "--switching_cost", str(SWITCHING_COST),
        "--fairness", str(FAIRNESS),
        "--penetration", str(penetration),
        "--output", os.path.join(output_dir, "tripinfo.xml"),
        # "--seed", "42" # Seed not supported by runner.py yet
    ]
    
    # Auto-add algorithm flag if not present
    explicit_algo_flag = False
    for arg in algo_config["args"]:
        if arg == "--algorithm":
            explicit_algo_flag = True
            break
            
    if not explicit_algo_flag:
        command.extend(["--algorithm", algo_config["name"]])
        
    command.extend(algo_config["args"])
    
    start_time = time.time()
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Simulation for {algo_config['name']} completed successfully.")
        
        # Parse results
        tripinfo_file = os.path.join(output_dir, "tripinfo.xml")
        throughput, avg_delay, avg_waiting_time, fairness_gini = parse_tripinfo(tripinfo_file)
        
        # Log results
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = pd.DataFrame([{
            "timestamp": timestamp,
            "run_id": run_id,
            "scenario": scenario_name,
            "day": day,
            "algorithm": algo_config['name'],
            "scale": scale,
            "penetration": penetration,
            "throughput": throughput,
            "avg_delay": avg_delay,
            "avg_waiting_time": avg_waiting_time,
            "fairness_gini": fairness_gini
        }])
        
        # Append to CSV
        log_df = pd.read_csv(EXPERIMENT_LOG)
        log_df = pd.concat([log_df, new_row], ignore_index=True)
        log_df.to_csv(EXPERIMENT_LOG, index=False)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running simulation for {algo_config['name']}: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred during run for {algo_config['name']}: {e}")
    finally:
        end_time = time.time()
        print(f"Run completed in {end_time - start_time:.2f} seconds.")
        restore_demand() # Ensure demand is restored after each run

def main():
    ensure_results_dir()
    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Run Scenarios
        # Run Scenarios
        # scenarios_to_run = ["sensitivity_analysis", "test_calibration"]
        scenarios_to_run = ["split_sensitivity"]
        # scenarios_to_run = SCENARIOS.keys()
        
        for scenario_name in scenarios_to_run:
            config = SCENARIOS[scenario_name]
            print(f"\n=== Starting Scenario: {scenario_name} ===")
            
            # Helper to run a single case
            def execute_run(day, day_type, scale, penetration, algo_name):
                # Find algo config or create ad-hoc
                algo_config = next((a for a in ALGORITHMS if a["name"] == algo_name), None)
                if not algo_config:
                    algo_config = {"name": algo_name, "args": []}
                run_experiment(scenario_name, day, day_type, scale, penetration, algo_config, run_id)

            if isinstance(config, list):
                # New List Format: Explicit run definitions
                for run_def in config:
                    # Provide defaults for missing keys if necessary, though explicit is better
                    dayType = "weekday" # Default
                    if "day" in run_def:
                         # Assume standard logical mapping if not explicit, or just pass "weekday"
                         dayType = "weekday" 
                    
                    execute_run(
                        run_def["day"], 
                        dayType, 
                        run_def["scale"], 
                        run_def["penetration"], 
                        run_def["algo"]
                    )
            else:
                # Old Dict Format (Legacy)
                for day in config["days"]:
                    day_type = config["day_types"][day]
                    scale = config["scales"][day_type]
                    
                    # Determine Penetration
                    if "penetration" in config:
                        penetration = config["penetration"]
                    else:
                        penetration = 0.15 # Default fallback
                        
                    if "penetration_override" in config and day in config["penetration_override"]:
                        penetration = config["penetration_override"][day]
                    
                    # Run Scenario Algorithms
                    scenario_algos = config.get("algorithms", [a["name"] for a in ALGORITHMS])
                    
                    for algo_name in scenario_algos:
                        execute_run(day, day_type, scale, penetration, algo_name)
                    
    finally:
        restore_demand()
    
    print("\n=== Comprehensive Experiments Completed ===")
    print(f"Results saved to {EXPERIMENT_LOG}")

if __name__ == "__main__":
    main()
