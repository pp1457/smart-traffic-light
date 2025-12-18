import os
import subprocess
import pandas as pd
import xml.etree.ElementTree as ET
import datetime
import itertools

# Configuration
RESULTS_DIR = "data/results"
TUNING_LOG = os.path.join(RESULTS_DIR, "tuning_log.csv")
PYTHON_EXEC = ".venv/bin/python" 

# Parameter Grid for MPC
HORIZONS = [40.0, 50.0, 60.0]
SWITCHING_COSTS = [0.0, 10.0, 50.0, 100.0]

def ensure_results_dir():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    
    # Initialize log file if it doesn't exist
    if not os.path.exists(TUNING_LOG):
        df = pd.DataFrame(columns=[
            "timestamp", "run_id", "horizon", "switching_cost", 
            "throughput", "avg_delay", "avg_waiting_time"
        ])
        df.to_csv(TUNING_LOG, index=False)

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
            return 0, 0, 0
            
        throughput = len(durations) 
        avg_delay = sum(time_losses) / len(time_losses)
        avg_waiting_time = sum(waiting_times) / len(waiting_times)
        
        return throughput, avg_delay, avg_waiting_time
        
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return 0, 0, 0

def run_tuning_experiment(horizon, switching_cost, run_id):
    print(f"\n--- Tuning Run: horizon={horizon}, switching_cost={switching_cost} ---")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(RESULTS_DIR, f"tripinfo_mpc_{timestamp}.xml")
    
    # Run simulation with parameters
    cmd = [
        PYTHON_EXEC, "runner.py", 
        "--algorithm", "hybrid", 
        "--output", output_file,
        "--horizon", str(horizon),
        "--switching_cost", str(switching_cost),
        "--penetration", "0.05"
    ]
    subprocess.run(cmd, check=True)
    
    # Evaluate
    throughput, avg_delay, avg_waiting_time = parse_tripinfo(output_file)
    
    print(f"Results: Throughput={throughput}, Delay={avg_delay:.2f}s")
    
    # Log results
    new_row = {
        "timestamp": timestamp,
        "run_id": run_id,
        "horizon": horizon,
        "switching_cost": switching_cost,
        "throughput": throughput,
        "avg_delay": avg_delay,
        "avg_waiting_time": avg_waiting_time
    }
    
    df = pd.read_csv(TUNING_LOG)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(TUNING_LOG, index=False)

def main():
    ensure_results_dir()
    
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    
    # Generate all combinations
    combinations = list(itertools.product(HORIZONS, SWITCHING_COSTS))
    total_runs = len(combinations)
    
    print(f"Starting MPC tuning batch with {total_runs} configurations...")
    
    for i, (horizon, cost) in enumerate(combinations):
        print(f"Progress: {i+1}/{total_runs}")
        run_tuning_experiment(horizon, cost, run_id)
    
    print("\n=== Tuning Batch Completed ===")
    print(f"Results saved to {TUNING_LOG}")

if __name__ == "__main__":
    main()
