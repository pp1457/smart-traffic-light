from .base_controller import TrafficSignalController
import traci

class MaxPressureController(TrafficSignalController):
    """
    Max-Pressure Controller.
    Selects the phase with the highest total pressure (queue length).
    Pressure = Sum(Queue Length of Incoming Lanes) - Sum(Queue Length of Outgoing Lanes)
    Simplified: Pressure = Sum(Queue Length of Incoming Lanes) (assuming infinite downstream capacity)
    """
    
    def __init__(self, traffic_light_id, phase_sequence, min_green=10, max_green=60, yellow_time=5, **kwargs):
        super().__init__(traffic_light_id, phase_sequence)
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        
        self.current_phase_index = 0
        self.time_in_current_phase = 0
        self.next_phase_index = 0

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
        best_phase = self.current_phase_index
        max_pressure = -1.0
        
        # Identify green phases
        green_phases = [p for p in self.phase_sequence if p.get("lanes")]
        
        for phase in green_phases:
            p_idx = phase['phase_index']
            lanes = phase['lanes']
            
            # Calculate Pressure (Sum of Queues)
            pressure = 0.0
            for lane in lanes:
                # Get queue length from TraCI (ground truth for baseline)
                # Note: getLastStepHaltingNumber returns number of vehicles with speed < 0.1 m/s
                queue = traci.lane.getLastStepHaltingNumber(lane)
                pressure += queue
            
            # Hysteresis: Add small bonus to current phase to prevent rapid flickering
            if p_idx == self.current_phase_index:
                pressure += 0.1
                
            if pressure > max_pressure:
                max_pressure = pressure
                best_phase = p_idx
                
        # 4. Decision
        if self.time_in_current_phase >= self.max_green:
             # Force switch if max green reached
             if best_phase == self.current_phase_index:
                 # Round robin fallback
                 best_phase = (self.current_phase_index + 1) % len(self.phase_sequence)
                 while not self.phase_sequence[best_phase].get("lanes"):
                     best_phase = (best_phase + 1) % len(self.phase_sequence)
        
        if best_phase != self.current_phase_index:
            self.time_in_current_phase = 0
            self.next_phase_index = best_phase
            # Transition to Yellow
            self.current_phase_index = (self.current_phase_index + 1) % len(self.phase_sequence)
            
        return self.current_phase_index
