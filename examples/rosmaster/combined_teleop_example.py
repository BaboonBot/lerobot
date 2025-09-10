#!/usr/bin/env python3
"""
Example script for using the Rosmaster Combined Teleoperator

This demonstrates how to control both mecanum wheels and robot arm simultaneously
using the rosmaster_combined teleoperator.

Usage:
    python combined_teleop_example.py

Key mappings:
    Mecanum Wheels (WASDQE):
    - W/S: Forward/Backward
    - A/D: Strafe Left/Right  
    - Q/E: Rotate Left/Right
    
    Robot Arm (TGYH UJIK OLP;):
    - T/G: Joint 1 (+/-) - Base rotation
    - Y/H: Joint 2 (+/-) - Shoulder
    - U/J: Joint 3 (+/-) - Elbow  
    - I/K: Joint 4 (+/-) - Wrist pitch
    - O/L: Joint 5 (+/-) - Wrist roll
    - P/;: Joint 6 (+/-) - Gripper
    
    Safety Controls:
    - SPACE: Lock/Unlock (robot starts locked!)
    - R: Reset to stopped state
    - ESC: Exit
"""

import sys
import os

def main():
    print("🤖 Rosmaster Combined Teleoperator Example")
    print("=" * 50)
    
    # The actual command to run the combined teleoperator
    command = """lerobot-teleoperate \\
  --robot.type=rosmaster \\
  --robot.com="/dev/myserial" \\
  --robot.id="my_rosmaster_robot" \\
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \\
  --teleop.type=rosmaster_combined \\
  --teleop.movement_step=0.3 \\
  --teleop.rotation_step=1.0 \\
  --teleop.joint_step=2.0 \\
  --display_data=true"""
    
    print("\n📋 Command to run:")
    print(command)
    
    print("\n🎮 Key Controls:")
    print("  Mecanum Wheels (WASDQE):")
    print("    W/S: Forward/Backward movement")
    print("    A/D: Strafe Left/Right movement")
    print("    Q/E: Rotate Left/Right")
    print("")
    print("  Robot Arm (TGYH UJIK OLP;):")
    print("    T/G: Joint 1 (+/-) - Base rotation")
    print("    Y/H: Joint 2 (+/-) - Shoulder")
    print("    U/J: Joint 3 (+/-) - Elbow")
    print("    I/K: Joint 4 (+/-) - Wrist pitch")
    print("    O/L: Joint 5 (+/-) - Wrist roll")
    print("    P/;: Joint 6 (+/-) - Gripper")
    print("")
    print("  Safety Controls:")
    print("    SPACE: Lock/Unlock (starts locked!)")
    print("    R: Reset to stopped state")
    print("    ESC: Exit")
    
    print("\n⚠️  Safety Reminders:")
    print("  1. Robot starts LOCKED - press SPACE to unlock")
    print("  2. Look for 🔒 LOCKED or 🔓 UNLOCKED messages")
    print("  3. Press R to stop all movement at any time")
    print("  4. Always lock when done controlling")
    
    print("\n🚀 Ready to run? Copy the command above to your terminal!")
    
    # Optionally, you could execute the command directly:
    run_now = input("\n❓ Run the teleoperator now? [y/N]: ").lower().strip()
    if run_now == 'y':
        print("\n🎮 Starting combined teleoperator...")
        print("   (Remember to press SPACE to unlock!)")
        os.system(command.replace('\\', ''))
    else:
        print("\n👋 Copy the command above when you're ready to start!")

if __name__ == "__main__":
    main()
