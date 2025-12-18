import pandas as pd
import numpy as np
import json
import os
from xml.etree import ElementTree as ET

class HistoricalDemandEstimator:
    """
    Estimates baseline traffic demand from historical AV trajectory data
    using a simplified Newellian reconstruction method.
    """
    
    def __init__(self, file_path=None, penetration_rate=0.1):
        """
        Args:
            file_path (str, optional): Path to the historical tripinfo.xml file.
            penetration_rate (float): Assumed rate of AVs (0.0 to 1.0).
        """
        self.file_path = file_path
        self.penetration_rate = penetration_rate
        # Map: day_type (str) -> { time_bin (str) -> { movement_id (str) -> flow_rate (float) } }
        # time_bin is stringified int for JSON compatibility
        self.demand_profile = {} 

    def load_trajectories(self):
        """Parses the tripinfo.xml file."""
        if not self.file_path:
            return pd.DataFrame()
            
        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()
            records = []
            for tripinfo in root.findall('tripinfo'):
                records.append(tripinfo.attrib)
            return pd.DataFrame(records)
        except FileNotFoundError:
            print(f"Warning: Historical data file {self.file_path} not found.")
            return pd.DataFrame()

    def reconstruct_arrivals(self, day_type="weekday"):
        """
        Reconstructs total traffic flow from AV data for a specific day type.
        Args:
            day_type (str): "weekday" or "weekend"
        """
        df = self.load_trajectories()
        if df.empty:
            return

        # Convert columns
        df['depart'] = pd.to_numeric(df['depart'])
        
        # SIMPLIFICATION: Random sampling for AVs
        av_df = df.sample(frac=self.penetration_rate, random_state=42)
        
        # Calculate time bin (15 minutes = 900 seconds)
        av_df['time_bin'] = (av_df['depart'] // 900) * 900
        
        # Group by time_bin AND departLane (incoming lane)
        # Scale up: Total = AV_Count / Penetration_Rate
        grouped = av_df.groupby(['time_bin', 'departLane']).size() / self.penetration_rate
        
        # Initialize day_type dict if not exists
        if day_type not in self.demand_profile:
            self.demand_profile[day_type] = {}

        # Update internal profile
        for (time_bin, lane), count in grouped.items():
            time_key = str(int(time_bin))
            if time_key not in self.demand_profile[day_type]:
                self.demand_profile[day_type][time_key] = {}
            
            # Convert 15-min count to hourly flow rate
            flow_rate = count * 4
            self.demand_profile[day_type][time_key][lane] = flow_rate
            
        print(f"Reconstructed demand profile for {day_type} with {len(self.demand_profile[day_type])} time bins.")

    def get_demand(self, current_time, lane_id, day_type="weekday"):
        """
        Returns the estimated demand (vehicles/hour) for the current time and day type.
        """
        # Default to weekday if day_type not found
        if day_type not in self.demand_profile:
            # Try to fall back to any available day type or return 0
            if not self.demand_profile:
                return 0
            day_data = next(iter(self.demand_profile.values()))
        else:
            day_data = self.demand_profile[day_type]

        time_bin = (current_time // 900) * 900
        time_key = str(int(time_bin))
        
        bin_data = day_data.get(time_key, {})
        
        return bin_data.get(lane_id, 0)

    def save_profile(self, output_path):
        """Saves the learned demand profile to a JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.demand_profile, f, indent=4)
        print(f"Saved demand profile to {output_path}")

    def load_profile(self, input_path):
        """Loads a demand profile from a JSON file."""
        if os.path.exists(input_path):
            with open(input_path, 'r') as f:
                self.demand_profile = json.load(f)
            print(f"Loaded demand profile from {input_path}")
        else:
            print(f"Warning: Profile {input_path} not found.")
