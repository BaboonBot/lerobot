#!/bin/bash
# Script to test Rosmaster robot inside Docker container

echo "🤖 Testing Rosmaster Robot in Docker Container"
echo "=============================================="

# Check if we're inside the container
if [ -f /.dockerenv ]; then
    echo "✓ Running inside Docker container"
else
    echo "❌ Not running inside Docker container"
    echo "Please run this script inside the Docker container"
    exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source /lerobot/.venv/bin/activate

# Test Python imports
echo "Testing Python imports..."
python3 -c "
try:
    from lerobot.robots.rosmaster import RosmasterRobot, RosmasterRobotConfig
    print('✓ Successfully imported RosmasterRobot')
    
    from lerobot.teleoperators.keyboard import KeyboardTeleop
    print('✓ Successfully imported KeyboardTeleop')
    
    print('✓ All imports successful!')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Check serial ports
echo ""
echo "Available serial ports:"
ls -la /dev/tty* | grep -E "(USB|AMA|THS)" || echo "No USB/UART ports found"

# Check permissions
echo ""
echo "Checking user permissions:"
groups

echo ""
echo "🎯 Ready to test robot!"
echo "Available test scripts:"
echo "  - python3 test_rosmaster_simple.py     # Basic robot test"
echo "  - python3 test_rosmaster_keyboard.py   # Robot with keyboard control"
echo ""
echo "Make sure your robot is connected via USB before running tests!"
