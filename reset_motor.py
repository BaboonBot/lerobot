#!/usr/bin/env python3
"""Reset motor to factory defaults and configure for full range"""
import serial
import time

PORT = '/dev/ttyACM0'
BAUDRATE = 1000000
MOTOR_ID = 1

def checksum(data):
    return (~sum(data[2:]) & 0xFF)

def write_1byte(ser, motor_id, address, value):
    packet = [0xFF, 0xFF, motor_id, 0x04, 0x03, address, value]
    packet.append(checksum(packet))
    ser.write(bytes(packet))
    time.sleep(0.1)

def write_2byte(ser, motor_id, address, value):
    low = value & 0xFF
    high = (value >> 8) & 0xFF
    packet = [0xFF, 0xFF, motor_id, 0x05, 0x03, address, low, high]
    packet.append(checksum(packet))
    ser.write(bytes(packet))
    time.sleep(0.1)

def unlock_eeprom(ser, motor_id):
    write_1byte(ser, motor_id, 0x30, 0x00)

def lock_eeprom(ser, motor_id):
    write_1byte(ser, motor_id, 0x30, 0x01)

print("="*60)
print("DISCONNECT POWER FROM MOTOR")
print("="*60)
input("Press Enter when power is disconnected...")

print("\nRECONNECT POWER TO MOTOR")
input("Press Enter when power is reconnected...")

time.sleep(2)

ser = serial.Serial(PORT, BAUDRATE, timeout=0.3)
print(f"\nConnected to {PORT}\n")

# Configure EEPROM
print("Unlocking EEPROM...")
unlock_eeprom(ser, MOTOR_ID)
time.sleep(0.3)

print("Setting position limits to 0-4095 (no limits)...")
write_2byte(ser, MOTOR_ID, 0x09, 0)     # Min limit = 0
write_2byte(ser, MOTOR_ID, 0x0B, 4095)  # Max limit = 4095

print("Setting mode to 0 (servo mode, position control)...")
write_1byte(ser, MOTOR_ID, 0x21, 0)

print("Locking EEPROM...")
lock_eeprom(ser, MOTOR_ID)
time.sleep(0.3)

# Enable torque
print("Enabling torque...")
write_1byte(ser, MOTOR_ID, 0x28, 1)

print("\n✓ Motor reset and configured")
print("  - Position limits: 0-4095 (full range)")
print("  - Mode: 0 (servo/position control)")
print("  - Torque: Enabled")

ser.close()
