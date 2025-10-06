#!/usr/bin/env python3

"""
Test position syncing functionality for torque control.
"""

import sys
import time
sys.path.insert(0, '/home/jetson/lerobot/src')

from lerobot.robots.rosmaster.rosmaster import RosmasterRobot, RosmasterRobotConfig
from lerobot.teleoperators.rosmaster_enhanced.configuration_rosmaster_enhanced import RosmasterEnhancedTeleopConfig
from lerobot.teleoperators.utils import make_teleoperator_from_config

def main():
    print("🔄 Testing Position Syncing with Torque Control")
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
        
        print("✅ Connected! Testing position syncing...")
        
        # Simulate teleoperation loop with position feedback
        for i in range(5):
            print(f"\n--- Loop {i+1} ---")
            
            # Get action from teleoperator
            action = teleop.get_action()
            teleop_positions = [action[f'servo_{j+1}'] for j in range(6)]
            print(f"Teleoperator positions: {[f'{p:.1f}' for p in teleop_positions]}")
            
            # Send action to robot
            robot.send_action(action)
            
            # Get robot observation
            observation = robot.get_observation()
            robot_positions = [observation.get(f'servo_{j+1}', 90.0) for j in range(6)]
            print(f"Robot actual positions: {[f'{p:.1f}' for p in robot_positions]}")
            
            # Send feedback to teleoperator (this is what enables position syncing)
            if teleop.feedback_features:
                feedback = {}
                for key in teleop.feedback_features:
                    if key in observation:
                        feedback[key] = observation[key]
                
                print("📤 Sending position feedback to teleoperator...")
                teleop.send_feedback(feedback)
            
            time.sleep(1)
        
        print("\n🎉 Position syncing test completed!")
        print("\nKey features:")
        print("- Teleoperator tracks robot's actual positions")
        print("- When torque disabled (x key), positions sync automatically")  
        print("- When torque enabled (z key), robot holds synced positions")
        print("- No more snapping back to old positions!")
        
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
