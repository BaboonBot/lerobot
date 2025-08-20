#!/usr/bin/env python3
"""
Terminal-based teleoperation for Rosmaster robot.

This version works in Docker environments without X11/display.
Uses terminal input instead of keyboard events.

Commands:
- Type joint commands like: j1+ j1- j2+ j2- etc.
- Or single letters: q a w s e d r f t g y h
- Type 'help' for commands
- Type 'quit' or 'exit' to stop
"""

import time
import numpy as np
import threading
import sys

from lerobot.robots.utils import make_robot_from_config
from lerobot.robots.rosmaster import RosmasterRobotConfig


class TerminalTeleop:
    def __init__(self, robot):
        self.robot = robot
        self.current_positions = np.array([90.0, 90.0, 90.0, 90.0, 90.0, 90.0], dtype=np.float32)
        self.joint_step = 5.0
        self.running = True
        
        # Set initial position
        self.send_to_robot(self.current_positions)
        
    def send_to_robot(self, positions):
        """Send joint positions to robot"""
        try:
            action = {"joint_positions": positions}
            self.robot.send_action(action)
            return True
        except Exception as e:
            print(f"⚠️  Command failed: {e}")
            return False
    
    def process_command(self, cmd):
        """Process a command and move joints"""
        cmd = cmd.strip().lower()
        
        if cmd in ['quit', 'exit', 'q']:
            self.running = False
            return
            
        if cmd == 'help':
            self.show_help()
            return
            
        if cmd == 'pos':
            print(f"Current positions: {self.current_positions}")
            return
            
        if cmd == 'home':
            self.current_positions = np.array([90.0, 90.0, 90.0, 90.0, 90.0, 90.0], dtype=np.float32)
            if self.send_to_robot(self.current_positions):
                print(f"🏠 Moved to home position: {self.current_positions}")
            return
        
        # Parse movement commands
        new_positions = self.current_positions.copy()
        joint_moved = False
        
        # Single letter commands
        moves = []
        for char in cmd:
            if char == 'q':  # Joint 1 +
                new_positions[0] += self.joint_step
                moves.append("J1+")
                joint_moved = True
            elif char == 'a':  # Joint 1 -
                new_positions[0] -= self.joint_step
                moves.append("J1-")
                joint_moved = True
            elif char == 'w':  # Joint 2 +
                new_positions[1] += self.joint_step
                moves.append("J2+")
                joint_moved = True
            elif char == 's':  # Joint 2 -
                new_positions[1] -= self.joint_step
                moves.append("J2-")
                joint_moved = True
            elif char == 'e':  # Joint 3 +
                new_positions[2] += self.joint_step
                moves.append("J3+")
                joint_moved = True
            elif char == 'd':  # Joint 3 -
                new_positions[2] -= self.joint_step
                moves.append("J3-")
                joint_moved = True
            elif char == 'r':  # Joint 4 +
                new_positions[3] += self.joint_step
                moves.append("J4+")
                joint_moved = True
            elif char == 'f':  # Joint 4 -
                new_positions[3] -= self.joint_step
                moves.append("J4-")
                joint_moved = True
            elif char == 't':  # Joint 5 +
                new_positions[4] += self.joint_step
                moves.append("J5+")
                joint_moved = True
            elif char == 'g':  # Joint 5 -
                new_positions[4] -= self.joint_step
                moves.append("J5-")
                joint_moved = True
            elif char == 'y':  # Joint 6 +
                new_positions[5] += self.joint_step
                moves.append("J6+")
                joint_moved = True
            elif char == 'h':  # Joint 6 -
                new_positions[5] -= self.joint_step
                moves.append("J6-")
                joint_moved = True
        
        # Apply safety limits
        new_positions = np.clip(new_positions, 0, 180)
        
        if joint_moved:
            if self.send_to_robot(new_positions):
                self.current_positions = new_positions
                print(f"🎯 Moved: {', '.join(moves)} | Positions: {self.current_positions}")
        else:
            print("❓ Unknown command. Type 'help' for available commands.")
    
    def show_help(self):
        print("\n🎮 Available Commands:")
        print("   Movement (single letters):")
        print("     q/a: Joint 1 (+/-)")
        print("     w/s: Joint 2 (+/-)")
        print("     e/d: Joint 3 (+/-)")
        print("     r/f: Joint 4 (+/-)")
        print("     t/g: Joint 5 (+/-)")
        print("     y/h: Joint 6 (+/-)")
        print("   ")
        print("   Other commands:")
        print("     home: Move to home position (all 90°)")
        print("     pos: Show current positions")
        print("     help: Show this help")
        print("     quit/exit: Stop teleoperation")
        print(f"   Step size: {self.joint_step}°")
        print()


def main():
    SERIAL_PORT = "/dev/ttyUSB0"
    
    print("🤖 Rosmaster Robot Terminal Teleoperation")
    print("=" * 50)
    
    try:
        # Connect to robot
        print(f"🔌 Connecting to robot on port: {SERIAL_PORT}")
        robot_config = RosmasterRobotConfig(
            id="terminal_teleop",
            com=SERIAL_PORT
        )
        
        robot = make_robot_from_config(robot_config)
        robot.connect(calibrate=True)
        robot.configure()
        print("✅ Robot connected and configured!")
        
        # Create teleoperator
        teleop = TerminalTeleop(robot)
        print(f"📍 Initial position set: {teleop.current_positions}")
        
        # Show help
        teleop.show_help()
        
        # Main input loop
        print("🚀 Ready! Type commands and press Enter:")
        print("-" * 50)
        
        while teleop.running:
            try:
                user_input = input("rosmaster> ").strip()
                if user_input:
                    teleop.process_command(user_input)
            except KeyboardInterrupt:
                print("\n🛑 Keyboard interrupt received.")
                break
            except EOFError:
                print("\n🛑 Input ended.")
                break
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print(f"   • Check robot connection to: {SERIAL_PORT}")
        print("   • Verify port permissions")
        print("   • Ensure robot is powered on")
        
    finally:
        print("\n🧹 Cleaning up...")
        try:
            if 'robot' in locals():
                robot.disconnect()
                print("✅ Robot disconnected")
        except:
            pass
        
        print("👋 Teleoperation ended. Goodbye!")


if __name__ == "__main__":
    main()
