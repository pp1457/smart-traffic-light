from dataclasses import dataclass
from typing import List, Dict, Optional
import time

# Constants
JAM_DENSITY_M_PER_VEH = 7.5 # Effective length of a vehicle in queue (meters)
SATURATION_FLOW_VEH_PER_SEC = 1800 / 3600 # 0.5 veh/sec
STOP_SPEED_THRESHOLD = 1.0 # m/s, below this considered stopped
DECAY_RATE = SATURATION_FLOW_VEH_PER_SEC

class ShockwaveQueueEstimator:
    """
    Estimates queue lengths using simplified Newellian Shockwave theory.
    It relies on the position of stopped AVs to determine the queue tail.
    """
    
    def __init__(self):
        # Map: lane_id -> estimated_vehicle_count
        self.queue_estimates: Dict[str, float] = {}
        self.last_update_time: Dict[str, float] = {}

    def update(self, current_time: float, av_messages: List['V2XMessage'], green_lanes: List[str], historical_rates: Dict[str, float]):
        """
        Updates queue estimates based on current AV messages, signal state, and historical demand.
        
        Args:
            current_time: Current simulation time.
            av_messages: List of V2X messages received in this step.
            green_lanes: List of lane IDs that currently have a green light.
            historical_rates: Map of lane_id -> arrival rate (veh/sec).
        """
        # Group messages by lane
        lane_msgs: Dict[str, List['V2XMessage']] = {}
        for msg in av_messages:
            if msg.lane_id not in lane_msgs:
                lane_msgs[msg.lane_id] = []
            lane_msgs[msg.lane_id].append(msg)
            
        # Update each lane
        all_known_lanes = set(self.queue_estimates.keys()) | set(lane_msgs.keys()) | set(historical_rates.keys())
        
        for lane_id in all_known_lanes:
            msgs = lane_msgs.get(lane_id, [])
            is_green = lane_id in green_lanes
            arrival_rate = historical_rates.get(lane_id, 0.0)
            self._update_lane(lane_id, current_time, msgs, is_green, arrival_rate)

    def _update_lane(self, lane_id: str, current_time: float, msgs: List['V2XMessage'], is_green: bool, arrival_rate: float):
        """
        Updates the estimate for a single lane using Continuous Integration + Correction.
        """
        last_time = self.last_update_time.get(lane_id, current_time)
        dt = current_time - last_time
        self.last_update_time[lane_id] = current_time
        
        # Track AVs for Demand Estimation
        self._track_av_arrival(lane_id, current_time, msgs)
        
        previous_estimate = self.queue_estimates.get(lane_id, 0.0)
        
        # 1. Continuous Integration (Prediction Step)
        # Q(t+dt) = Q(t) + Inflow - Outflow
        
        inflow = arrival_rate * dt
        outflow = 0.0
        
        if is_green:
            # If green, we discharge at saturation flow rate
            # But we can't discharge more than what we have
            outflow = SATURATION_FLOW_VEH_PER_SEC * dt
            
        predicted_queue = previous_estimate + inflow - outflow
        predicted_queue = max(0.0, predicted_queue) # Queue cannot be negative
        
        # 2. Measurement Correction (Update Step)
        # Identify stopped AVs (The "Probe" Vehicles)
        stopped_avs = [m for m in msgs if m.speed < STOP_SPEED_THRESHOLD]
        
        if len(msgs) > 0:
             # print(f"[Shockwave] Lane {lane_id}: {len(msgs)} msgs, {len(stopped_avs)} stopped")
             pass
        
        current_queue_observation = 0.0
        
        if stopped_avs:
            # Find the furthest stopped AV
            furthest_distance = max(m.distance_to_stop for m in stopped_avs)
            
            # Estimate queue based on this AV's position
            current_queue_observation = furthest_distance / JAM_DENSITY_M_PER_VEH
            
        # Fusion Logic:
        # The observation is a "Lower Bound" on the queue length.
        # If we see a car at 100m, the queue is AT LEAST 100m.
        # If our prediction is 50m, we were wrong -> Jump up to 100m.
        # If our prediction is 150m, we might be right (cars behind the AV), so we keep prediction?
        # OR, if we see the AV moving fast, we know the queue is clearing?
        
        # Simplified Fusion: Max(Prediction, Observation)
        # This ensures we never underestimate if we see a long queue.
        # But it might overestimate if we don't discharge fast enough.
        
        final_estimate = max(predicted_queue, current_queue_observation)
        
        # Special Case: If Green and No Stopped AVs?
        # If we predicted 20 cars, but we see 0 stopped AVs and maybe some moving AVs near the stop line?
        # This suggests the queue might have cleared faster or our history was too high.
        # For now, let's stick to the simple Max logic. The discharge rate should handle the clearing.
        
        self.queue_estimates[lane_id] = final_estimate

    def get_queue_length(self, lane_id: str) -> float:
        """
        Returns the current estimated queue length for a lane.
        """
        return self.queue_estimates.get(lane_id, 0.0)

    def predict(self, horizon_seconds: float, current_green_lanes: List[str], next_green_lanes: List[str], 
                switch_time: float, historical_rates: Dict[str, float]) -> Dict[str, float]:
        """
        Predicts queue lengths after `horizon_seconds`.
        
        Args:
            horizon_seconds: How far into the future to predict.
            current_green_lanes: Lanes currently green.
            next_green_lanes: Lanes that WILL be green if we switch.
            switch_time: Time from now when the switch happens (0 if immediate switch, infinity if keep).
            historical_rates: Arrival rates.
            
        Returns:
            Map of lane_id -> predicted queue length.
        """
        predicted_queues = {}
        all_lanes = set(self.queue_estimates.keys()) | set(historical_rates.keys())
        
        for lane_id in all_lanes:
            current_q = self.queue_estimates.get(lane_id, 0.0)
            arrival_rate = historical_rates.get(lane_id, 0.0)
            
            # Simulate forward
            # We simplify: Assume constant arrival.
            # Outflow depends on green status.
            
            # Calculate Green Time within the horizon for this lane
            green_time = 0.0
            
            if lane_id in current_green_lanes:
                # Currently Green
                if switch_time >= horizon_seconds:
                    # Stays green for whole horizon
                    green_time = horizon_seconds
                else:
                    # Green until switch, then Red (Yellow is effectively Red for discharge)
                    green_time = switch_time
            elif lane_id in next_green_lanes:
                # Currently Red, will become Green
                if switch_time < horizon_seconds:
                    # Becomes green after switch + yellow_time?
                    # Let's assume switch_time includes yellow penalty or we handle it in controller.
                    # For simplicity: Becomes green at switch_time.
                    green_time = horizon_seconds - switch_time
            
            inflow = arrival_rate * horizon_seconds
            outflow = SATURATION_FLOW_VEH_PER_SEC * green_time
            
            pred_q = current_q + inflow - outflow
            predicted_queues[lane_id] = max(0.0, pred_q)
            
        return predicted_queues

    def get_fused_demand(self, current_time: float, lane_id: str, historical_rate: float, alpha: float = 0.5, penetration: float = 0.15) -> float:
        """
        Calculates fused demand intensity (Lambda) using the formula:
        Lambda = alpha * D_real + (1 - alpha) * Lambda_hist
        
        Args:
            current_time: Current simulation time.
            lane_id: Lane ID.
            lane_id: Lane ID.
            historical_rate: Historical arrival rate (veh/sec).
            alpha: Fusion weight (0.0 = History only, 1.0 = AV only).
            penetration: AV Penetration rate (0.0 to 1.0).
            
        Returns:
            Fused demand estimate (veh/sec).
        """
        if penetration <= 0.01:
            # Avoid division by zero, trust history completely if no AVs expected
            return historical_rate
        # 1. Estimate Real-Time Demand (D_real) from AVs
        # We use a simple moving average of recent AV arrivals
        # In a real system, this would be a kernel density estimate
        
        window_size = 60.0 # Look back 60 seconds
        recent_avs = 0
        
        # We need to store AV arrival timestamps. 
        # For simplicity in this "v2" update without major refactoring, 
        # we will assume we have access to a list of recent AVs.
        # Since we don't track them yet, we need to add tracking in update().
        
        # Check if we have tracking data
        if not hasattr(self, 'av_arrival_history'):
            self.av_arrival_history = {} # lane_id -> list of timestamps
            
        history = self.av_arrival_history.get(lane_id, [])
        
        # Filter for window
        valid_history = [t for t in history if current_time - t <= window_size]
        self.av_arrival_history[lane_id] = valid_history # Cleanup
        
        av_count = len(valid_history)
        
        # D_real = AVs / Window / Penetration (Naive upscaling)
        # But we don't know penetration perfectly? 
        # The proposal says D_real is "arrival pulse from AVs".
        # Let's assume D_real is just the raw AV rate scaled by an assumed penetration
        # or just the AV rate if we treat alpha as the "trust" in AVs.
        # Let's use a simple rate:
        d_real = av_count / window_size
        
        # Upscale d_real? If alpha handles the "weight", maybe we don't need to upscale?
        # Proposal: "down-weight implausible ETAs... Fuse demand... alpha * D_real..."
        # Usually D_real should be "Total Estimated Real Demand".
        # So we should divide by penetration if we want it to be comparable to historical_rate.
        # Let's assume a fixed penetration estimate for now (e.g., 0.15) or pass it in.
        # For this implementation, we'll assume D_real is *normalized* to be comparable.
        # So we multiply AV rate by (1/penetration).
        
        # Use the actual known penetration rate (or estimated)
        d_real_total = d_real / max(penetration, 0.01)
        
        # 2. Fuse
        fused_demand = alpha * d_real_total + (1 - alpha) * historical_rate
        
        return fused_demand

    def _track_av_arrival(self, lane_id: str, current_time: float, msgs: List['V2XMessage']):
        """
        Helper to track unique AV arrivals.
        """
        if not hasattr(self, 'av_arrival_history'):
            self.av_arrival_history = {}
            self.seen_av_ids = {} # lane_id -> set of veh_ids
            
        if lane_id not in self.av_arrival_history:
            self.av_arrival_history[lane_id] = []
            self.seen_av_ids[lane_id] = set()
            
        # We only want to count NEW arrivals in this lane
        # This is tricky without persistent IDs across steps.
        # But msgs contain all current AVs.
        # We can check if a vehicle ID is new to this lane *recently*.
        
        current_ids = set(m.vehicle_id for m in msgs)
        
        # Identify new IDs
        new_ids = current_ids - self.seen_av_ids[lane_id]
        
        for vid in new_ids:
            self.av_arrival_history[lane_id].append(current_time)
            
        # Update seen set (keep only current)
        self.seen_av_ids[lane_id] = current_ids
