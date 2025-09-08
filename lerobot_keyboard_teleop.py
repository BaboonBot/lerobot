#!/usr/bin/env python3
"""
Real keyboard teleoperation for Rosmaster robot using LeRobot framework.

This script uses the standard LeRobot teleoperation workflow with real keyboard input.
Run this OUTSIDE of Docker on the host system so pynput can access keyboard.

Key Controls:
- q/a: Joint 1 (+/-)
- w/s: Joint 2 (+/-)  
- e/d: Joint 3 (+/-)
- r/f: Joint 4 (+/-)
- t/g: Joint 5 (+/-)
- y/h: Joint 6 (+/-)
- ESC: Exit
"""

import sys
import os
import time
import numpy as np

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lerobot.robots.rosmaster import RosmasterRobotConfig
from lerobot.teleoperators.rosmaster_keyboard import RosmasterKeyboardTeleopConfig
from lerobot.robots.utils import make_robot_from_config
from lerobot.teleoperators.utils import make_teleoperator_from_config
from lerobot.utils.robot_utils import busy_wait


def custom_teleop_loop(teleop, robot, fps=30):
    """Custom teleoperation loop that handles Rosmaster's joint_positions correctly."""
    loop_count = 0
    
    print("\n🎮 Keyboard Teleoperation Active!")
    print("Key Controls:")
    print("  q/a: Joint 1 (+/-)")
    print("  w/s: Joint 2 (+/-)")
    print("  e/d: Joint 3 (+/-)")
    print("  r/f: Joint 4 (+/-)")
    print("  t/g: Joint 5 (+/-)")
    print("  y/h: Joint 6 (+/-)")
    print("  ESC: Exit")
    print(f"  Step size: 5.0°")
    print("\n" + "="*50)
    
    try:
        while True:
            loop_start = time.perf_counter()
            action = teleop.get_action()
            
            robot.send_action(action)
            dt_s = time.perf_counter() - loop_start
            busy_wait(1 / fps - dt_s)
            
            loop_s = time.perf_counter() - loop_start
            loop_count += 1

            # Display current joint positions (every 30 loops = ~1 second)
            if loop_count % 30 == 1:
                # Extract positions from individual joint actions
                positions = [action.get(f"servo_{i+1}", 0.0) for i in range(6)]
                print(f"\r🎯 Joints: [{positions[0]:5.1f}° {positions[1]:5.1f}° {positions[2]:5.1f}° {positions[3]:5.1f}° {positions[4]:5.1f}° {positions[5]:5.1f}°] | {1/loop_s:.0f}Hz", end="", flush=True)
                
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received.")
    except Exception as e:
        if "disconnecting" in str(e).lower():
            print("\n✅ ESC pressed - teleoperation ended.")
        else:
            raise e
def main():
    SERIAL_PORT = "/dev/myserial"
    
    print("🤖 LeRobot Keyboard Teleoperation - Rosmaster Robot")
    print("=" * 60)
    
    try:
        # Create robot configuration
        robot_config = RosmasterRobotConfig(
            id="keyboard_rosmaster",
            com=SERIAL_PORT
        )
        
        # Create teleoperator configuration  
        teleop_config = RosmasterKeyboardTeleopConfig(
            id="keyboard_teleop",
            joint_step=5.0,
            mock=False  # Real keyboard input
        )
        
        print(f"🔌 Creating robot with config: {robot_config}")
        robot = make_robot_from_config(robot_config)
        
        print(f"🎮 Creating teleoperator with config: {teleop_config}")
        teleop = make_teleoperator_from_config(teleop_config)
        
        print("🔗 Connecting robot...")
        robot.connect(calibrate=True)
        robot.configure()
        print("✅ Robot connected!")
        
        print("🔗 Connecting teleoperator...")
        teleop.connect()
        print("✅ Teleoperator connected!")
        
        if not robot.is_connected:
            raise ValueError("Robot failed to connect!")
            
        if not teleop.is_connected:
            raise ValueError("Teleoperator failed to connect!")
        
        print("\n🚀 Starting real keyboard teleoperation...")
        print("⚡ Press keys to move joints, ESC to exit")
        
        # Run real teleoperation
        custom_teleop_loop(teleop, robot, fps=30)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🧹 Cleaning up...")
        try:
            if 'teleop' in locals():
                teleop.disconnect()
                print("✅ Teleoperator disconnected")
        except:
            pass
            
        try:
            if 'robot' in locals():
                robot.disconnect()
                print("✅ Robot disconnected")
        except:
            pass
        
        print("👋 Teleoperation ended!")


if __name__ == "__main__":
    main()
