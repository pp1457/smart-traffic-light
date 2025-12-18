import os
import subprocess
import pandas as pd
import xml.etree.ElementTree as ET
import datetime

# Configuration
RESULTS_DIR = "data/results"
PENETRATION_LOG = os.path.join(RESULTS_DIR, "penetration_log.csv")
PYTHON_EXEC = ".venv/bin/python" 

# Penetration Rates to Test
PENETRATION_RATES = [0.05, 0.15, 0.30, 0.50, 0.75, 1.0]

# Optimal parameters from tuning
HORIZON = 60.0
SWITCHING_COST = 50.0
FAIRNESS = 0.1

def ensure_results_dir():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    
    # Initialize log file if it doesn't exist
    if not os.path.exists(PENETRATION_LOG):
        df = pd.DataFrame(columns=[
            "run_id", "penetration_rate", 
            "throughput", "avg_delay", "avg_waiting_time"
        ])
        df.to_csv(PENETRATION_LOG, index=False)

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

def run_penetration_experiment(penetration, run_id):
    print(f"\n--- Penetration Run: {penetration*100}% ---")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(RESULTS_DIR, f"tripinfo_pen_{int(penetration*100)}_{timestamp}.xml")
    
    # Run simulation with parameters
    cmd = [
        PYTHON_EXEC, "runner.py", 
        "--algorithm", "hybrid", 
        "--output", output_file,
        "--horizon", str(HORIZON),
        "--switching_cost", str(SWITCHING_COST),
        "--fairness", str(FAIRNESS),
        "--penetration", str(penetration)
    ]
    subprocess.run(cmd, check=True)
    
    # Evaluate
    throughput, avg_delay, avg_waiting_time = parse_tripinfo(output_file)
    
    print(f"Results: Throughput={throughput}, Delay={avg_delay:.2f}s")
    
    # Log results
    new_row = {
        "timestamp": timestamp,
        "run_id": run_id,
        "penetration_rate": penetration,
        "throughput": throughput,
        "avg_delay": avg_delay,
        "avg_waiting_time": avg_waiting_time
    }
    
    df = pd.read_csv(PENETRATION_LOG)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(PENETRATION_LOG, index=False)

def main():
    ensure_results_dir()
    
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    
    print(f"Starting penetration rate sweep: {PENETRATION_RATES}")
    
    for i, pen in enumerate(PENETRATION_RATES):
        print(f"Progress: {i+1}/{len(PENETRATION_RATES)}")
        run_penetration_experiment(pen, run_id)
    
    print("\n=== Penetration Sweep Completed ===")
    print(f"Results saved to {PENETRATION_LOG}")

if __name__ == "__main__":
    main()
