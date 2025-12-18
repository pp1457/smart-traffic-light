from controllers import FixedTimeController, MaxPressureController, HybridController
from historical_demand import HistoricalDemandEstimator
from queue_estimator import ShockwaveQueueEstimator
import os

# --- Configuration ---
# Define the sequence of phases and their durations in seconds
# Lanes: E4=West->East, E5=North->South, E6=East->West, E7=South->North (Assumed based on standard SUMO grid)
PHASE_SEQUENCE = [
    {"phase_index": 0, "duration": 30, "min_green": 10, "max_green": 60, "lanes": ["E0_0", "E1_0"]}, # E-W Green (Incoming E0, E1)
    {"phase_index": 1, "duration": 5,  "min_green": 5,  "max_green": 5,  "lanes": []},             # E-W Yellow
    {"phase_index": 2, "duration": 30, "min_green": 10, "max_green": 60, "lanes": ["E2_0", "E3_0"]}, # N-S Green (Incoming E2, E3)
    {"phase_index": 3, "duration": 5,  "min_green": 5,  "max_green": 5,  "lanes": []}              # N-S Yellow
]

# Misconfigured Sequence (45s / 15s split) - Simulates poor calibration
def create_fixed_sequence(ew_green, ns_green):
    return [
        {"phase_index": 0, "duration": ew_green, "min_green": 10, "max_green": 60, "lanes": ["E0_0", "E1_0"]},
        {"phase_index": 1, "duration": 5,        "min_green": 5,  "max_green": 5,  "lanes": []},
        {"phase_index": 2, "duration": ns_green, "min_green": 10, "max_green": 60, "lanes": ["E2_0", "E3_0"]},
        {"phase_index": 3, "duration": 5,        "min_green": 5,  "max_green": 5,  "lanes": []}
    ]

# Pre-defined Sequences
PHASE_SEQ_30_30 = create_fixed_sequence(30, 30) # Optimal Mean
PHASE_SEQ_40_20 = create_fixed_sequence(40, 20) # Skewed EW
PHASE_SEQ_20_40 = create_fixed_sequence(20, 40) # Skewed NS
PHASE_SEQ_45_15 = create_fixed_sequence(45, 15) # Heavily Skewed EW (Misconfigured)

# Hybrid Control Configuration
WEIGHT_HISTORICAL = 1.0
WEIGHT_AV = 2.0
PRESSURE_THRESHOLD = 0.0 # Best found value from tuning

def get_controller(algorithm_name, traffic_light_id="J2", **kwargs):
    """
    Factory function to return the appropriate controller instance.
    """
    # Initialize Historical Demand Estimator and Queue Estimator once if needed by any controller
    tripinfo_file = "history.xml" # Use a dedicated history file
    historical_estimator = None
    if os.path.exists(tripinfo_file):
        historical_estimator = HistoricalDemandEstimator(tripinfo_file)
        # Try to load processed profile if available
        historical_estimator.load_profile("data/processed/demand_profile.json")
    else:
        print("Warning: No history.xml found. Hybrid/MPC controller will run without historical data.")
        
    queue_estimator = ShockwaveQueueEstimator()

    if algorithm_name == "fixed_time":
        return FixedTimeController(traffic_light_id, PHASE_SEQUENCE) # Default 30/30
    elif algorithm_name == "fixed_time_30_30":
        return FixedTimeController(traffic_light_id, PHASE_SEQ_30_30)
    elif algorithm_name == "fixed_time_40_20":
        return FixedTimeController(traffic_light_id, PHASE_SEQ_40_20)
    elif algorithm_name == "fixed_time_20_40":
        return FixedTimeController(traffic_light_id, PHASE_SEQ_20_40)
    elif algorithm_name == "fixed_time_45_15" or algorithm_name == "fixed_time_misconfigured":
        return FixedTimeController(traffic_light_id, PHASE_SEQ_45_15)
    elif algorithm_name == "max_pressure":
        return MaxPressureController(traffic_light_id, PHASE_SEQUENCE)
    elif algorithm_name == "hybrid":
        # Use the new MPC Controller as the "Hybrid" solution
        from controllers.mpc_controller import MPCController
        controller = MPCController(traffic_light_id, PHASE_SEQUENCE, queue_estimator, **kwargs)
        # Attach historical estimator
        controller.historical_demand_estimator = historical_estimator
        return controller
    elif algorithm_name == "hybrid_old":
        from controllers.hybrid_controller import HybridController
        return HybridController(traffic_light_id, PHASE_SEQUENCE, historical_estimator, queue_estimator=queue_estimator, **kwargs)
    elif algorithm_name == "hybrid_pressure":
        from controllers.hybrid_pressure_controller import HybridPressureController
        controller = HybridPressureController(traffic_light_id, PHASE_SEQUENCE, queue_estimator, **kwargs)
        controller.historical_demand_estimator = historical_estimator
        return controller
    elif algorithm_name == "offline_optimized":
        from controllers.offline_optimizer import OfflineOptimizer
        optimizer = OfflineOptimizer(historical_estimator, traffic_light_id, PHASE_SEQUENCE)
        # Optimize for the specific day type (assuming full day average for now)
        scale = kwargs.get("scale", 1.0)
        controller = optimizer.optimize(day_type=kwargs.get("day_type", "weekday"), demand_scale=scale)
        return controller
    elif algorithm_name == "hybrid_pressure_v2":
        from controllers.hybrid_pressure_controller_v2 import HybridPressureControllerV2
        controller = HybridPressureControllerV2(traffic_light_id, PHASE_SEQUENCE, queue_estimator, **kwargs)
        controller.historical_demand_estimator = historical_estimator
        return controller
    else:
        raise ValueError(f"Unknown algorithm: {algorithm_name}")
