#!/usr/bin/env python3

"""
Demonstration of torque control functionality for Rosmaster robot.

This script demonstrates how the torque control works by:
1. Connecting to the robot
2. Enabling/disabling torque programmatically
3. Showing the current servo positions
4. Testing different torque states

Usage:
    python demo_torque_control.py
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, '/home/jetson/lerobot/src')

from lerobot.robots.rosmaster.rosmaster import RosmasterRobot, RosmasterRobotConfig

def main():
    print("🤖 Rosmaster Torque Control Demo")
    print("=" * 40)
    
    # Create robot config
    robot_config = RosmasterRobotConfig(com='/dev/myserial')
    robot = RosmasterRobot(robot_config)
    
    try:
        print("📡 Connecting to robot...")
        robot.connect()
        
        print("✅ Robot connected!")
        print("Current firmware version detected")
        
        # Get current positions
        print("\n📊 Reading current servo positions...")
        obs = robot.get_observation()
        print("Current positions:")
        for i in range(6):
            servo_name = f'servo_{i+1}'
            if servo_name in obs:
                print(f"   {servo_name}: {obs[servo_name]:.1f}°")
        
        print("\n🔧 Testing torque control...")
        
        # Create base action
        action = {}
        for i in range(6):
            servo_name = f'servo_{i+1}'
            if servo_name in obs:
                action[servo_name] = obs[servo_name]
            else:
                action[servo_name] = 90.0
        
        # Test 1: Enable torque
        print("\n1️⃣  Enabling torque (normal operation mode)")
        print("   Motors will resist manual movement")
        action['torque_enable'] = True
        action['torque_disable'] = False
        robot.send_action(action)
        time.sleep(1)
        
        # Test 2: Disable torque
        print("\n2️⃣  Disabling torque (manual positioning mode)")
        print("   🖐️  You can now move the robot manually!")
        print("   Try gently moving the arm joints by hand.")
        action['torque_enable'] = False
        action['torque_disable'] = True
        robot.send_action(action)
        
        print("\n⏰ Torque will remain disabled for 5 seconds...")
        print("   Feel free to manually position the robot.")
        time.sleep(5)
        
        # Test 3: Re-enable torque
        print("\n3️⃣  Re-enabling torque")
        print("   Motors will now hold their current positions")
        action['torque_enable'] = True
        action['torque_disable'] = False
        robot.send_action(action)
        
        # Read final positions
        print("\n📊 Reading final servo positions...")
        obs = robot.get_observation()
        print("Final positions:")
        for i in range(6):
            servo_name = f'servo_{i+1}'
            if servo_name in obs:
                print(f"   {servo_name}: {obs[servo_name]:.1f}°")
        
        print("\n🎉 Demo completed successfully!")
        print("\nTo use torque control during teleoperation:")
        print("   - Press 'z' to enable torque")
        print("   - Press 'x' to disable torque") 
        print("   - Use with either 'rosmaster_keyboard' or 'rosmaster_enhanced' teleoperators")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔌 Disconnecting...")
        try:
            robot.disconnect()
        except:
            pass
        print("✅ Demo cleanup complete")

if __name__ == "__main__":
    main()
