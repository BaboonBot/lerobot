#!/usr/bin/env python3
"""
Power and voltage diagnostic for Rosmaster robot.
"""
import sys
import time

sys.path.append('/workspace/py_install')
from Rosmaster_Lib import Rosmaster

def check_power_and_voltage():
    """Check power supply and voltage levels."""
    
    print("🔋 POWER SUPPLY DIAGNOSTIC")
    print("=" * 40)
    
    try:
        print("🔌 Connecting to robot...")
        bot = Rosmaster(com="/dev/myserial", debug=True)
        bot.create_receive_threading()
        time.sleep(1)
        
        # Check battery voltage
        print("\n⚡ Reading battery voltage...")
        voltage = bot.get_battery_voltage()
        print(f"🔋 Battery voltage: {voltage}V")
        
        if voltage < 1.0:
            print("❌ CRITICAL: No voltage detected!")
            print("   ➤ Check if external power supply is connected")
            print("   ➤ Check if power switch is ON")
        elif voltage < 6.0:
            print("⚠️  WARNING: Low voltage detected!")
            print("   ➤ Servos may not have enough power to move")
            print("   ➤ Check external power supply (should be 6-12V)")
        else:
            print("✅ Voltage levels appear adequate for servo operation")
        
        # Test beep to confirm basic communication
        print("\n📢 Testing basic communication...")
        bot.set_beep(300)
        print("🔊 Beep command sent - did you hear it?")
        
        # Try to read servo positions to check servo bus communication
        print("\n🔍 Testing servo bus communication...")
        angles = bot.get_uart_servo_angle_array()
        print(f"📊 Servo positions: {angles}")
        
        if all(angle == -1 for angle in angles):
            print("❌ PROBLEM: Cannot read any servo positions")
            print("   ➤ Servo bus may be disconnected")
            print("   ➤ Check servo cables between controller and servos")
        elif any(angle == -1 for angle in angles):
            print("⚠️  WARNING: Some servos not responding")
            print("   ➤ Check individual servo connections")
        else:
            print("✅ Servo bus communication working")
            
        return voltage
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return 0
    finally:
        try:
            if 'bot' in locals():
                bot.set_uart_servo_torque(0)
        except:
            pass

if __name__ == "__main__":
    voltage = check_power_and_voltage()
    
    print(f"\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 20)
    print(f"Battery voltage: {voltage}V")
    
    if voltage < 1.0:
        print("🔴 Status: POWER FAILURE - No external power detected")
    elif voltage < 6.0:
        print("🟡 Status: LOW POWER - May not be sufficient for servo movement")
    else:
        print("🟢 Status: POWER OK - Issue likely in servo connections or hardware")
