import os
import subprocess
import pandas as pd
import xml.etree.ElementTree as ET
import datetime
import shutil

# Configuration
RESULTS_DIR = "data/results"
WEEK_LOG = os.path.join(RESULTS_DIR, "week_log.csv")
PYTHON_EXEC = ".venv/bin/python" 

# Simulation Settings
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_TYPES = {
    "Monday": "weekday", "Tuesday": "weekday", "Wednesday": "weekday", 
    "Thursday": "weekday", "Friday": "weekday", 
    "Saturday": "weekend", "Sunday": "weekend"
}
# Scale factor for traffic demand (1.0 = normal, 0.6 = weekend light traffic)
DEMAND_SCALES = {
    "weekday": 1.0,
    "weekend": 0.6
}

# Tuned Parameters
W_HIST = 1.0
W_AV = 2.0
THRESHOLD = 0.0
PENETRATION = 0.15 # Use a stable penetration rate for this test

def ensure_results_dir():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    
    if not os.path.exists(WEEK_LOG):
        df = pd.DataFrame(columns=[
            "timestamp", "run_id", "day", "day_type", "scale",
            "throughput", "avg_delay", "avg_waiting_time"
        ])
        df.to_csv(WEEK_LOG, index=False)

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

def modify_demand(scale):
    """
    Modifies hello.rou.xml to scale demand.
    We scale the 'probability' attribute of flows.
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
            
    tree.write("hello.rou.xml")
    print(f"Modified traffic demand with scale {scale}")

def restore_demand():
    if os.path.exists("hello.rou.xml.bak"):
        shutil.copy("hello.rou.xml.bak", "hello.rou.xml")
        print("Restored original traffic demand.")

def run_day_experiment(day, day_type, run_id):
    scale = DEMAND_SCALES[day_type]
    print(f"\n--- Simulating {day} ({day_type}, scale={scale}) ---")
    
    # 1. Modify Traffic
    modify_demand(scale)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(RESULTS_DIR, f"tripinfo_{day}_{timestamp}.xml")
    
    # 2. Run Simulation
    cmd = [
        PYTHON_EXEC, "runner.py", 
        "--algorithm", "hybrid", 
        "--output", output_file,
        "--w_hist", str(W_HIST),
        "--w_av", str(W_AV),
        "--threshold", str(THRESHOLD),
        "--penetration", str(PENETRATION),
        "--day_type", day_type
    ]
    subprocess.run(cmd, check=True)
    
    # 3. Evaluate
    throughput, avg_delay, avg_waiting_time = parse_tripinfo(output_file)
    
    print(f"Results: Throughput={throughput}, Delay={avg_delay:.2f}s")
    
    # 4. Log
    new_row = {
        "timestamp": timestamp,
        "run_id": run_id,
        "day": day,
        "day_type": day_type,
        "scale": scale,
        "throughput": throughput,
        "avg_delay": avg_delay,
        "avg_waiting_time": avg_waiting_time
    }
    
    df = pd.read_csv(WEEK_LOG)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(WEEK_LOG, index=False)

def main():
    ensure_results_dir()
    
    # Ensure we have a backup of the route file before we start messing with it
    if not os.path.exists("hello.rou.xml.bak"):
        shutil.copy("hello.rou.xml", "hello.rou.xml.bak")
    
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    
    try:
        for day in DAYS:
            day_type = DAY_TYPES[day]
            run_day_experiment(day, day_type, run_id)
            
    finally:
        # Always restore original file
        restore_demand()
    
    print("\n=== Week Simulation Completed ===")
    print(f"Results saved to {WEEK_LOG}")

if __name__ == "__main__":
    main()
