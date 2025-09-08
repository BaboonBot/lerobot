#!/usr/bin/env python3
"""
Test script to check if motor sync_write commands are actually being sent.
"""

import logging
from lerobot.robots.rosmaster.config import RosmasterRobotConfig
import time

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)

def test_motor_commands():
    # Load configuration
    config = RosmasterRobotConfig()
    print(f"Config loaded: {config}")
    
    # Create and connect robot
    print("\n1. Creating robot...")
    robot = config.create_robot()
    
    print("\n2. Connecting to robot...")
    robot.connect()
    print(f"✅ Robot connected! Joint names: {robot.joint_names}")
    
    # Get initial position
    obs = robot.get_observation()
    print(f"\n3. Initial position: {obs['joint_positions']}")
    
    # Test sending action with debug output
    print("\n4. Testing send_action with debug...")
    test_action = {"servo_1": 100.0}
    
    print(f"Sending action: {test_action}")
    robot.send_action(test_action)
    
    print("\n5. Waiting 2 seconds...")
    time.sleep(2)
    
    # Check if position changed
    new_obs = robot.get_observation()
    print(f"New position: {new_obs['joint_positions']}")
    
    # Compare positions
    old_pos = obs['joint_positions']
    new_pos = new_obs['joint_positions']
    
    for i, (old, new) in enumerate(zip(old_pos, new_pos)):
        if abs(old - new) > 0.1:
            print(f"✅ Joint {i+1} changed: {old} -> {new}")
        else:
            print(f"❌ Joint {i+1} unchanged: {old} -> {new}")
    
    print("\n6. Disconnecting...")
    robot.disconnect()

if __name__ == "__main__":
    test_motor_commands()
