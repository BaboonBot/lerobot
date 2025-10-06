#!/usr/bin/env python3

"""
Test script to demonstrate the enhanced Rosmaster teleoperator with torque control.

Usage:
    python test_enhanced_teleop.py

Key mappings:
- q/a: Joint 1 (+/-)
- w/s: Joint 2 (+/-)  
- e/d: Joint 3 (+/-)
- r/f: Joint 4 (+/-)
- t/g: Joint 5 (+/-)
- y/h: Joint 6 (+/-)

Torque Control:
- z: Enable torque (motors can resist movement)
- x: Disable torque (motors can be moved freely by hand)

Other Controls:
- SPACE: Lock/Unlock position control (SAFETY FEATURE)
- ESC: Disconnect
"""

import sys
import os

# Add src to path
sys.path.insert(0, '/home/jetson/lerobot/src')

from lerobot.robots.rosmaster.rosmaster import RosmasterRobot, RosmasterRobotConfig
from lerobot.teleoperators.rosmaster_enhanced.configuration_rosmaster_enhanced import RosmasterEnhancedTeleopConfig
from lerobot.teleoperators.utils import make_teleoperator_from_config
import time
import logging

def main():
    logging.basicConfig(level=logging.INFO)
    
    print("🤖 Enhanced Rosmaster Teleoperator Test")
    print("=" * 50)
    
    # Create robot and teleoperator configs
    robot_config = RosmasterRobotConfig(com='/dev/myserial')
    teleop_config = RosmasterEnhancedTeleopConfig(mock=False)  # Real keyboard input
    
    # Create instances
    robot = RosmasterRobot(robot_config)
    teleop = make_teleoperator_from_config(teleop_config)
    
    try:
        print("Connecting to robot and teleoperator...")
        robot.connect()
        teleop.connect()
        
        print("\n🎮 Starting teleoperation loop...")
        print("Press ESC to exit, or Ctrl+C")
        
        # Simple teleop loop
        start_time = time.time()
        loop_count = 0
        
        while True:
            loop_start = time.perf_counter()
            
            # Get action from teleoperator
            action = teleop.get_action()
            
            # Send action to robot
            robot.send_action(action)
            
            # Simple rate limiting (30 Hz)
            dt = time.perf_counter() - loop_start
            if dt < 1/30:
                time.sleep(1/30 - dt)
            
            loop_count += 1
            
            # Print status every 100 loops
            if loop_count % 100 == 0:
                elapsed = time.time() - start_time
                hz = loop_count / elapsed
                print(f"Loop {loop_count}: Running at {hz:.1f} Hz")
                
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("Cleaning up...")
        try:
            robot.disconnect()
            teleop.disconnect()
        except:
            pass
        print("✅ Cleanup complete")

if __name__ == "__main__":
    main()
