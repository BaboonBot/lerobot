#!/usr/bin/env python3
"""Try different position write methods"""
import serial
import time

PORT = '/dev/ttyACM0'
BAUDRATE = 1000000
MOTOR_ID = 1

def checksum(data):
    return (~sum(data[2:]) & 0xFF)

def read_position(ser, motor_id):
    ser.reset_input_buffer()
    packet = [0xFF, 0xFF, motor_id, 0x04, 0x02, 0x38, 0x02]
    packet.append(checksum(packet))
    ser.write(bytes(packet))
    time.sleep(0.1)
    response = ser.read(20)
    if len(response) >= 7:
        return response[5] + (response[6] << 8)
    return None

ser = serial.Serial(PORT, BAUDRATE, timeout=0.3)
print(f"Connected\n")

target = 2000
pos_low = target & 0xFF
pos_high = (target >> 8) & 0xFF

print(f"Trying to move to {target}\n")

# Method 1: Write only position (not speed)
print("Method 1: Position only (addr 0x2A, 2 bytes)")
packet = [0xFF, 0xFF, MOTOR_ID, 0x05, 0x03, 0x2A, pos_low, pos_high]
packet.append(checksum(packet))
print(f"Packet: {' '.join(f'{b:02X}' for b in packet)}")
ser.write(bytes(packet))
time.sleep(1.0)
pos = read_position(ser, MOTOR_ID)
print(f"Position: {pos}\n")

# Method 2: Write position with speed 0 (max speed)
print("Method 2: Position + Speed=0")
packet = [0xFF, 0xFF, MOTOR_ID, 0x07, 0x03, 0x2A, pos_low, pos_high, 0x00, 0x00]
packet.append(checksum(packet))
print(f"Packet: {' '.join(f'{b:02X}' for b in packet)}")
ser.write(bytes(packet))
time.sleep(1.0)
pos = read_position(ser, MOTOR_ID)
print(f"Position: {pos}\n")

# Method 3: Write position with high speed
print("Method 3: Position + Speed=2047 (max)")
packet = [0xFF, 0xFF, MOTOR_ID, 0x07, 0x03, 0x2A, pos_low, pos_high, 0xFF, 0x07]
packet.append(checksum(packet))
print(f"Packet: {' '.join(f'{b:02X}' for b in packet)}")
ser.write(bytes(packet))
time.sleep(1.0)
pos = read_position(ser, MOTOR_ID)
print(f"Position: {pos}\n")

ser.close()
