#!/usr/bin/env python3
"""
Direct test of the terminal teleoperator without going through the CLI.
"""

import sys
sys.path.append('/home/jetson/lerobot/src')

import logging
import time
from lerobot.robots.rosmaster.config import RosmasterRobotConfig
from lerobot.teleoperators.rosmaster_terminal.config import RosmasterTerminalTeleopConfig
from lerobot.utils.utils import init_logging

def main():
    init_logging()
    
    print("🚀 Starting manual terminal teleop test...")
    
    # Create robot
    robot_config = RosmasterRobotConfig()
    robot = robot_config.create_robot()
    print("✅ Robot created")
    
    # Create terminal teleop 
    teleop_config = RosmasterTerminalTeleopConfig()
    teleop = teleop_config.create_teleop()
    print("✅ Terminal teleop created")
    
    # Connect both
    print("\n🔌 Connecting robot...")
    robot.connect()
    print("✅ Robot connected!")
    
    print("\n🔌 Connecting teleop...")
    teleop.connect()
    print("✅ Terminal teleop connected!")
    
    print("\n🎯 Starting control loop...")
    print("You can now type commands like:")
    print("  set servo_1 120")
    print("  set all 90 120 45 90 90 90")
    print("  get")
    print("  quit")
    
    # Control loop
    try:
        for i in range(100):  # Run for max 100 iterations
            if not teleop.is_connected:
                break
                
            # Get action from teleop
            action = teleop.get_action()
            
            # Send to robot
            robot.send_action(action)
            
            # Get robot observation to verify
            obs = robot.get_observation()
            
            time.sleep(0.1)  # 10 Hz
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    
    finally:
        print("\n🔌 Disconnecting...")
        teleop.disconnect()
        robot.disconnect()
        print("✅ Clean shutdown complete")

if __name__ == "__main__":
    main()
