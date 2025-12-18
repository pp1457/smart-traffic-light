from .base_controller import TrafficSignalController
import traci

class HybridPressureController(TrafficSignalController):
    """
    Hybrid Pressure Controller (Greedy).
    Calculates pressure for each phase based on fused queue estimates (Historical + AV).
    Formula: P_i = Sum(w_m * Q_up(m)) - Beta * Sum(Q_down(m))
    """
    
    def __init__(self, traffic_light_id, phase_sequence, queue_estimator, 
                 min_green=10, max_green=60, yellow_time=5, **kwargs):
        super().__init__(traffic_light_id, phase_sequence)
        self.queue_estimator = queue_estimator
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        
        self.current_phase_index = 0
        self.time_in_current_phase = 0
        self.next_phase_index = 0
        
        # Map phase index to lanes
        self.phase_lanes = {}
        for p in phase_sequence:
            self.phase_lanes[p['phase_index']] = p.get('lanes', [])

    def get_next_phase(self, current_step, day_type="weekday"):
        self.time_in_current_phase += 1
        
        current_config = self.phase_sequence[self.current_phase_index]
        is_yellow = not current_config.get("lanes")
        
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
        # We need to update the estimator first? No, runner.py does that.
        # We just read from self.queue_estimator.queue_estimates
        
        best_phase = self.current_phase_index
        max_pressure = -1.0
        
        # Identify green phases
        green_phases = [p for p in self.phase_sequence if p.get("lanes")]
        
        for phase in green_phases:
            p_idx = phase['phase_index']
            lanes = phase['lanes']
            
            # Calculate Pressure
            pressure = 0.0
            for lane in lanes:
                # Q_up: Estimated Queue
                q_up = self.queue_estimator.queue_estimates.get(lane, 0.0)
                # Q_down: Assumed 0 for now (infinite capacity)
                q_down = 0.0 
                
                pressure += (q_up - q_down)
            
            # Hysteresis: Add small bonus to current phase to prevent rapid flickering if pressures are equal
            if p_idx == self.current_phase_index:
                pressure += 0.1
                
            if pressure > max_pressure:
                max_pressure = pressure
                best_phase = p_idx
                
        # 4. Decision
        # If Max Green reached, force switch to next best (or sequential if we want to be simple)
        # But greedy pressure usually switches when another phase has higher pressure.
        # We just check if best_phase != current
        
        if self.time_in_current_phase >= self.max_green:
             # Force switch if we are at max green. 
             # If best_phase is still current, we MUST switch to something else?
             # Standard MaxPressure doesn't necessarily force switch, but for safety we should.
             # Let's pick the phase with 2nd highest pressure or just next sequential.
             if best_phase == self.current_phase_index:
                 # Simple round-robin fallback if stuck
                 best_phase = (self.current_phase_index + 1) % len(self.phase_sequence)
                 while not self.phase_sequence[best_phase].get("lanes"):
                     best_phase = (best_phase + 1) % len(self.phase_sequence)
        
        if best_phase != self.current_phase_index:
            self.time_in_current_phase = 0
            self.next_phase_index = best_phase
            # Transition to Yellow
            # Assume next phase in list is yellow
            self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_sequence)
            
        return self.current_phase_index
