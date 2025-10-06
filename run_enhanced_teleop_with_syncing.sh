#!/bin/bash

# Complete Torque Control with Position Syncing Demo
# This script demonstrates the enhanced teleoperator with both torque control AND position syncing

echo "🤖 Enhanced Rosmaster Teleoperator with Position Syncing"
echo "========================================================="
echo ""
echo "This enhanced teleoperator includes:"
echo "✅ Torque enable/disable control (z/x keys)"
echo "✅ Position syncing when torque is disabled"
echo "✅ No snap-back when torque is re-enabled"
echo ""

read -p "Press Enter to start teleoperation..."

export PYTHONPATH=/home/jetson/lerobot/src

echo "Starting enhanced teleoperator..."
echo ""
echo "🎮 Key Controls:"
echo "=================="
echo "Joint Control:"
echo "  q/a: Joint 1 (+/-)"
echo "  w/s: Joint 2 (+/-)" 
echo "  e/d: Joint 3 (+/-)"
echo "  r/f: Joint 4 (+/-)"
echo "  t/g: Joint 5 (+/-)"
echo "  y/h: Joint 6 (+/-)"
echo ""
echo "🔥 Torque Control:"
echo "  z: Enable torque (motors resist movement)"
echo "  x: Disable torque (motors can be moved freely)"
echo ""
echo "🔄 Position Syncing:"
echo "  When torque is disabled (x), the teleoperator automatically"
echo "  tracks the robot's actual positions as you move it manually."
echo "  When you re-enable torque (z), the robot holds the current"
echo "  positions without snapping back!"
echo ""
echo "Safety:"
echo "  SPACE: Lock/Unlock position control"
echo "  ESC: Disconnect"
echo ""
echo "Starting in 3 seconds..."
sleep 1
echo "2..."
sleep 1  
echo "1..."
sleep 1
echo "GO!"
echo ""

# Run the enhanced teleoperator
lerobot-teleoperate \
  --robot.type=rosmaster \
  --robot.com=/dev/myserial \
  --robot.id=rosmaster \
  --teleop.type=rosmaster_enhanced \
  --teleop.mock=false

echo ""
echo "✅ Teleoperation session completed!"
echo "Thank you for using the enhanced Rosmaster teleoperator!"
