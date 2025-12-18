import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configuration
LOG_FILE = "data/results/experiment_log.csv"
OUTPUT_DIR = "data/results/plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def visualize_split_sensitivity():
    print("Loading data...")
    try:
        df = pd.read_csv(LOG_FILE)
    except FileNotFoundError:
        print(f"Error: Log file not found at {LOG_FILE}")
        return

    # Filter for the split_sensitivity scenario
    df_split = df[df['scenario'] == 'split_sensitivity'].copy()
    
    if df_split.empty:
        print("No data found for 'split_sensitivity' scenario.")
        return

    # Extract Split Ratio from algorithm name
    # Format: fixed_time_XX_YY -> Ratio = XX / (XX+YY)
    def get_split_ratio(algo):
        if "mpc" in algo:
            return "MPC (Adaptive)"
        parts = algo.split('_')
        if len(parts) >= 4: # fixed_time_30_30
            try:
                g1 = int(parts[2])
                g2 = int(parts[3])
                total = g1 + g2
                return g1 / total
            except:
                return "Unknown"
        return "Unknown"

    df_split['split_ratio'] = df_split['algorithm'].apply(get_split_ratio)
    
    # Separate MPC and Fixed Time
    df_mpc = df_split[df_split['algorithm'].str.contains('mpc')]
    df_fixed = df_split[~df_split['algorithm'].str.contains('mpc')]
    
    # Sort Fixed Time by ratio
    df_fixed['split_ratio_val'] = df_fixed['split_ratio'].astype(float)
    df_fixed = df_fixed.sort_values('split_ratio_val')

    # Aggregating if multiple runs exist (mean)
    mpc_delay = df_mpc['avg_delay'].mean()
    
    # Plotting
    plt.figure(figsize=(10, 6))
    
    # Plot Fixed Time Curve
    plt.plot(df_fixed['split_ratio_val'], df_fixed['avg_delay'], marker='o', linestyle='-', linewidth=2, label='Fixed Time (Manual)')
    
    # Plot MPC Line (Horizontal)
    plt.axhline(y=mpc_delay, color='r', linestyle='--', linewidth=2, label=f'MPC (Adaptive, {mpc_delay:.1f}s)')
    
    # Annotations
    plt.title("Impact of Green Split calibration on Average Delay", fontsize=16)
    plt.xlabel("East-West Green Split Ratio (Green / Cycle)", fontsize=14)
    plt.ylabel("Average Delay (s)", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    
    # Highlight Optimal Split
    optimal_row = df_fixed.loc[df_fixed['avg_delay'].idxmin()]
    plt.annotate(f"Optimal Fixed\n({optimal_row['avg_delay']:.1f}s)", 
                 xy=(optimal_row['split_ratio_val'], optimal_row['avg_delay']), 
                 xytext=(optimal_row['split_ratio_val'], optimal_row['avg_delay'] + 10),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 ha='center')

    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "split_sensitivity.png")
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    visualize_split_sensitivity()
