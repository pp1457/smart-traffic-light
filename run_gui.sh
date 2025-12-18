#!/bin/bash
echo "Starting SUMO GUI with Hybrid Pressure V2 controller..."
echo "Scenario: Stress Test (1.5x Demand), Penetration: 15%"
/Users/liaoyunyang/NTU_CSIE/Research/Smart_Traffic_Light/.venv/bin/python runner.py \
    --algorithm hybrid_pressure_v2 \
    --gui \
    --scale 1.5 \
    --penetration 0.15 \
    --alpha 0.5 \
    --beta 0.5 \
    --day_type weekday
