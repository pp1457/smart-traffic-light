from .base_controller import TrafficSignalController
from .base_controller import TrafficSignalController
from v2x_manager import VoteCollector
from queue_estimator import ShockwaveQueueEstimator

# Default constants if not in config
DEFAULT_MIN_GREEN = 5
DEFAULT_MAX_GREEN = 60

class HybridController(TrafficSignalController):
    """
    Hybrid control logic fusing historical demand with AV data.
    """
    
    def __init__(self, traffic_light_id, phase_sequence, historical_demand_estimator=None, vote_collector=None, 
                 w_hist=1.0, w_av=2.0, pressure_threshold=10.0, queue_estimator=None):
        super().__init__(traffic_light_id, phase_sequence)
        self.historical_demand_estimator = historical_demand_estimator
        self.vote_collector = vote_collector if vote_collector else VoteCollector()
        self.queue_estimator = queue_estimator
        self.w_hist = w_hist
        self.w_av = w_av
        self.pressure_threshold = pressure_threshold
        self.current_phase_index = 0
        self.last_switch_step = 0
        print(f"[HybridController] Initialized with w_hist={w_hist}, w_av={w_av}, threshold={pressure_threshold}")
        if self.queue_estimator:
            print("[HybridController] Shockwave Queue Estimation ENABLED")

    def update_weights(self, penetration_rate):
        """
        Adaptively updates weights based on penetration rate.
        Low penetration -> Trust History more.
        High penetration -> Trust AVs more.
        """
        # Heuristic: Linear interpolation
        # At 0% pen: w_hist=1.0, w_av=0.0 (but we keep w_av > 0 to use votes if any)
        # At 100% pen: w_hist=0.0, w_av=2.0
        
        # Let's try a simple blend:
        # w_hist decays from 1.0 to 0.2
        # w_av grows from 1.0 to 3.0
        self.w_hist = 1.0 * (1.0 - penetration_rate * 0.8)
        self.w_av = 1.0 + (penetration_rate * 2.0)
        print(f"[Adaptive] Updated weights for pen={penetration_rate:.2f}: w_hist={self.w_hist:.2f}, w_av={self.w_av:.2f}")

    def get_next_phase(self, current_step, day_type="weekday"):
        """
        Determines the next phase based on hybrid pressure.
        """
        # 1. Calculate pressure for ALL phases
        phase_pressures = []
        
        for i, phase_config in enumerate(self.phase_sequence):
            # Only calculate pressure for green phases (those with lanes)
            if not phase_config.get("lanes"):
                phase_pressures.append(-1.0) # Yellow phase has no pressure
                continue
                
            pressure = self.calculate_pressure(phase_config["lanes"], current_step, day_type)
            phase_pressures.append(pressure)
            
        # 2. Get current phase pressure
        current_pressure = phase_pressures[self.current_phase_index]
        if current_pressure < 0: # If currently yellow, pressure is irrelevant, we just transition
             pass

        # 3. Find best candidate (highest pressure)
        # Filter out negative pressures (yellow phases)
        valid_pressures = [(i, p) for i, p in enumerate(phase_pressures) if p >= 0]
        if not valid_pressures:
            return self.current_phase_index
            
        best_phase_index, best_pressure = max(valid_pressures, key=lambda x: x[1])
        
        # 4. Switching Logic
        # Only switch if:
        # a. We've held the current phase for MIN_GREEN
        # b. The best phase has significantly higher pressure than current
        # c. We haven't exceeded MAX_GREEN (force switch if we have)
        
        time_in_phase = current_step - self.last_switch_step
        
        # If we are in a yellow phase, we MUST switch after duration
        current_phase_config = self.phase_sequence[self.current_phase_index]
        if not current_phase_config.get("lanes"):
             if time_in_phase >= current_phase_config["duration"]:
                 # Switch to the next phase in sequence (which should be the target green)
                 # For simplicity in this pressure controller, let's assume we cycle 0 -> 1(Y) -> 2 -> 3(Y) -> 0
                 next_index = (self.current_phase_index + 1) % len(self.phase_sequence)
                 self.current_phase_index = next_index
                 self.last_switch_step = current_step
                 return next_index
             else:
                 return self.current_phase_index

        # If in Green Phase
        min_green = current_phase_config.get("min_green", DEFAULT_MIN_GREEN)
        max_green = current_phase_config.get("max_green", DEFAULT_MAX_GREEN)

        if time_in_phase < min_green:
            return self.current_phase_index
            
        if time_in_phase >= max_green:
            # Force switch to best candidate (or just next in cycle if we wanted fixed order)
            if best_phase_index != self.current_phase_index:
                # We need to go through yellow first!
                # Find the yellow phase between current and best
                # Assuming structure: Green(0) -> Yellow(1) -> Green(2) -> Yellow(3)
                yellow_index = (self.current_phase_index + 1) % len(self.phase_sequence)
                print(f"[Hybrid] Step {current_step}: Max Green. Switch {self.current_phase_index} -> {yellow_index} (Yellow) -> {best_phase_index}")
                self.current_phase_index = yellow_index
                self.last_switch_step = current_step
            return self.current_phase_index
            
        # Pressure-based switch
        if best_phase_index != self.current_phase_index and best_pressure > current_pressure + self.pressure_threshold:
            print(f"[Hybrid] Step {current_step}: Cur P={current_pressure:.2f}, Next P={best_pressure:.2f}")
            print(f"  -> Switching! Next pressure {best_pressure:.2f} > Cur {current_pressure:.2f} + {self.pressure_threshold}")
            # Switch to yellow first
            yellow_index = (self.current_phase_index + 1) % len(self.phase_sequence)
            self.current_phase_index = yellow_index
            self.last_switch_step = current_step
            
        return self.current_phase_index

    def calculate_pressure(self, lanes, current_step, day_type):
        """
        Calculates pressure for a set of lanes (a phase).
        P = w_hist * Demand_hist + w_av * Count_av (or Queue_est)
        """
        pressure = 0.0
        
        for lane_id in lanes:
            # Historical Component
            demand = 0
            if self.historical_demand_estimator:
                demand = self.historical_demand_estimator.get_demand(current_step, lane_id, day_type)
                # Demand is in veh/hr, convert to veh/cycle (approx) or just use raw scale
                # Let's scale it down to be comparable to vehicle counts
                # 3600 sec/hr. If cycle is ~60s, then demand/60 is expected vehicles.
                demand = demand / 60.0 
            
            # AV Component
            av_pressure = 0
            if self.queue_estimator:
                # Use Shockwave Estimation
                av_pressure = self.queue_estimator.get_queue_length(lane_id)
            elif self.vote_collector:
                # Fallback to raw counting
                av_pressure = len(self.vote_collector.get_votes_for_lane(lane_id))
                
            pressure += (self.w_hist * demand) + (self.w_av * av_pressure)
            
            if current_step % 100 == 0:
                print(f"[Hybrid] Lane {lane_id}: Demand={demand:.2f}, AV_P={av_pressure:.2f}, Total={pressure:.2f}")
            
        return pressure
