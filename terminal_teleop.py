#!/usr/bin/env python3
"""
Simple terminal teleop for Rosmaster robot.
Direct joint angle input via terminal commands.
"""

import sys
import time
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lerobot.robots.rosmaster import RosmasterRobotConfig

def validate_angle(angle, joint_name):
    """Validate angle is within 0-180 degrees."""
    if not (0 <= angle <= 180):
        print(f"❌ Error: {joint_name} angle {angle}° out of range [0-180]")
        return False
    return True

def show_help():
    """Show available commands."""
    print("\n📋 Available Commands:")
    print("  set <joint> <angle>     - Set single joint (e.g., 'set servo_1 120')")
    print("  set all <angles>        - Set all 6 joints (e.g., 'set all 90 120 45 90 90 90')")
    print("  get                     - Show current joint positions")
    print("  move <angles>           - Quick set all joints (e.g., 'move 90 120 45 90 90 90')")
    print("  help                    - Show this help")
    print("  quit                    - Exit")
    print("\n📍 Joint Names: servo_1, servo_2, servo_3, servo_4, servo_5, servo_6")
    print("📐 All angles in degrees (0-180)")

def show_current_positions(robot):
    """Show current robot positions."""
    try:
        obs = robot.get_observation()
        positions = obs['joint_positions']
        print("\n📍 Current Joint Positions:")
        for i, pos in enumerate(positions):
            print(f"  servo_{i+1}: {pos:6.1f}°")
    except Exception as e:
        print(f"❌ Error reading positions: {e}")

def main():
    print("🤖 Rosmaster Terminal Teleop")
    print("=" * 40)
    
    # Create and connect robot
    try:
        config = RosmasterRobotConfig()
        robot = config.create_robot()
        print("🔌 Connecting to robot...")
        robot.connect()
        print("✅ Robot connected!")
    except Exception as e:
        print(f"❌ Failed to connect to robot: {e}")
        return
    
    show_help()
    show_current_positions(robot)
    
    print("\nReady for commands!")
    
    try:
        while True:
            try:
                command = input("\nrosmaster> ").strip()
                if not command:
                    continue
                    
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd in ['quit', 'exit', 'q']:
                    break
                    
                elif cmd == 'help':
                    show_help()
                    
                elif cmd == 'get':
                    show_current_positions(robot)
                    
                elif cmd == 'move':
                    # Quick move command: move 90 120 45 90 90 90
                    if len(parts) != 7:
                        print("❌ Usage: move <servo_1> <servo_2> <servo_3> <servo_4> <servo_5> <servo_6>")
                        continue
                    
                    try:
                        angles = [float(parts[i+1]) for i in range(6)]
                        
                        # Validate all angles
                        valid = True
                        for i, angle in enumerate(angles):
                            if not validate_angle(angle, f"servo_{i+1}"):
                                valid = False
                                break
                        
                        if not valid:
                            continue
                        
                        # Send action
                        action = {f"servo_{i+1}": angles[i] for i in range(6)}
                        print(f"🎯 Moving to: {angles}")
                        robot.send_action(action)
                        
                        # Wait a bit and show new position
                        time.sleep(0.5)
                        show_current_positions(robot)
                        
                    except ValueError:
                        print("❌ All angles must be numbers")
                    except Exception as e:
                        print(f"❌ Error moving robot: {e}")
                
                elif cmd == 'set':
                    if len(parts) < 3:
                        print("❌ Usage: set <joint> <angle> OR set all <angle1> ... <angle6>")
                        continue
                    
                    if parts[1].lower() == 'all':
                        # Set all joints
                        if len(parts) != 8:  # 'set' 'all' + 6 angles
                            print("❌ Usage: set all <servo_1> <servo_2> <servo_3> <servo_4> <servo_5> <servo_6>")
                            continue
                        
                        try:
                            angles = [float(parts[i+2]) for i in range(6)]
                            
                            # Validate all angles
                            valid = True
                            for i, angle in enumerate(angles):
                                if not validate_angle(angle, f"servo_{i+1}"):
                                    valid = False
                                    break
                            
                            if not valid:
                                continue
                            
                            # Send action
                            action = {f"servo_{i+1}": angles[i] for i in range(6)}
                            print(f"🎯 Setting all joints to: {angles}")
                            robot.send_action(action)
                            
                            # Wait and show new position
                            time.sleep(0.5)
                            show_current_positions(robot)
                            
                        except ValueError:
                            print("❌ All angles must be numbers")
                        except Exception as e:
                            print(f"❌ Error setting joints: {e}")
                    
                    else:
                        # Set single joint
                        joint = parts[1].lower()
                        if not joint.startswith('servo_') or joint not in [f'servo_{i+1}' for i in range(6)]:
                            print("❌ Invalid joint. Use: servo_1, servo_2, servo_3, servo_4, servo_5, servo_6")
                            continue
                        
                        try:
                            angle = float(parts[2])
                            if not validate_angle(angle, joint):
                                continue
                            
                            # Send action (need to get current positions for other joints)
                            obs = robot.get_observation()
                            current_positions = obs['joint_positions']
                            
                            action = {}
                            for i in range(6):
                                servo_name = f"servo_{i+1}"
                                if servo_name == joint:
                                    action[servo_name] = angle
                                else:
                                    action[servo_name] = current_positions[i]
                            
                            print(f"🎯 Setting {joint} to {angle}°")
                            robot.send_action(action)
                            
                            # Wait and show new position
                            time.sleep(0.5)
                            show_current_positions(robot)
                            
                        except ValueError:
                            print("❌ Angle must be a number")
                        except Exception as e:
                            print(f"❌ Error setting joint: {e}")
                
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n🔌 Interrupted, exiting...")
                break
            except EOFError:
                print("\n🔌 EOF, exiting...")
                break
                
    finally:
        print("🔌 Disconnecting robot...")
        robot.disconnect()
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
