import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

LOG_FILE = "data/results/queue_dynamics.csv"
OUTPUT_FILE = "data/results/plots/queue_dynamics.png"

def plot_queue_dynamics():
    if not os.path.exists(LOG_FILE):
        print("No log file found.")
        return

    df = pd.read_csv(LOG_FILE)
    
    # Filter for a subset of time to make it readable (e.g., first 600 seconds)
    df = df[df['time'] <= 600]
    
    # Filter: Show only top 3 busiest lanes to avoid clutter
    top_lanes = df.groupby('lane')['queue_length'].max().nlargest(3).index
    df = df[df['lane'].isin(top_lanes)]

    sns.set_context("paper", font_scale=1.5)
    plt.figure(figsize=(10, 5)) # Wide aspect ratio
    sns.lineplot(data=df, x='time', y='queue_length', hue='lane', linewidth=2.5)
    
    plt.title('Queue Dynamics: Hybrid Controller (Top 3 Lanes)', fontsize=14, fontweight='bold')
    plt.ylabel('Queue Length (veh)', fontsize=12)
    plt.xlabel('Simulation Time (s)', fontsize=12)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    if not os.path.exists("data/results/plots"):
        os.makedirs("data/results/plots")
        
    plt.savefig(OUTPUT_FILE)
    print(f"Saved queue dynamics plot to {OUTPUT_FILE}")

if __name__ == "__main__":
    plot_queue_dynamics()
