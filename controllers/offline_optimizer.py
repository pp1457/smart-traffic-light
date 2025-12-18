from .fixed_time import FixedTimeController
from historical_demand import HistoricalDemandEstimator

class OfflineOptimizer:
    """
    Implements Offline Optimization (Nature Paper Approach).
    Calculates optimal Cycle Length and Green Splits using Webster's Method
    based on average historical demand.
    """
    
    def __init__(self, historical_estimator, traffic_light_id, phase_sequence):
        self.historical_estimator = historical_estimator
        self.traffic_light_id = traffic_light_id
        self.phase_sequence = phase_sequence
        
        # Constants for Webster's
        self.SATURATION_FLOW = 1800.0 # veh/hr/lane (Assumed)
        self.LOST_TIME_PER_PHASE = 4.0 # seconds (Yellow + Red Clearance)
        self.MIN_CYCLE = 40
        self.MAX_CYCLE = 120
        
    def optimize(self, day_type="weekday", start_hour=0, end_hour=24, demand_scale=1.0):
        """
        Calculates optimal timings and returns a configured FixedTimeController.
        """
        print(f"[OfflineOptimizer] Optimizing for {day_type} ({start_hour}-{end_hour}h) with scale {demand_scale}...")
        
        # 1. Calculate Average Demand for each Lane
        avg_demand = {}
        all_lanes = []
        for p in self.phase_sequence:
            if p.get("lanes"):
                all_lanes.extend(p["lanes"])
        
        for lane in all_lanes:
            total_demand = 0
            count = 0
            # Sample every hour
            for h in range(start_hour, end_hour):
                time_sec = h * 3600
                d = self.historical_estimator.get_demand(time_sec, lane, day_type)
                total_demand += d
                count += 1
            
            avg_demand[lane] = (total_demand / max(1, count)) * demand_scale
            # print(f"  Lane {lane}: {avg_demand[lane]:.1f} veh/hr")
            
        # 2. Calculate Critical Flow Ratios (Y)
        Y = 0.0
        critical_lanes = []
        
        green_phases = [p for p in self.phase_sequence if p.get("lanes")]
        num_phases = len(green_phases)
        
        for phase in green_phases:
            # Find critical lane (max flow ratio) for this phase
            max_y = 0.0
            crit_lane = None
            for lane in phase["lanes"]:
                flow = avg_demand.get(lane, 0)
                y = flow / self.SATURATION_FLOW
                if y > max_y:
                    max_y = y
                    crit_lane = lane
            
            Y += max_y
            critical_lanes.append((phase['phase_index'], max_y))
            
        # 3. Calculate Optimal Cycle Length (Webster's)
        # C = (1.5 * L + 5) / (1 - Y)
        L = num_phases * self.LOST_TIME_PER_PHASE
        
        if Y >= 1.0:
            print(f"[OfflineOptimizer] Warning: Intersection oversaturated (Y={Y:.2f}). Using Max Cycle.")
            opt_cycle = self.MAX_CYCLE
        else:
            opt_cycle = (1.5 * L + 5) / (1.0 - Y)
            opt_cycle = max(self.MIN_CYCLE, min(self.MAX_CYCLE, opt_cycle))
            
        print(f"[OfflineOptimizer] Optimal Cycle: {opt_cycle:.1f}s (Y={Y:.2f})")
        
        # 4. Calculate Green Splits
        # G_i = (y_i / Y) * (C - L)
        effective_green_time = opt_cycle - L
        
        new_sequence = []
        for p in self.phase_sequence:
            new_p = p.copy()
            if p.get("lanes"):
                # Green Phase
                # Find y_i for this phase
                y_i = 0.0
                for idx, y in critical_lanes:
                    if idx == p['phase_index']:
                        y_i = y
                        break
                
                if Y > 0:
                    g_i = (y_i / Y) * effective_green_time
                else:
                    g_i = effective_green_time / num_phases
                    
                # Enforce Min Green
                g_i = max(p.get("min_green", 10), g_i)
                new_p["duration"] = int(g_i)
            else:
                # Yellow Phase (Keep original)
                pass
            new_sequence.append(new_p)
            
        # 5. Return Controller
        return FixedTimeController(self.traffic_light_id, new_sequence)
