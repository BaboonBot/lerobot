#!/usr/bin/env python3
"""
Docker-compatible keyboard control test for Rosmaster robot.
This version uses real keyboard input within the Docker environment.
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
    """Custom teleoperation loop that shows keyboard activity and robot response."""
    loop_count = 0
    last_positions = None
    
    print("🚀 Teleoperation started!")
    print("Press keys to control robot. ESC to exit.")
    print()
    
    try:
        while True:
            loop_start = time.perf_counter()
            
            # Get action from teleoperator
            action = teleop.get_action()
            
            # Send to robot
            robot.send_action(action)
            
            # Check for position changes
            current_positions = action.get("joint_positions")
            if current_positions is not None:
                current_positions = np.array(current_positions)
                
                # Only print when positions change or every 100 loops
                if (last_positions is None or 
                    not np.array_equal(current_positions, last_positions) or 
                    loop_count % 100 == 0):
                    
                    if last_positions is not None and not np.array_equal(current_positions, last_positions):
                        print(f"\n🎯 POSITION CHANGED - Loop {loop_count}")
                    elif loop_count % 100 == 0:
                        print(f"\n📊 Status - Loop {loop_count}")
                    
                    for i, pos in enumerate(current_positions):
                        print(f"  joint_{i+1}: {pos:7.2f}°")
                    
                    dt_s = time.perf_counter() - loop_start
                    busy_wait(1 / fps - dt_s)
                    loop_s = time.perf_counter() - loop_start
                    print(f"  time: {loop_s * 1e3:.2f}ms ({1 / loop_s:.0f} Hz)")
                    
                    last_positions = current_positions.copy()
                else:
                    # Just maintain timing without printing
                    dt_s = time.perf_counter() - loop_start
                    busy_wait(1 / fps - dt_s)
            
            loop_count += 1
            
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
    except Exception as e:
        print(f"\n❌ Error in teleoperation loop: {e}")


def main():
    SERIAL_PORT = "/dev/ttyUSB0"
    
    print("🤖 Docker LeRobot Keyboard Control")
    print("=" * 50)
    
    try:
        # Create robot configuration
        robot_config = RosmasterRobotConfig(
            id="docker_rosmaster",
            com=SERIAL_PORT
        )
        
        # Create teleoperator configuration - DISABLE mock mode for real keyboard
        teleop_config = RosmasterKeyboardTeleopConfig(
            id="docker_keyboard",
            joint_step=5.0,
            mock=False  # REAL KEYBOARD INPUT
        )
        
        print(f"🔌 Creating robot: {robot_config}")
        robot = make_robot_from_config(robot_config)
        
        print(f"🎮 Creating teleoperator: {teleop_config}")
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
        
        print("\n🎮 Keyboard Controls:")
        print("  q/a: Joint 1 (+/-)     r/f: Joint 4 (+/-)")
        print("  w/s: Joint 2 (+/-)     t/g: Joint 5 (+/-)")
        print("  e/d: Joint 3 (+/-)     y/h: Joint 6 (+/-)")
        print("  ESC: Exit")
        print(f"  Step: {teleop_config.joint_step}°")
        print()
        
        # Start teleoperation loop
        custom_teleop_loop(teleop, robot, fps=30)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🧹 Cleaning up...")
        try:
            if 'teleop' in locals() and teleop.is_connected:
                teleop.disconnect()
                print("✅ Teleoperator disconnected")
        except:
            pass
            
        try:
            if 'robot' in locals() and robot.is_connected:
                robot.disconnect()
                print("✅ Robot disconnected")
        except:
            pass
        
        print("👋 Docker session completed!")


if __name__ == "__main__":
    main()
