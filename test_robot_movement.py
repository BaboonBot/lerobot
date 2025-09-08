#!/usr/bin/env python3
"""
Test script to debug robot.send_action() issues.
This helps diagnose why the robot isn't moving when you call send_action.
"""

import sys
import os
import time
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lerobot.robots.rosmaster import RosmasterRobotConfig
from lerobot.robots.utils import make_robot_from_config

def test_robot_movement():
    """Test different ways to send actions to the robot."""
    
    print("🤖 Testing Robot Movement")
    print("=" * 50)
    
    # Create robot
    robot_config = RosmasterRobotConfig(
        id="movement_test",
        # com="/dev/myserial"
        com = "/dev/ttyUSB0"  # Change as needed
    )
    
    robot = make_robot_from_config(robot_config)
    
    try:
        # Connect robot
        print("🔗 Connecting robot...")
        robot.connect(calibrate=True)
        
        if not robot.is_connected:
            print("❌ Robot failed to connect!")
            return
        
        print("✅ Robot connected!")
        print(f"Joint names: {robot.joint_names}")
        
        # Get initial observation
        print("\n📊 Initial robot state:")
        obs = robot.get_observation()
        print(f"Current positions: {[obs[name] for name in robot.joint_names]}")
        
        # Test 1: Individual joint action (correct format)
        print("\n🧪 Test 1: Individual joint actions")
        action1 = {
            "servo_1": 95.0,  # Move joint 1 by 5 degrees
            "servo_2": 90.0,  # Keep joint 2 at center
            "servo_3": 90.0,
            "servo_4": 90.0,
            "servo_5": 90.0,
            "servo_6": 90.0
        }
        
        print(f"Sending action: {action1}")
        robot.send_action(action1)
        time.sleep(2)
        
        # Check if robot moved
        obs_after = robot.get_observation()
        new_positions = [obs_after[name] for name in robot.joint_names]
        print(f"Positions after action: {new_positions}")
        
        # Test 2: Vector format (if this is what you're using)
        print("\n🧪 Test 2: Vector format (converted to individual joints)")
        angle_vector = [85.0, 90.0, 90.0, 90.0, 90.0, 90.0]  # Move joint 1 back
        
        # Convert vector to individual joint actions
        action2 = {}
        for i, joint_name in enumerate(robot.joint_names):
            action2[joint_name] = angle_vector[i]
        
        print(f"Vector: {angle_vector}")
        print(f"Converted action: {action2}")
        robot.send_action(action2)
        time.sleep(2)
        
        # Check movement
        obs_final = robot.get_observation()
        final_positions = [obs_final[name] for name in robot.joint_names]
        print(f"Final positions: {final_positions}")
        
        # Test 3: Small incremental movement
        print("\n🧪 Test 3: Small incremental movement")
        current_pos = obs_final["servo_1"]
        target_pos = current_pos + 10.0  # Small 10-degree movement
        
        action3 = {name: obs_final[name] for name in robot.joint_names}  # Keep all current
        action3["servo_1"] = target_pos  # Change only one joint
        
        print(f"Moving servo_1 from {current_pos:.1f}° to {target_pos:.1f}°")
        robot.send_action(action3)
        time.sleep(2)
        
        obs_test3 = robot.get_observation()
        actual_pos = obs_test3["servo_1"]
        print(f"Actual position: {actual_pos:.1f}°")
        
        if abs(actual_pos - target_pos) < 5.0:
            print("✅ Robot moved successfully!")
        else:
            print("❌ Robot didn't move as expected")
            
        # Diagnosis
        print("\n🔍 Diagnosis:")
        print("If robot didn't move, possible causes:")
        print("1. Action format issue - robot expects individual joint dict")
        print("2. Servo torque not enabled")
        print("3. Safety limits preventing movement")
        print("4. Hardware communication issue")
        print("5. Values outside joint limits (0-180° for most joints)")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            robot.disconnect()
            print("\n✅ Robot disconnected")
        except:
            pass

def create_action_from_vector(joint_names, angle_vector):
    """Helper function to convert angle vector to action dict."""
    if len(angle_vector) != len(joint_names):
        raise ValueError(f"Vector length {len(angle_vector)} doesn't match joints {len(joint_names)}")
    
    action = {}
    for i, joint_name in enumerate(joint_names):
        action[joint_name] = float(angle_vector[i])
    
    return action

def print_action_format_help():
    """Print help about correct action formats."""
    print("\n📚 Correct Action Formats:")
    print("=" * 40)
    
    print("\n✅ CORRECT - Individual joint dictionary:")
    print("action = {")
    print("    'servo_1': 90.0,")
    print("    'servo_2': 90.0,")
    print("    'servo_3': 90.0,")
    print("    'servo_4': 90.0,")
    print("    'servo_5': 90.0,")
    print("    'servo_6': 90.0")
    print("}")
    print("robot.send_action(action)")
    
    print("\n❌ INCORRECT - Raw vector:")
    print("action = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0]")
    print("robot.send_action(action)  # This won't work!")
    
    print("\n✅ CORRECT - Convert vector to dict:")
    print("angle_vector = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0]")
    print("action = {}")
    print("for i, joint_name in enumerate(robot.joint_names):")
    print("    action[joint_name] = angle_vector[i]")
    print("robot.send_action(action)")

if __name__ == "__main__":
    print_action_format_help()
    print("\nPress ENTER to run movement test...")
    input()
    test_robot_movement()
