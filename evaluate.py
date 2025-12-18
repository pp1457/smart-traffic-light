"""
This script analyzes the SUMO simulation outputs (tripinfo.xml) to evaluate
the performance of the traffic signal control logic based on the metrics
defined in the research proposal.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from xml.etree import ElementTree as ET

def parse_tripinfo(file_path):
    """Parses the tripinfo.xml file and returns a pandas DataFrame."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    records = []
    for tripinfo in root.findall('tripinfo'):
        records.append(tripinfo.attrib)
        
    return pd.DataFrame(records)

def calculate_gini(x):
    """Calculate the Gini coefficient of a numpy array."""
    # based on https://stackoverflow.com/a/39513799
    total = 0
    for i, xi in enumerate(x[:-1], 1):
        total += np.sum(np.abs(xi - x[i:]))
    return total / (len(x)**2 * np.mean(x))

def evaluate_results(trip_df):
    """
    Calculates and prints key performance metrics based on the proposal.
    
    Args:
        trip_df (pd.DataFrame): DataFrame containing trip information.
    """
    # Convert relevant columns to numeric types
    numeric_cols = ['duration', 'timeLoss', 'waitingTime']
    for col in numeric_cols:
        trip_df[col] = pd.to_numeric(trip_df[col], errors='coerce')
    
    # --- Primary Evaluation Metrics (from proposal.md) ---
    
    # 1. Intersection Throughput
    total_vehicles = len(trip_df)
    simulation_time_hours = (trip_df['depart'].astype(float).max() - trip_df['depart'].astype(float).min()) / 3600
    throughput = total_vehicles / simulation_time_hours if simulation_time_hours > 0 else 0
    
    # 2. Average Delay (using timeLoss)
    average_delay = trip_df['timeLoss'].mean()
    
    # 3. Fairness Index (Gini coefficient of vehicle delays)
    # We use timeLoss as the measure of delay for the Gini coefficient
    delays = trip_df['timeLoss'].dropna().to_numpy()
    fairness_gini = calculate_gini(delays) if len(delays) > 1 else 0
    
    print("\n--- Primary Evaluation Metrics ---")
    print(f"Intersection Throughput: {throughput:.2f} vehicles/hour")
    print(f"Average Delay (timeLoss): {average_delay:.2f} seconds/vehicle")
    print(f"Fairness Index (Gini of Delay): {fairness_gini:.4f}")
    print("------------------------------------")
    
    # --- Additional Detailed Metrics ---
    avg_wait_time = trip_df['waitingTime'].mean()
    delay_variance = trip_df['timeLoss'].var()
    
    print("\n--- Detailed Statistics ---")
    print(f"Total Vehicles Processed: {total_vehicles}")
    print(f"Average Waiting Time: {avg_wait_time:.2f} seconds")
    print(f"Delay Variance: {delay_variance:.2f}")
    print("---------------------------\n")
    
    return {
        "throughput": throughput,
        "average_delay": average_delay,
        "fairness_gini": fairness_gini,
        "avg_wait_time": avg_wait_time,
        "delay_variance": delay_variance
    }

def plot_results(trip_df):
    """
    Generates and saves plots for key performance indicators.
    """
    # Convert relevant columns to numeric types
    numeric_cols = ['duration', 'timeLoss', 'waitingTime']
    for col in numeric_cols:
        trip_df[col] = pd.to_numeric(trip_df[col], errors='coerce')

    # Plot 1: Histogram of Delays (timeLoss)
    plt.figure(figsize=(10, 6))
    trip_df['timeLoss'].hist(bins=30, alpha=0.7)
    plt.title('Distribution of Vehicle Delays (timeLoss)')
    plt.xlabel('Delay (seconds)')
    plt.ylabel('Number of Vehicles')
    plt.grid(axis='y')
    plt.savefig('delay_distribution.png')
    print("Saved delay distribution plot to 'delay_distribution.png'")

    # Plot 2: Histogram of Waiting Times
    plt.figure(figsize=(10, 6))
    trip_df['waitingTime'].hist(bins=30, alpha=0.7, color='orange')
    plt.title('Distribution of Vehicle Waiting Times')
    plt.xlabel('Waiting Time (seconds)')
    plt.ylabel('Number of Vehicles')
    plt.grid(axis='y')
    plt.savefig('waiting_time_distribution.png')
    print("Saved waiting time distribution plot to 'waiting_time_distribution.png'")


if __name__ == "__main__":
    TRIPINFO_FILE = 'tripinfo.xml'
    
    try:
        # 1. Parse the tripinfo file
        trip_data = parse_tripinfo(TRIPINFO_FILE)
        
        # 2. Evaluate the results based on the proposal's metrics
        evaluate_results(trip_data)
        
        # 3. Generate and save plots
        plot_results(trip_data)
        
    except FileNotFoundError:
        print(f"Error: '{TRIPINFO_FILE}' not found. Please run the simulation first.")
    except Exception as e:
        print(f"An error occurred: {e}")

