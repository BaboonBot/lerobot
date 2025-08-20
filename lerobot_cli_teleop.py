#!/usr/bin/env python3
"""
Official LeRobot teleoperation using the standard CLI command.

This demonstrates how to use the standard LeRobot workflow with config files.
"""

import subprocess
import sys
import os

def main():
    # Add src to Python path for development
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{src_path}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = src_path
    
    print("🤖 Running LeRobot Teleoperation Command")
    print("=" * 50)
    
    # Standard LeRobot teleoperation command
    cmd = [
        sys.executable, "-m", "lerobot.teleoperate",
        "--robot.type=rosmaster",
        "--robot.id=my_rosmaster", 
        "--robot.com=/dev/ttyUSB0",
        "--teleop.type=rosmaster_keyboard",
        "--teleop.id=my_keyboard",
        "--teleop.joint_step=5.0",
        "--fps=30"
    ]
    
    print("Executing command:")
    print(" ".join(cmd))
    print("\nKey Controls:")
    print("  q/a: Joint 1 (+/-)")
    print("  w/s: Joint 2 (+/-)")
    print("  e/d: Joint 3 (+/-)")
    print("  r/f: Joint 4 (+/-)")
    print("  t/g: Joint 5 (+/-)")
    print("  y/h: Joint 6 (+/-)")
    print("  ESC: Exit")
    print("\n" + "="*50)
    
    try:
        result = subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n🛑 Teleoperation interrupted")
        return 0
    
    print("✅ Teleoperation completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
