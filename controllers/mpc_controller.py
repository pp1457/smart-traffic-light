from .base_controller import TrafficSignalController
import traci
from typing import List, Dict, Any

class MPCController(TrafficSignalController):
    def __init__(self, traffic_light_id, phase_sequence: List[Dict[str, Any]], queue_estimator, 
                 w_hist=1.0, w_av=1.0, horizon=10.0, fairness_weight=0.1, switching_cost=0.0, 
                 dynamic_switching=True, **kwargs):
        super().__init__(traffic_light_id, phase_sequence)
        self.queue_estimator = queue_estimator
        self.w_hist = w_hist # Not used directly, but kept for interface compat
        self.w_av = w_av     # Not used directly
        self.vote_collector = None # For interface compatibility with runner.py
        self.horizon = horizon
        self.fairness_weight = fairness_weight
        self.switching_cost = switching_cost
        self.dynamic_switching = dynamic_switching
        
        self.current_phase_index = 0
        self.time_in_current_phase = 0
        self.starvation_counters = {i: 0 for i in range(len(phase_sequence))}
        
        # Constants
        self.YELLOW_TIME = 5.0 # Assumed yellow time
        self.STARVATION_LIMIT = 120.0 # Seconds before forced switch

    def update_weights(self, penetration_rate):
        """
        Adaptively updates weights based on penetration rate.
        Matches HybridController logic.
        """
        self.w_hist = 1.0 * (1.0 - penetration_rate * 0.8)
        self.w_av = 1.0 + (penetration_rate * 2.0)
        print(f"[MPC] Updated weights for pen={penetration_rate:.2f}: w_hist={self.w_hist:.2f}, w_av={self.w_av:.2f}")

    def get_next_phase(self, current_step, day_type="weekday"):
        """
        Decides the next phase using MPC with Dynamic Phase Generation.
        """
        self.time_in_current_phase += 1
        
        current_config = self.phase_sequence[self.current_phase_index]
        min_green = current_config.get("min_green", 10)
        max_green = current_config.get("max_green", 60)
        
        # 0. Update Starvation Counters
        for i in range(len(self.phase_sequence)):
            if i != self.current_phase_index:
                self.starvation_counters[i] += 1
            else:
                self.starvation_counters[i] = 0

        # 1. Hard Constraints (Safety)
        # If Yellow, must finish yellow
        if not current_config.get("lanes"): # Yellow phase (empty lanes)
            if self.time_in_current_phase >= current_config["duration"]:
                self.time_in_current_phase = 0
                # Transition to the stored target phase
                if hasattr(self, 'next_green_phase'):
                    self.current_phase_index = self.next_green_phase
                else:
                    # Fallback to sequential if not set
                    self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_sequence)
            return self.current_phase_index
            
        # If Green, check Min Green
        if self.time_in_current_phase < min_green:
            return self.current_phase_index
            
        # Check Max Green
        if self.time_in_current_phase >= max_green:
            # Force Switch to next sequential (or could be smarter, but keep simple for safety)
            self.time_in_current_phase = 0
            # Default to next green in sequence
            next_idx = (self.current_phase_index + 1) % len(self.phase_sequence)
            while not self.phase_sequence[next_idx].get("lanes"):
                 next_idx = (next_idx + 1) % len(self.phase_sequence)
            
            self.next_green_phase = next_idx
            # Transition to Yellow first
            self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_sequence)
            return self.current_phase_index

        # Check Starvation (Fairness)
        for i, count in self.starvation_counters.items():
            if count > self.STARVATION_LIMIT:
                # Force switch to starving phase
                self.time_in_current_phase = 0
                self.next_green_phase = i
                # Transition to Yellow first
                self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_sequence)
                return self.current_phase_index

        # 2. MPC Optimization (Efficiency)
        # Evaluate switching to ANY Green Phase
        
        best_cost = float('inf')
        best_target_phase = self.current_phase_index
        
        # Identify candidates
        if self.dynamic_switching:
             # Dynamic: Consider ALL green phases
             candidates = [i for i, p in enumerate(self.phase_sequence) if p.get("lanes")]
        else:
             # Static: Consider only KEEP or NEXT SEQUENTIAL GREEN
             candidates = [self.current_phase_index]
             # Find next green
             next_idx = (self.current_phase_index + 1) % len(self.phase_sequence)
             while not self.phase_sequence[next_idx].get("lanes"):
                 next_idx = (next_idx + 1) % len(self.phase_sequence)
             candidates.append(next_idx)
        
        for target_phase in candidates:
            cost = self._evaluate_scenario(target_phase, current_step, day_type)
            
            # Add Switching Cost if target is not current
            if target_phase != self.current_phase_index:
                cost += self.switching_cost
            
            if cost < best_cost:
                best_cost = cost
                best_target_phase = target_phase
        
        # Decision
        if best_target_phase != self.current_phase_index:
            # Switch
            # print(f"[MPC] Switching from {self.current_phase_index} to {best_target_phase} (Cost: {best_cost:.1f})")
            self.time_in_current_phase = 0
            self.next_green_phase = best_target_phase
            # Transition to Yellow first
            # Note: We assume the next phase in sequence IS the yellow for current phase
            self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_sequence)
        else:
            # Keep
            pass
            
        return self.current_phase_index

    def _evaluate_scenario(self, target_phase_index, current_step, day_type):
        """
        Calculates the total cost for transitioning to target_phase_index.
        """
        current_lanes = self.phase_sequence[self.current_phase_index]["lanes"]
        
        if target_phase_index == self.current_phase_index:
            # KEEP Scenario
            next_lanes = [] # No next lanes active
            switch_time = self.horizon + 1.0 # Don't switch
        else:
            # SWITCH Scenario
            # We transition: Current -> Yellow -> Target
            next_lanes = self.phase_sequence[target_phase_index]["lanes"]
            switch_time = self.YELLOW_TIME # Next lanes start after Yellow
            
        # Get Historical Rates
        historical_rates = {}
        if hasattr(self, 'historical_demand_estimator') and self.historical_demand_estimator:
             all_lanes = []
             for p in self.phase_sequence:
                 if p.get("lanes"):
                     all_lanes.extend(p["lanes"])
             for lane in all_lanes:
                 demand = self.historical_demand_estimator.get_demand(current_step, lane, day_type)
                 historical_rates[lane] = demand / 3600.0
        else:
             # print("[MPC WARNING] No Historical Estimator attached!")
             pass
        
        predicted_queues = self.queue_estimator.predict(
            horizon_seconds=self.horizon,
            current_green_lanes=current_lanes,
            next_green_lanes=next_lanes,
            switch_time=switch_time,
            historical_rates=historical_rates
        )
        
        # Calculate Cost
        total_cost = 0.0
        for lane_id, queue_len in predicted_queues.items():
            # Fairness Weighting
            phase_idx = -1
            for i, p in enumerate(self.phase_sequence):
                if lane_id in p.get("lanes", []):
                    phase_idx = i
                    break
            
            weight = 1.0
            if phase_idx != -1:
                starvation = self.starvation_counters.get(phase_idx, 0)
                weight = 1.0 + (starvation / 60.0)**2 
            
            total_cost += (queue_len * weight)
            
        return total_cost
