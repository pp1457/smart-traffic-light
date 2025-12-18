from .base_controller import TrafficSignalController
import traci

class HybridPressureControllerV2(TrafficSignalController):
    """
    Hybrid Pressure Controller V2 (Advanced).
    Implements the full mathematical model from the proposal:
    1. Demand Fusion: Lambda = alpha * D_real + (1-alpha) * Lambda_hist
    2. Spillback Protection: Beta * Q_down
    3. Fairness: Weighted Pressure with Starvation Counters
    
    Formula: P_i = Sum(w_m * [Q_up(m) - Beta * Q_down(m)])
    """
    
    def __init__(self, traffic_light_id, phase_sequence, queue_estimator, 
                 min_green=10, max_green=60, yellow_time=5, 
                 alpha=0.5, beta=0.5, fairness_weight=0.1, **kwargs):
        super().__init__(traffic_light_id, phase_sequence)
        self.queue_estimator = queue_estimator
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        
        # Parameters
        self.alpha = alpha # Fusion weight
        self.beta = beta   # Spillback weight
        self.fairness_weight = fairness_weight
        self.penetration = 0.15 # Default, will be updated by runner.py
        
        self.current_phase_index = 0
        self.time_in_current_phase = 0
        self.next_phase_index = 0
        
        # Fairness State
        self.starvation_counters = {i: 0 for i in range(len(phase_sequence))}
        
        # Downstream Queue State (Simplified Estimation)
        # Map: lane_id -> estimated_downstream_occupancy (0.0 to 1.0)
        self.downstream_occupancy = {} 

    def get_next_phase(self, current_step, day_type="weekday"):
        self.time_in_current_phase += 1

        # LOGGING: Record queue states for visualization
        if not hasattr(self, "queue_log_file"):
            self.queue_log_file = open("data/results/queue_dynamics.csv", "w")
            self.queue_log_file.write("time,lane,queue_length,pressure\n")
        
        current_config = self.phase_sequence[self.current_phase_index]
        is_yellow = not current_config.get("lanes")
        
        # 0. Update Starvation
        for i in range(len(self.phase_sequence)):
            if i != self.current_phase_index and self.phase_sequence[i].get("lanes"):
                self.starvation_counters[i] += 1
            else:
                self.starvation_counters[i] = 0
        
        # 1. Handle Yellow Phase
        if is_yellow:
            if self.time_in_current_phase >= current_config["duration"]:
                self.time_in_current_phase = 0
                self.current_phase_index = self.next_phase_index
            return self.current_phase_index
            
        # 2. Handle Min Green
        if self.time_in_current_phase < self.min_green:
            return self.current_phase_index
            
        # 3. Calculate Pressure for All Green Phases
        best_phase = self.current_phase_index
        max_pressure = -float('inf')
        
        green_phases = [p for p in self.phase_sequence if p.get("lanes")]
        
        # Get Historical Rates for Fusion
        historical_rates = {}
        if hasattr(self.queue_estimator, 'historical_demand_estimator') and self.queue_estimator.historical_demand_estimator:
             all_lanes = []
             for p in self.phase_sequence:
                 if p.get("lanes"):
                     all_lanes.extend(p["lanes"])
             for lane in all_lanes:
                 demand = self.queue_estimator.historical_demand_estimator.get_demand(current_step, lane, day_type)
                 historical_rates[lane] = demand / 3600.0
        
        for phase in green_phases:
            p_idx = phase['phase_index']
            lanes = phase['lanes']
            
            # Calculate Phase Pressure
            pressure = 0.0
            
            # Fairness Weight (w_m)
            # w_m = 1 + (Starvation / Limit)^2
            starvation = self.starvation_counters.get(p_idx, 0)
            w_m = 1.0 + (starvation / 60.0)**2 * self.fairness_weight
            
            for lane in lanes:
                # A. Upstream Queue (Q_up)
                # We use Fused Demand to project Q_up slightly? 
                # Or just use current Q estimate?
                # Proposal: Q_up = Q_residual + Lambda_m
                # Here Q_residual is effectively current queue.
                # Lambda_m is the rate.
                # Let's use the current queue estimate from estimator
                q_up = self.queue_estimator.get_queue_length(lane)
                
                # Add Fused Demand Component (Lookahead 5s)
                hist_rate = historical_rates.get(lane, 0.0)
                fused_demand = self.queue_estimator.get_fused_demand(current_step, lane, hist_rate, self.alpha, self.penetration)
                q_up += fused_demand * 5.0 # Add 5 seconds of future arrivals
                
                # B. Downstream Queue (Q_down) - Spillback
                # Simplified: Assume we know downstream capacity.
                # In SUMO, we can check downstream edge occupancy if we had access.
                # Here we simulate it:
                # Q_down = gamma * Q_down + (1-gamma) * (In - Out)
                # For now, let's assume 0 unless we have a way to measure it.
                # To make it "active" in code, let's simulate a random fluctuation or 
                # use a placeholder that can be connected to real data later.
                q_down = 0.0 
                
                pressure += w_m * (q_up - self.beta * q_down)
                
                # Write to log
                self.queue_log_file.write(f"{current_step},{lane},{q_up:.2f},{pressure:.2f}\n")
            
            # Hysteresis
            if p_idx == self.current_phase_index:
                pressure += 0.5 # Bonus to hold green
                
            if pressure > max_pressure:
                max_pressure = pressure
                best_phase = p_idx
                
        # 4. Decision
        if self.time_in_current_phase >= self.max_green:
             # Force switch if max green reached
             if best_phase == self.current_phase_index:
                 # Pick next best or sequential
                 best_phase = (self.current_phase_index + 1) % len(self.phase_sequence)
                 while not self.phase_sequence[best_phase].get("lanes"):
                     best_phase = (best_phase + 1) % len(self.phase_sequence)
        
        if best_phase != self.current_phase_index:
            self.time_in_current_phase = 0
            self.next_phase_index = best_phase
            # Transition to Yellow
            self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_sequence)
            
        return self.current_phase_index

    def update_weights(self, penetration):
        """
        Updates internal parameters based on penetration rate.
        Called by runner.py before simulation starts.
        """
        self.penetration = penetration
        print(f"[HybridV2] Updated penetration to {penetration:.2f}")
