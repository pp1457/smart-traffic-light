from dataclasses import dataclass
from typing import List, Dict

@dataclass
class V2XMessage:
    """
    Represents a V2X message sent by an AV.
    """
    vehicle_id: str
    lane_id: str
    speed: float
    distance_to_stop: float
    estimated_arrival_time: float # Current time + (distance / speed)

class VoteCollector:
    """
    Collects and aggregates V2X messages from AVs.
    """
    def __init__(self):
        # Map: lane_id -> List[V2XMessage]
        self.votes: Dict[str, List[V2XMessage]] = {}

    def clear_votes(self):
        """Resets the votes for the current time step."""
        self.votes = {}

    def collect_vote(self, message: V2XMessage):
        """Receives a vote from an AV."""
        if message.lane_id not in self.votes:
            self.votes[message.lane_id] = []
        self.votes[message.lane_id].append(message)

    def get_votes_for_lane(self, lane_id: str) -> List[V2XMessage]:
        """Returns all votes for a specific lane."""
        return self.votes.get(lane_id, [])

    def get_total_pressure(self, lane_ids: List[str]) -> float:
        """
        Calculates the total 'pressure' (e.g., number of AVs) for a set of lanes.
        This is a simplified metric for now.
        """
        total_avs = 0
        for lane in lane_ids:
            total_avs += len(self.get_votes_for_lane(lane))
        return total_avs
