import pandas as pd
import os

RESULTS_FILE = "data/results/experiment_log.csv"

def generate_latex_table():
    if not os.path.exists(RESULTS_FILE):
        print("No results file found.")
        return

    df = pd.read_csv(RESULTS_FILE)
    
    # Comparative Study Table
    subset = df[df['scenario'] == 'comparative_study']
    if not subset.empty:
        # Get latest run_id or group by run_id
        latest_run = subset['run_id'].max()
        data = subset[subset['run_id'] == latest_run].copy()
        
    # Sort by algorithm name or custom order
        order = ["fixed_time", "max_pressure", "offline_optimized", "mpc_dynamic", "hybrid_pressure_v2"]
        data = data[data['algorithm'].isin(order)].copy()
        data['algorithm'] = pd.Categorical(data['algorithm'], categories=order, ordered=True)
        data = data.sort_values('algorithm')
        
        print(r"% Comparative Study Results")
        for _, row in data.iterrows():
            algo = str(row['algorithm']).replace("_", " ").title()
            throughput = int(row['throughput'])
            delay = f"{row['avg_delay']:.2f}"
            gini = f"{row['fairness_gini']:.4f}"
            print(f"{algo} & {throughput} & {delay} & {gini} \\\\")
            
    # Stress Test Table
    subset = df[df['scenario'] == 'stress_test']
    if not subset.empty:
        print(r"% Stress Test Results")
        latest_run = subset['run_id'].max()
        data = subset[subset['run_id'] == latest_run].copy()
        order = ["fixed_time", "max_pressure", "mpc_dynamic", "hybrid_pressure_v2"]
        data = data[data['algorithm'].isin(order)].copy()
        data['algorithm'] = pd.Categorical(data['algorithm'], categories=order, ordered=True)
        data = data.sort_values('algorithm')
        
        for _, row in data.iterrows():
            algo = str(row['algorithm']).replace("_", " ").title()
            throughput = int(row['throughput'])
            delay = f"{row['avg_delay']:.2f}"
            gini = f"{row['fairness_gini']:.4f}"
            print(f"{algo} & {throughput} & {delay} & {gini} \\\\")

    # Robustness Table (Low Pen)
    subset = df[(df['scenario'] == 'robustness_test') & (df['day'] == 'Low_Pen')]
    if not subset.empty:
        print(r"% Robustness (Low Pen) Results")
        latest_run = subset['run_id'].max()
        data = subset[subset['run_id'] == latest_run].copy()
        
        order = ["fixed_time", "max_pressure", "mpc_dynamic", "hybrid_pressure_v2"]
        data = data[data['algorithm'].isin(order)].copy()
        data['algorithm'] = pd.Categorical(data['algorithm'], categories=order, ordered=True)
        data = data.sort_values('algorithm')
        
        for _, row in data.iterrows():
            algo = str(row['algorithm']).replace("_", " ").title()
            throughput = int(row['throughput'])
            delay = f"{row['avg_delay']:.2f}"
            gini = f"{row['fairness_gini']:.4f}"
            print(f"{algo} & {throughput} & {delay} & {gini} \\\\")
            
if __name__ == "__main__":
    generate_latex_table()
