#!/bin/bash

# Enhanced Rosmaster Teleoperation with Torque Control
# This script runs the enhanced teleoperator that includes torque enable/disable functionality

echo "🤖 Starting Enhanced Rosmaster Teleoperator"
echo "============================================"

export PYTHONPATH=/home/jetson/lerobot/src

# Run the enhanced teleoperator
lerobot-teleoperate \
    --robot.type=rosmaster \
    --robot.com=/dev/myserial \
    --robot.id=rosmaster \
    --teleop.type=rosmaster_enhanced \
    --teleop.mock=false

echo "✅ Teleoperation completed"
