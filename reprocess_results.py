import os
import pandas as pd
import xml.etree.ElementTree as ET
import glob

RESULTS_DIR = "data/results"
EXPERIMENT_LOG = os.path.join(RESULTS_DIR, "experiment_log.csv")

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
            sorted_delays = sorted(time_losses)
            n = len(sorted_delays)
            cumulative_delays = sum(sorted_delays)
            if cumulative_delays > 0:
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

def main():
    # 1. Find all XML files in results directory
    pattern = os.path.join(RESULTS_DIR, "*.xml")
    files = glob.glob(pattern)
    
    records = []
    
    print(f"Found {len(files)} result files.")
    
    for xml_file in files:
        basename = os.path.basename(xml_file)
        
        # Skip raw tripinfo files
        if basename.startswith("tripinfo_"):
            continue
            
        # Parse filename to extract metadata
        # Format: {scenario}_{day}_{algorithm}_{timestamp}.xml
        # This is tricky because algorithm can have underscores.
        # But we know the structure:
        # Scenario is first (can have underscores? e.g. comparative_study)
        # Day is next (Monday, Pen_05, etc)
        # Timestamp is last (YYYYMMDD_HHMMSS)
        # Algorithm is in between.
        
        parts = basename.replace(".xml", "").split("_")
        
        # Timestamp is last 2 parts joined
        timestamp_str = f"{parts[-2]}_{parts[-1]}"
        run_id = f"{parts[-2]}-{parts[-1][:4]}"
        
        # Identify Scenario and Day
        # We know our scenarios: comparative_study, sensitivity_analysis, robustness_test, standard_week, stress_test
        known_scenarios = ["comparative_study", "sensitivity_analysis", "robustness_test", "standard_week", "stress_test"]
        
        scenario = "unknown"
        for s in known_scenarios:
            if basename.startswith(s):
                scenario = s
                break
        
        if scenario == "unknown":
            continue
            
        # Remove scenario from parts to find day
        # scenario length in parts
        scen_parts_len = len(scenario.split("_"))
        remaining_parts = parts[scen_parts_len:]
        
        # Day is the first of remaining
        day = remaining_parts[0]
        
        # Algorithm is everything between Day and Timestamp
        # remaining_parts[1:-2]
        algo_parts = remaining_parts[1:-2]
        algorithm = "_".join(algo_parts)
        
        # Parse metrics
        throughput, avg_delay, avg_waiting_time, gini = parse_tripinfo(xml_file)
        
        if throughput == 0:
            continue
            
        # Determine Penetration and Scale (Approximate or Default)
        # This is hard to reverse engineer perfectly without the log, 
        # but we can infer from Day for sensitivity/robustness
        penetration = 0.15
        scale = 1.0
        
        if scenario == "sensitivity_analysis":
            if "Pen_05" in day: penetration = 0.05
            elif "Pen_15" in day: penetration = 0.15
            elif "Pen_30" in day: penetration = 0.30
            elif "Pen_50" in day: penetration = 0.50
            elif "Pen_80" in day: penetration = 0.80
            elif "Pen_100" in day: penetration = 1.0
            
        if scenario == "stress_test":
            scale = 1.5
            
        records.append({
            "timestamp": timestamp_str,
            "run_id": run_id,
            "scenario": scenario,
            "day": day,
            "algorithm": algorithm,
            "scale": scale,
            "penetration": penetration,
            "throughput": throughput,
            "avg_delay": avg_delay,
            "avg_waiting_time": avg_waiting_time,
            "fairness_gini": gini
        })
        
    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    # Sort by timestamp
    df = df.sort_values("timestamp")
    
    # Save
    print(f"Saving {len(df)} records to {EXPERIMENT_LOG}")
    df.to_csv(EXPERIMENT_LOG, index=False)

if __name__ == "__main__":
    main()
