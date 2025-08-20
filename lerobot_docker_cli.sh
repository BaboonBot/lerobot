#!/bin/bash
# Official LeRobot Teleoperation using Docker
# This avoids dependency conflicts and provides the proper LeRobot CLI experience

echo "🤖 Starting LeRobot Teleoperation in Docker"
echo "==========================================="

# Check if robot is connected
if [[ ! -e /dev/ttyUSB0 ]]; then
    echo "❌ Error: Robot not found at /dev/ttyUSB0"
    echo "   Please check robot connection and try again."
    exit 1
fi

echo "✅ Robot found at /dev/ttyUSB0"
echo "🐳 Starting Docker container with LeRobot teleoperation..."
echo ""
echo "Key Controls:"
echo "  q/a: Joint 1 (+/-)"
echo "  w/s: Joint 2 (+/-)" 
echo "  e/d: Joint 3 (+/-)"
echo "  r/f: Joint 4 (+/-)"
echo "  t/g: Joint 5 (+/-)"
echo "  y/h: Joint 6 (+/-)"
echo "  ESC: Exit"
echo ""
echo "⚠️  Note: Keyboard input is simulated in Docker (mock mode)"
echo "   For real keyboard control, run the host version."
echo ""
echo "===========================================" 

# Official LeRobot CLI command in Docker
docker run --device=/dev/ttyUSB0 \
           -v $(pwd):/workspace \
           -w /workspace \
           -it lerobot-yahboom-jetson \
           python -m lerobot.teleoperate \
           --robot.type=rosmaster \
           --robot.com=/dev/ttyUSB0 \
           --robot.id=my_rosmaster \
           --teleop.type=rosmaster_keyboard \
           --teleop.id=my_keyboard \
           --teleop.joint_step=5.0 \
           --teleop.mock=true \
           --fps=30

echo ""
echo "👋 LeRobot teleoperation ended"
