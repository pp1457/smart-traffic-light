"""
This file will contain the main simulation runner.
It will start SUMO, connect to it using TraCI, and run the simulation step-by-step.
The traffic light control logic will be imported from signal_control_algorithm.py.
"""
import os
import sys

# Check for SUMO_HOME
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
from sumolib import checkBinary # For checkBinary function
from signal_control_algorithm import get_controller

# --- Simulation Setup ---
CONFIG_FILE = "hello.sumocfg"
SIMULATION_STEPS = 3600 # Run for 1 hour (3600 seconds)
TRAFFIC_LIGHT_ID = "J2"

import datetime
import shutil
import argparse

from v2x_manager import V2XMessage
import hashlib

def is_av(vehicle_id, penetration_rate=0.1):
    """
    Deterministically decides if a vehicle is an AV based on its ID.
    """
    # Use a hash of the ID to get a consistent number between 0 and 1
    hash_val = int(hashlib.md5(vehicle_id.encode()).hexdigest(), 16)
    normalized_hash = (hash_val % 1000) / 1000.0
    return normalized_hash < penetration_rate

def run_simulation(sumo_binary, algorithm_name, output_file=None, w_hist=1.0, w_av=2.0, threshold=10.0, 
                   horizon=10.0, fairness=0.1, switching_cost=0.0, penetration_rate=0.05, day_type="weekday",
                   dynamic_switching=True, alpha=0.5, beta=0.5, scale=1.0):
    """Runs the SUMO simulation with the specified controller."""
    
    # Start SUMO as a subprocess and connect with TraCI
    # We need to specify the output file in the SUMO command if provided
    sumo_cmd = [sumo_binary, "-c", "hello.sumocfg"]
    if output_file:
        sumo_cmd.extend(["--tripinfo-output", output_file])
    else:
        sumo_cmd.extend(["--tripinfo-output", "tripinfo.xml"])
    
    # Debugging: Log internal SUMO errors
    sumo_cmd.extend(["--log", "sumo_debug.log"])

    print(f"Executing SUMO command: {' '.join(sumo_cmd)}")
        
    traci.start(sumo_cmd)
    
    # Initialize the controller
    # Pass tuning parameters as kwargs
    controller = get_controller(algorithm_name, TRAFFIC_LIGHT_ID, 
                                w_hist=w_hist, w_av=w_av, pressure_threshold=threshold,
                                horizon=horizon, fairness_weight=fairness, switching_cost=switching_cost,
                                dynamic_switching=dynamic_switching,
                                alpha=alpha, beta=beta, scale=scale)
    
    # Adaptive Weights
    if hasattr(controller, 'update_weights'):
        controller.update_weights(penetration_rate)
        
    print(f"Running simulation with {algorithm_name} controller (Penetration: {penetration_rate}, Day: {day_type})...")
    
    step = 0
    while step < SIMULATION_STEPS and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # --- V2X Simulation ---
        if algorithm_name in ['hybrid', 'hybrid_pressure', 'hybrid_pressure_v2']:
            # Collect all AV messages for this step
            av_messages = []
            vehicle_ids = traci.vehicle.getIDList()
            for vid in vehicle_ids:
                if is_av(vid, penetration_rate):
                    lane_id = traci.vehicle.getLaneID(vid)
                    speed = traci.vehicle.getSpeed(vid)
                    lane_len = traci.lane.getLength(lane_id)
                    pos = traci.vehicle.getLanePosition(vid)
                    dist = lane_len - pos
                    
                    msg = V2XMessage(
                        vehicle_id=vid,
                        lane_id=lane_id,
                        speed=speed,
                        distance_to_stop=dist,
                        estimated_arrival_time=step + (dist / max(speed, 0.1))
                    )
                    av_messages.append(msg)
                    
                    if hasattr(controller, 'vote_collector') and controller.vote_collector:
                        controller.vote_collector.collect_vote(msg)
            
            if hasattr(controller, 'queue_estimator') and controller.queue_estimator:
                # 1. Get Green Lanes
                # We need to know which lanes are currently green to allow discharge
                # The controller knows the current phase index
                # But we can also ask TraCI
                current_phase_idx = traci.trafficlight.getPhase(TRAFFIC_LIGHT_ID)
                # We need to map phase index to lanes.
                # Ideally we should ask the controller for this mapping or use the one in signal_control_algorithm
                # For now, let's access the controller's phase_sequence if available
                green_lanes = []
                if hasattr(controller, 'phase_sequence'):
                    phase_config = controller.phase_sequence[current_phase_idx]
                    if phase_config.get("lanes"):
                        green_lanes = phase_config["lanes"]
                
                # 2. Get Historical Rates
                # We need arrival rates (veh/sec) for all relevant lanes
                # The estimator has get_demand(step, lane, day_type) which returns veh/hr
                historical_rates = {}
                if hasattr(controller, 'historical_demand_estimator') and controller.historical_demand_estimator:
                    # We need the list of all lanes we care about.
                    # Let's assume all lanes in the phase sequence.
                    all_lanes = []
                    if hasattr(controller, 'phase_sequence'):
                         for p in controller.phase_sequence:
                             if p.get("lanes"):
                                 all_lanes.extend(p["lanes"])
                    
                    for lane in all_lanes:
                        demand_veh_hr = controller.historical_demand_estimator.get_demand(step, lane, day_type)
                        historical_rates[lane] = demand_veh_hr / 3600.0 # Convert to veh/sec
                
                controller.queue_estimator.update(step, av_messages, green_lanes, historical_rates)

        # --- Control Logic ---
        # Get the next phase from the controller
        # Pass day_type if hybrid
        if algorithm_name in ['hybrid', 'hybrid_pressure', 'hybrid_pressure_v2']:
            next_phase_index = controller.get_next_phase(step, day_type=day_type)
        else:
            next_phase_index = controller.get_next_phase(step)
        
        # If the current phase is different from the new one, set it
        if traci.trafficlight.getPhase(TRAFFIC_LIGHT_ID) != next_phase_index:
            traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, next_phase_index)
        
        step += 1

    traci.close()
    print("Simulation finished.")
    
    # --- Data Management ---
    # If output_file was provided, SUMO already saved it there.
    # If not, we do our default timestamped saving.
    if not output_file:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_tripinfo = f"data/raw/tripinfo_{timestamp}.xml"
        if os.path.exists("tripinfo.xml"):
            shutil.move("tripinfo.xml", raw_tripinfo)
            print(f"Saved raw tripinfo to {raw_tripinfo}")
            output_file = raw_tripinfo # For the estimator below

    # 2. Update and Save Processed Profile (if Hybrid)
    if algorithm_name in ['hybrid', 'hybrid_pressure', 'hybrid_pressure_v2']:
        # The controller has the estimator
        estimator = controller.historical_demand_estimator
        if estimator and output_file and os.path.exists(output_file):
            # Load the just-generated raw data to learn from this run
            estimator.file_path = output_file
            estimator.reconstruct_arrivals(day_type=day_type)
            
            # Save the updated profile
            profile_path = "data/processed/demand_profile.json"
            estimator.save_profile(profile_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SUMO simulation with specific controller.")
    parser.add_argument("--algorithm", type=str, default="fixed_time", help="Control algorithm (fixed_time, max_pressure, hybrid)")
    parser.add_argument("--output", type=str, help="Path to save tripinfo.xml output")
    parser.add_argument("--gui", action="store_true", help="Run with GUI")
    
    # Tuning parameters
    parser.add_argument("--w_hist", type=float, default=1.0, help="Weight for historical demand")
    parser.add_argument("--w_av", type=float, default=2.0, help="Weight for AV votes")
    parser.add_argument("--threshold", type=float, default=10.0, help="Pressure threshold for switching")
    parser.add_argument("--horizon", type=float, default=10.0, help="MPC prediction horizon")
    parser.add_argument("--fairness", type=float, default=0.1, help="MPC fairness weight")
    parser.add_argument("--switching_cost", type=float, default=0.0, help="MPC switching cost")
    parser.add_argument("--alpha", type=float, default=0.5, help="Fusion weight (alpha)")
    parser.add_argument("--beta", type=float, default=0.5, help="Spillback weight (beta)")
    
    # Penetration rate
    parser.add_argument("--penetration", type=float, default=0.1, help="AV Penetration Rate (0.0 to 1.0)")
    
    # Day Type
    parser.add_argument("--day_type", type=str, default="weekday", help="Day type (weekday/weekend)")
    parser.add_argument("--scale", type=float, default=1.0, help="Traffic demand scale")
    
    # Dynamic Switching
    parser.add_argument("--disable_dynamic", action="store_true", help="Disable dynamic phase generation (Static MPC)")
    
    args = parser.parse_args()
    
    # Allow running without the GUI
    if args.gui:
        sumo_binary = checkBinary('sumo-gui')
    else:
        sumo_binary = checkBinary('sumo')
        
    run_simulation(sumo_binary, args.algorithm, args.output, 
                   w_hist=args.w_hist, w_av=args.w_av, threshold=args.threshold,
                   horizon=args.horizon, fairness=args.fairness, switching_cost=args.switching_cost,
                   penetration_rate=args.penetration, day_type=args.day_type,
                   dynamic_switching=not args.disable_dynamic,
                   alpha=args.alpha, beta=args.beta, scale=args.scale)
