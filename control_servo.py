#!/usr/bin/env python3
"""
Simple script to control a Feetech servo motor on ID 1
"""
import serial
import time
import sys

PORT = '/dev/ttyACM0'
BAUDRATE = 1000000
MOTOR_ID = 1

def checksum(data):
    return (~sum(data[2:]) & 0xFF)

def enable_torque(ser, motor_id):
    """Enable torque (address 0x28, value 1)"""
    packet = [0xFF, 0xFF, motor_id, 0x04, 0x03, 0x28, 0x01]
    packet.append(checksum(packet))
    ser.write(bytes(packet))
    time.sleep(0.1)

def disable_torque(ser, motor_id):
    """Disable torque (address 0x28, value 0)"""
    packet = [0xFF, 0xFF, motor_id, 0x04, 0x03, 0x28, 0x00]
    packet.append(checksum(packet))
    ser.write(bytes(packet))
    time.sleep(0.1)

def set_position(ser, motor_id, position, speed=100):
    """
    Set motor position
    Position: 0-4095 (12-bit resolution, SAFE RANGE: 875-3504)
    Speed: 0-255 (0 = max speed)
    """
    # SAFETY: Clamp to known safe physical limits
    if position < 875:
        print(f"⚠️  WARNING: Position {position} below safe minimum (875), clamping")
        position = 875
    elif position > 3504:
        print(f"⚠️  WARNING: Position {position} above safe maximum (3504), clamping")
        position = 3504
    
    # Goal Position address: 0x2A (2 bytes)
    # Goal Speed address: 0x2E (2 bytes)
    pos_low = position & 0xFF
    pos_high = (position >> 8) & 0xFF
    speed_low = speed & 0xFF
    speed_high = (speed >> 8) & 0xFF
    
    # Write position and speed
    packet = [0xFF, 0xFF, motor_id, 0x07, 0x03, 0x2A, pos_low, pos_high, speed_low, speed_high]
    packet.append(checksum(packet))
    ser.write(bytes(packet))
    time.sleep(0.05)

def read_position(ser, motor_id):
    """Read current position (address 0x38, 2 bytes)"""
    ser.reset_input_buffer()
    packet = [0xFF, 0xFF, motor_id, 0x04, 0x02, 0x38, 0x02]
    packet.append(checksum(packet))
    ser.write(bytes(packet))
    time.sleep(0.1)
    response = ser.read(20)
    if len(response) >= 7:
        position = response[5] + (response[6] << 8)
        return position
    return None

def main():
    print("="*60)
    print("FEETECH SERVO CONTROL - ID 1")
    print("="*60)
    
    ser = serial.Serial(PORT, BAUDRATE, timeout=0.3)
    print(f"✓ Connected to {PORT}\n")
    
    # Enable torque
    enable_torque(ser, MOTOR_ID)
    print("✓ Torque enabled\n")
    
    # Read current position
    current = read_position(ser, MOTOR_ID)
    if current is not None:
        print(f"Current position: {current}\n")
    
    print("Commands:")
    print("  Enter position (0-4095) to move")
    print("  'r' - read current position")
    print("  'h' - move to home (2190)")
    print("  'min' - move to minimum (875)")
    print("  'max' - move to maximum (3504)")
    print("  'off' - disable torque")
    print("  'on' - enable torque")
    print("  'q' - quit")
    print("="*60 + "\n")
    
    try:
        while True:
            cmd = input("Command: ").strip()
            
            if cmd == 'q':
                break
            elif cmd == 'r':
                pos = read_position(ser, MOTOR_ID)
                print(f"Current position: {pos}")
            elif cmd == 'h':
                print("Moving to home (2190)...")
                set_position(ser, MOTOR_ID, 2190, speed=100)
                time.sleep(2.0)
                pos = read_position(ser, MOTOR_ID)
                print(f"Position: {pos}")
            elif cmd == 'min':
                print("Moving to minimum (875)...")
                set_position(ser, MOTOR_ID, 875, speed=100)
                time.sleep(2.0)
                pos = read_position(ser, MOTOR_ID)
                print(f"Position: {pos}")
            elif cmd == 'max':
                print("Moving to maximum (3504)...")
                set_position(ser, MOTOR_ID, 3504, speed=100)
                time.sleep(2.0)
                pos = read_position(ser, MOTOR_ID)
                print(f"Position: {pos}")
            elif cmd == 'off':
                disable_torque(ser, MOTOR_ID)
                print("✓ Torque disabled")
            elif cmd == 'on':
                enable_torque(ser, MOTOR_ID)
                print("✓ Torque enabled")
            elif cmd.isdigit():
                position = int(cmd)
                if 0 <= position <= 4095:
                    print(f"Moving to position {position}...")
                    set_position(ser, MOTOR_ID, position, speed=100)
                    time.sleep(2.0)
                    pos = read_position(ser, MOTOR_ID)
                    print(f"Position: {pos}")
                else:
                    print("Position must be 0-4095")
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted!")
    
    finally:
        disable_torque(ser, MOTOR_ID)
        ser.close()
        print("\n✓ Torque disabled and disconnected")

if __name__ == "__main__":
    main()
