#!/usr/bin/env python3

"""
Demo showing position syncing when torque is disabled.
"""

import sys
import time
sys.path.insert(0, '/home/jetson/lerobot/src')

from lerobot.robots.rosmaster.rosmaster import RosmasterRobot, RosmasterRobotConfig
from lerobot.teleoperators.rosmaster_enhanced.configuration_rosmaster_enhanced import RosmasterEnhancedTeleopConfig
from lerobot.teleoperators.utils import make_teleoperator_from_config

def main():
    print("🔄 Demo: Position Syncing with Torque Control")
    print("=" * 50)
    
    # Create robot and teleoperator
    robot_config = RosmasterRobotConfig(com='/dev/myserial')
    robot = RosmasterRobot(robot_config)
    teleop_config = RosmasterEnhancedTeleopConfig(mock=True)
    teleop = make_teleoperator_from_config(teleop_config)
    
    try:
        print("📡 Connecting...")
        robot.connect()
        teleop.connect()
        
        print("✅ Connected!")
        
        # Initial state - torque enabled
        print("\n🟢 PHASE 1: Torque ENABLED (normal operation)")
        print("   Teleoperator has default positions (90° each)")
        
        for i in range(3):
            action = teleop.get_action()
            teleop_positions = [action[f'servo_{j+1}'] for j in range(6)]
            observation = robot.get_observation()
            robot_positions = [observation.get(f'servo_{j+1}', 90.0) for j in range(6)]
            
            print(f"   Teleop: {teleop_positions[0]:.1f}° {teleop_positions[1]:.1f}° {teleop_positions[2]:.1f}°...")
            print(f"   Robot:  {robot_positions[0]:.1f}° {robot_positions[1]:.1f}° {robot_positions[2]:.1f}°...")
            time.sleep(1)
        
        # Simulate torque disable
        print("\n🔴 PHASE 2: Simulating Torque DISABLED")
        print("   Robot can be moved manually, positions should sync")
        
        # Manually set torque state to disabled in teleoperator
        teleop.torque_enabled = False
        
        for i in range(5):
            action = teleop.get_action()
            observation = robot.get_observation()
            
            # Send feedback to trigger position syncing
            if teleop.feedback_features:
                feedback = {}
                for key in teleop.feedback_features:
                    if key in observation:
                        feedback[key] = observation[key]
                teleop.send_feedback(feedback)
            
            # Get updated positions after feedback
            action_after = teleop.get_action()
            teleop_positions = [action_after[f'servo_{j+1}'] for j in range(6)]
            robot_positions = [observation.get(f'servo_{j+1}', 90.0) for j in range(6)]
            
            print(f"   Loop {i+1}:")
            print(f"     Teleop synced: {teleop_positions[0]:.1f}° {teleop_positions[1]:.1f}° {teleop_positions[2]:.1f}°...")
            print(f"     Robot actual:  {robot_positions[0]:.1f}° {robot_positions[1]:.1f}° {robot_positions[2]:.1f}°...")
            
            # Check if positions are synced
            diff1 = abs(teleop_positions[0] - robot_positions[0])
            diff2 = abs(teleop_positions[1] - robot_positions[1])
            diff3 = abs(teleop_positions[2] - robot_positions[2])
            
            if max(diff1, diff2, diff3) < 1.0:
                print("     ✅ Positions SYNCED!")
            else:
                print(f"     🔄 Syncing... (diff: {diff1:.1f}° {diff2:.1f}° {diff3:.1f}°)")
            
            time.sleep(1)
        
        # Simulate torque re-enable
        print("\n🟢 PHASE 3: Simulating Torque RE-ENABLED")
        print("   Robot should hold the synced positions (no snap-back!)")
        
        teleop.torque_enabled = True
        
        action = teleop.get_action()
        teleop_positions = [action[f'servo_{j+1}'] for j in range(6)]
        observation = robot.get_observation()  
        robot_positions = [observation.get(f'servo_{j+1}', 90.0) for j in range(6)]
        
        print(f"   Final teleop: {teleop_positions[0]:.1f}° {teleop_positions[1]:.1f}° {teleop_positions[2]:.1f}°...")
        print(f"   Final robot:  {robot_positions[0]:.1f}° {robot_positions[1]:.1f}° {robot_positions[2]:.1f}°...")
        
        diff1 = abs(teleop_positions[0] - robot_positions[0])
        diff2 = abs(teleop_positions[1] - robot_positions[1])
        diff3 = abs(teleop_positions[2] - robot_positions[2])
        
        if max(diff1, diff2, diff3) < 5.0:  # Allow some tolerance
            print("   ✅ SUCCESS: No snap-back! Positions remain synced.")
        else:
            print("   ❌ Positions diverged - may need tuning")
        
        print("\n🎉 Demo completed!")
        print("\nHow to use in practice:")
        print("1. Start teleoperation: lerobot-teleoperate --teleop.type=rosmaster_enhanced")
        print("2. Press 'x' to disable torque")
        print("3. Manually move the robot arm")  
        print("4. Watch positions sync automatically")
        print("5. Press 'z' to re-enable torque")
        print("6. Robot holds current position (no snap-back!)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            robot.disconnect()
            teleop.disconnect()
        except:
            pass

if __name__ == "__main__":
    main()
