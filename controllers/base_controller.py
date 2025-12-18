from abc import ABC, abstractmethod

class TrafficSignalController(ABC):
    """
    Abstract base class for traffic signal control algorithms.
    """
    
    def __init__(self, traffic_light_id, phase_sequence):
        self.traffic_light_id = traffic_light_id
        self.phase_sequence = phase_sequence
        self.current_phase_pointer = 0
        self.phase_timer = 0

    @abstractmethod
    def get_next_phase(self, current_step, simulation_data=None):
        """
        Determines the next phase index based on the current step and data.
        
        Args:
            current_step (int): Current simulation time in seconds.
            simulation_data (dict, optional): Additional data (e.g., detector counts, AV messages).
            
        Returns:
            int: The index of the next phase.
        """
        pass
