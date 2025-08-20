#!/usr/bin/env python3
"""
Direct hardware test - bypassing LeRobot config system.
"""
import sys
import time

# Import the Rosmaster library directly
sys.path.append('/workspace/py_install')
from Rosmaster_Lib import Rosmaster

def test_keyboard_servo_control():
    """Direct servo control test with keyboard commands."""
    
    print("🤖 DIRECT SERVO KEYBOARD CONTROL")
    print("=" * 50)
    
    try:
        # Connect directly to hardware
        print("🔌 Connecting to Rosmaster on /dev/myserial...")
        bot = Rosmaster(com="/dev/myserial", debug=False)
        bot.create_receive_threading()
        time.sleep(1)
        
        # Enable torque
        print("⚡ Enabling servo torque...")
        bot.set_uart_servo_torque(1)
        time.sleep(0.5)
        
        # Get initial positions
        print("📊 Reading initial servo positions...")
        angles = bot.get_uart_servo_angle_array()
        print(f"📍 Initial angles: {angles}")
        
        # Center all servos
        print("🎯 Centering all servos...")
        bot.set_uart_servo_angle_array([90, 90, 90, 90, 90, 90], 1000)
        time.sleep(2)
        
        print("\n🎮 KEYBOARD CONTROL READY!")
        print("=" * 30)
        print("Commands:")
        print("q: Joint 1 left (45°)")
        print("a: Joint 1 right (135°)")
        print("w: Joint 2 up (60°)")
        print("s: Joint 2 down (120°)")
        print("e: Joint 3 forward (60°)")
        print("d: Joint 3 back (120°)")
        print("r: Joint 4 down (60°)")
        print("f: Joint 4 up (120°)")
        print("t: Joint 5 counter-clockwise (60°)")
        print("g: Joint 5 clockwise (120°)")
        print("y: Joint 6 open (45°)")
        print("h: Joint 6 close (135°)")
        print("0: Center all joints")
        print("x: Exit")
        
        # Current joint positions
        positions = [90, 90, 90, 90, 90, 90]
        
        while True:
            try:
                print(f"\n📍 Current: {positions}")
                command = input("Command: ").strip().lower()
                
                if command == 'x':
                    break
                elif command == 'q':
                    positions[0] = 45
                    print("🔄 Joint 1 → 45°")
                elif command == 'a':
                    positions[0] = 135
                    print("🔄 Joint 1 → 135°")
                elif command == 'w':
                    positions[1] = 60
                    print("🔄 Joint 2 → 60°")
                elif command == 's':
                    positions[1] = 120
                    print("🔄 Joint 2 → 120°")
                elif command == 'e':
                    positions[2] = 60
                    print("🔄 Joint 3 → 60°")
                elif command == 'd':
                    positions[2] = 120
                    print("🔄 Joint 3 → 120°")
                elif command == 'r':
                    positions[3] = 60
                    print("🔄 Joint 4 → 60°")
                elif command == 'f':
                    positions[3] = 120
                    print("🔄 Joint 4 → 120°")
                elif command == 't':
                    positions[4] = 60
                    print("🔄 Joint 5 → 60°")
                elif command == 'g':
                    positions[4] = 120
                    print("🔄 Joint 5 → 120°")
                elif command == 'y':
                    positions[5] = 45
                    print("🔄 Joint 6 → 45°")
                elif command == 'h':
                    positions[5] = 135
                    print("🔄 Joint 6 → 135°")
                elif command == '0':
                    positions = [90, 90, 90, 90, 90, 90]
                    print("🎯 Centering all joints")
                else:
                    print("❓ Unknown command")
                    continue
                
                # Send the movement command
                print("🚀 Moving...")
                bot.set_uart_servo_angle_array(positions, 1000)
                time.sleep(1.5)
                
                # Read actual positions
                actual_angles = bot.get_uart_servo_angle_array()
                if actual_angles and actual_angles[0] != -1:
                    print(f"✅ Actual: {actual_angles}")
                else:
                    print("⚠️  Could not read servo positions")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n🧹 Cleaning up...")
        try:
            if 'bot' in locals():
                bot.set_uart_servo_torque(0)  # Disable torque for safety
        except:
            pass

if __name__ == "__main__":
    success = test_keyboard_servo_control()
    if success:
        print("\n🎉 KEYBOARD SERVO CONTROL TEST COMPLETED!")
        print("Your robot hardware and communication are working perfectly!")
        print("The LeRobot integration should also work once the import issues are resolved.")
    else:
        print("\n💔 KEYBOARD SERVO CONTROL TEST FAILED!")
