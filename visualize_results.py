import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

RESULTS_FILE = "data/results/experiment_log.csv"
OUTPUT_DIR = "data/results/plots"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_data():
    if not os.path.exists(RESULTS_FILE):
        print(f"No results file found at {RESULTS_FILE}")
        return None
    return pd.read_csv(RESULTS_FILE)

def plot_fairness_comparison(df):
    """
    Bar chart comparing Gini Coefficient across algorithms for the 'comparative_study' scenario.
    """
    # Filter for comparative study and latest run
    # We assume the latest run_id is the one we want, or we aggregate
    # Let's take the latest run_id for 'comparative_study'
    
    subset = df[df['scenario'] == 'comparative_study']
    if subset.empty:
        print("No comparative_study data found.")
        return

    # Get latest run_id
    latest_run = subset['run_id'].max()
    data = subset[subset['run_id'] == latest_run]
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=data, x='algorithm', y='fairness_gini', palette='viridis')
    plt.title(f'Fairness Comparison (Gini Coefficient) - Run {latest_run}')
    plt.ylabel('Gini Coefficient (Lower is Fairer)')
    plt.xlabel('Algorithm')
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    
    ensure_dir(OUTPUT_DIR)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fairness_comparison.png'))
    print(f"Saved fairness plot to {OUTPUT_DIR}/fairness_comparison.png")

def plot_delay_comparison(df):
    """
    Bar chart comparing Average Delay.
    """
    subset = df[df['scenario'] == 'comparative_study']
    if subset.empty:
        return

    latest_run = subset['run_id'].max()
    data = subset[subset['run_id'] == latest_run]
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=data, x='algorithm', y='avg_delay', palette='magma')
    plt.title(f'Average Delay Comparison - Run {latest_run}')
    plt.ylabel('Average Delay (s)')
    plt.xlabel('Algorithm')
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    
    ensure_dir(OUTPUT_DIR)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'delay_comparison.png'))
    print(f"Saved delay plot to {OUTPUT_DIR}/delay_comparison.png")

def plot_sensitivity_analysis(df):
    """
    Line chart showing Delay vs Penetration Rate for 'sensitivity_analysis'.
    """
    subset = df[df['scenario'] == 'sensitivity_analysis']
    if subset.empty:
        print("No sensitivity_analysis data found.")
        return

    # Get latest run_id (approximate, since sensitivity runs multiple sims)
    # Actually, we should group by algorithm and penetration
    # Filter for the latest run batch
    latest_timestamp = subset['timestamp'].max()
    # This might be tricky if they have slightly different timestamps.
    # Let's just take the last 20 records or filter by run_id if consistent.
    latest_run = subset['run_id'].max()
    data = subset[subset['run_id'] == latest_run]
    
    if data.empty:
        # Fallback to all data if run_id matching fails
        data = subset
        
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=data, x='penetration', y='avg_delay', hue='algorithm', marker='o')
    plt.title(f'Sensitivity Analysis: Delay vs AV Penetration')
    plt.ylabel('Average Delay (s)')
    plt.xlabel('AV Penetration Rate')
    plt.grid(True, alpha=0.3)
    
    ensure_dir(OUTPUT_DIR)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'sensitivity_analysis.png'))
    print(f"Saved sensitivity plot to {OUTPUT_DIR}/sensitivity_analysis.png")

def plot_stress_test(df):
    """
    Bar chart for Stress Test (Peak Hour) comparison.
    """
    subset = df[df['scenario'] == 'stress_test']
    if subset.empty:
        print("No stress_test data found.")
        return

    latest_run = subset['run_id'].max()
    data = subset[subset['run_id'] == latest_run].copy()
    
    # Sort for visual consistency
    order = ["fixed_time", "max_pressure", "mpc_static", "mpc_dynamic", "hybrid_pressure_v2"]
    data = data[data['algorithm'].isin(order)]
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=data, x='algorithm', y='avg_delay', palette='rocket')
    plt.title(f'Stress Test: Average Delay under 1.5x Demand')
    plt.ylabel('Average Delay (s)')
    plt.xlabel('Algorithm')
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    
    ensure_dir(OUTPUT_DIR)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'stress_test_comparison.png'))
    print(f"Saved stress test plot to {OUTPUT_DIR}/stress_test_comparison.png")

def plot_robustness_test(df):
    """
    Clustered bar chart for Robustness Test (Low vs Med Penetration).
    """
    subset = df[df['scenario'] == 'robustness_test']
    if subset.empty:
        print("No robustness_test data found.")
        return

    latest_run = subset['run_id'].max()
    data = subset[subset['run_id'] == latest_run].copy()
    
    order = ["fixed_time", "max_pressure", "mpc_dynamic", "hybrid_pressure_v2"]
    data = data[data['algorithm'].isin(order)]
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=data, x='algorithm', y='avg_delay', hue='day', palette='mako')
    plt.title(f'Robustness: Performance at Low (5%) vs Med (20%) Penetration')
    plt.ylabel('Average Delay (s)')
    plt.xlabel('Algorithm')
    plt.xticks(rotation=45)
    plt.legend(title='Scenario')
    plt.grid(axis='y', alpha=0.3)
    
    ensure_dir(OUTPUT_DIR)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'robustness_comparison.png'))
    print(f"Saved robustness plot to {OUTPUT_DIR}/robustness_comparison.png")

def plot_fairness_sensitivity(df):
    """
    Line chart showing Gini Coefficient vs Penetration Rate for 'sensitivity_analysis'.
    """
    subset = df[df['scenario'] == 'sensitivity_analysis']
    if subset.empty:
        return

    latest_run = subset['run_id'].max()
    data = subset[subset['run_id'] == latest_run]
    
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=data, x='penetration', y='fairness_gini', hue='algorithm', marker='s')
    plt.title(f'Equity Analysis: Fairness (Gini) vs AV Penetration')
    plt.ylabel('Gini Coefficient (Lower is Fairer)')
    plt.xlabel('AV Penetration Rate')
    plt.grid(True, alpha=0.3)
    
    ensure_dir(OUTPUT_DIR)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fairness_sensitivity.png'))
    print(f"Saved fairness sensitivity plot to {OUTPUT_DIR}/fairness_sensitivity.png")

def plot_throughput_sensitivity(df):
    """
    Line chart showing Throughput vs Penetration Rate for 'sensitivity_analysis'.
    """
    subset = df[df['scenario'] == 'sensitivity_analysis']
    if subset.empty:
        return

    latest_run = subset['run_id'].max()
    data = subset[subset['run_id'] == latest_run]
    
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=data, x='penetration', y='throughput', hue='algorithm', marker='^')
    plt.title(f'Throughput Analysis: Vehicles Served vs AV Penetration')
    plt.ylabel('Throughput (veh/hr)')
    plt.xlabel('AV Penetration Rate')
    plt.grid(True, alpha=0.3)
    
    ensure_dir(OUTPUT_DIR)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'throughput_sensitivity.png'))
    print(f"Saved throughput sensitivity plot to {OUTPUT_DIR}/throughput_sensitivity.png")

def main():
    df = load_data()
    if df is not None:
        plot_fairness_comparison(df)
        plot_delay_comparison(df)
        plot_sensitivity_analysis(df)
        plot_stress_test(df)
        plot_robustness_test(df)
        plot_fairness_sensitivity(df)
        plot_throughput_sensitivity(df)

if __name__ == "__main__":
    main()
