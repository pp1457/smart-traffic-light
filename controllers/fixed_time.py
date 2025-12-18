from .base_controller import TrafficSignalController

class FixedTimeController(TrafficSignalController):
    """
    A basic time-based control logic that cycles through a predefined sequence.
    """
    
    def __init__(self, traffic_light_id, phase_sequence):
        super().__init__(traffic_light_id, phase_sequence)
        # Initialize timer with the duration of the first phase
        if self.phase_sequence:
            self.phase_timer = self.phase_sequence[0]["duration"]

    def get_next_phase(self, current_step, simulation_data=None):
        # Decrement the timer for the current phase
        self.phase_timer -= 1

        # If the timer for the current phase has run out, move to the next phase
        if self.phase_timer <= 0:
            # Move to the next phase in the sequence
            self.current_phase_pointer = (self.current_phase_pointer + 1) % len(self.phase_sequence)
            
            # Reset the timer with the duration of the new phase
            self.phase_timer = self.phase_sequence[self.current_phase_pointer]["duration"]

        # Return the phase index that should be active
        return self.phase_sequence[self.current_phase_pointer]["phase_index"]
