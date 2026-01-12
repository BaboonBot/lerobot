# Rosmaster & Yahboom Technical Deep Dive

## Overview

This document provides an in-depth technical explanation of how the Rosmaster robot integration works within the LeRobot framework, including detailed explanations of every operation involving Yahboom hardware and Rosmaster protocols.

## System Architecture

### Component Hierarchy

```
LeRobot Framework
├── Robot Layer (src/lerobot/robots/rosmaster/)
│   ├── rosmaster.py - Main robot interface
│   └── configuration_rosmaster.py - Robot configuration
├── Motor Bus Layer (src/lerobot/motors/yahboom/)
│   ├── yahboom.py - Hardware communication bus
│   └── rosmaster_driver.py - Low-level driver (embedded)
└── Teleoperator Layer (src/lerobot/teleoperators/rosmaster_combined/)
    ├── teleop_rosmaster_combined.py - Combined arm+base input handling
    └── configuration_rosmaster_combined.py - Combined teleop configuration
```

### Data Flow

```
Keyboard Input → Teleoperator → Robot → Motor Bus → Hardware
     ↑                                                    ↓
User Interface ←←←←←←←←←←←← Feedback ←←←←←←←←←←←← Serial Protocol
```

## Robot Layer (`RosmasterRobot`)

### Class Architecture

The `RosmasterRobot` class inherits from LeRobot's `Robot` base class and implements the following key interfaces:

```python
class RosmasterRobot(Robot):
    def __init__(self, com: str, **kwargs)
    def connect(self) -> None
    def send_action(self, action: dict) -> None
    def get_observation(self) -> dict
    def disconnect(self) -> None
```

### Connection Process

1. **Initialization:**
   ```python
   self.motors_bus = RosmasterMotorsBus(
       port=self.config.com,
       motors=self.motors
   )
   ```

2. **Motor Configuration:**
   - 6 servo motors with IDs 1-6
   - Individual position control
   - Joint limits: 0-180° (1-4,6), 0-270° (5)

3. **Hardware Handshake:**
   - Firmware version check
   - Torque enable for responsive control
   - Communication verification

### Action Processing

**Input Format:**
```python
action = {
    "servo_1": 90.0,  # degrees
    "servo_2": 45.0,
    "servo_3": 120.0,
    "servo_4": 60.0,
    "servo_5": 135.0,
    "servo_6": 90.0
}
```

**Processing Steps:**
1. **Validation:** Check joint limits and data types
2. **Conversion:** Map servo names to motor IDs
3. **Safety Check:** Verify positions within safe ranges
4. **Execution:** Send commands to motor bus

### Observation Handling

The robot provides position feedback through:
```python
observation = {
    "servo_1": current_angle_1,
    "servo_2": current_angle_2,
    # ... for all 6 servos
}
```

## Motor Bus Layer (`RosmasterMotorsBus`)

### Hardware Abstraction

The `RosmasterMotorsBus` class acts as an adapter between LeRobot's `MotorsBus` interface and the Yahboom Rosmaster hardware:

```python
class RosmasterMotorsBus(MotorsBus):
    def sync_write(self, data_name: str, values: dict) -> None
    def sync_read(self, data_name: str, motors: list) -> dict
    def enable_torque(self, motors: list) -> None
    def disable_torque(self, motors: list) -> None
```

### Change Detection Algorithm

**Problem:** LeRobot framework calls `get_action()` continuously at 10Hz, which would flood the hardware with identical position commands.

**Solution:** Implement position change detection:

```python
def sync_write(self, data_name: str, values: dict) -> None:
    # Check if we have stored previous positions
    if not hasattr(self, '_last_positions'):
        self._last_positions = {}
    
    # Only send commands for motors that have changed position
    changed_motors = {}
    for motor_id, angle in ids_values.items():
        last_angle = self._last_positions.get(motor_id, None)
        # Only send command if position changed by more than 0.5 degrees
        if last_angle is None or abs(angle - last_angle) > 0.5:
            changed_motors[motor_id] = angle
            self._last_positions[motor_id] = angle
    
    if not changed_motors:
        return  # Silent return - no movement needed
    
    # Send commands only to motors that need to move
    for motor_id, angle in changed_motors.items():
        self.driver.set_uart_servo_angle(s_id=motor_id, s_angle=angle, run_time=500)
```

**Benefits:**
- Eliminates command flooding
- Reduces servo stress and wear
- Improves system responsiveness
- Prevents "random" micro-movements

### Serial Communication

**Protocol Details:**
- Baud Rate: 115200
- Data Bits: 8
- Stop Bits: 1
- Parity: None
- Flow Control: None

**Command Structure:**
```
[HEADER][DEVICE_ID][LENGTH][FUNCTION][DATA...][CHECKSUM]
```

**Key Functions:**
- `FUNC_UART_SERVO` (0x20): Individual servo control
- `FUNC_ARM_CTRL` (0x23): All-servo control
- `FUNC_VERSION` (0x51): Firmware version

## Yahboom Hardware Protocol

### Servo Control Commands

**Individual Servo Control:**
```python
def set_uart_servo_angle(self, s_id, s_angle, run_time=500):
    # Convert angle to pulse value based on servo ID
    value = self.__arm_convert_value(s_id, s_angle)
    
    # Send command with timing control
    self.set_uart_servo(s_id, value, run_time)
```

**Angle to Pulse Conversion:**
- **Servos 1-4,6:** `pulse = (3100-900) * (angle-180) / (0-180) + 900`
- **Servo 5:** `pulse = (3700-380) * (angle-0) / (270-0) + 380`

### Multi-Servo Control

**Simultaneous Control:**
```python
def set_uart_servo_angle_array(self, angle_s=[90,90,90,90,90,180], run_time=500):
    # Convert all angles to pulse values
    temp_val = [self.__arm_convert_value(i+1, angle_s[i]) for i in range(6)]
    
    # Pack into command structure
    cmd = [HEADER, DEVICE_ID, LENGTH, FUNC_ARM_CTRL, ...pulse_data..., run_time]
    
    # Send complete command
    self.ser.write(cmd)
```

### Position Feedback

**Reading Current Positions:**
```python
def get_uart_servo_angle_array(self):
    # Request all servo positions
    self.__request_data(self.FUNC_ARM_CTRL, 1)
    
    # Wait for response with timeout
    timeout = 30
    while timeout > 0:
        if self.__read_arm_ok == 1:
            # Convert pulse values back to angles
            angle = [self.__arm_convert_angle(i+1, self.__read_arm[i]) for i in range(6)]
            return angle
        time.sleep(.001)
        timeout -= 1
```

### Torque Management

**Enable/Disable Torque:**
```python
def set_uart_servo_torque(self, enable):
    # enable=0: Servos can be moved manually
    # enable=1: Servos resist manual movement
    cmd = [HEADER, DEVICE_ID, LENGTH, FUNC_UART_SERVO_TORQUE, enable]
    self.ser.write(cmd)
```

## Teleoperator Layer (`RosmasterKeyboardTeleop`)

### Real-Time Input Processing

**Keyboard Event Handling:**
```python
class RosmasterKeyboardTeleop(Teleoperator):
    def __init__(self, config):
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self.event_queue = Queue()
        self.current_pressed = {}
```

**Event Processing:**
```python
def _drain_pressed_keys(self):
    while not self.event_queue.empty():
        key_char, is_pressed = self.event_queue.get_nowait()
        if is_pressed:
            self.current_pressed[key_char] = True
        else:
            self.current_pressed.pop(key_char, None)
```

### Safety Mechanisms

**1. Position Lock System:**
```python
def _on_press(self, key):
    if key == keyboard.Key.space:
        self.position_locked = not self.position_locked
        status = "🔒 LOCKED" if self.position_locked else "🔓 UNLOCKED"
        print(f"Position control: {status}")
```

**2. Rate Limiting:**
```python
def get_action(self):
    current_time = time.time()
    if current_time - self.last_command_time < self.command_rate_limit:
        # Return current positions without changes
        return self._current_action()
```

**3. Joint Limit Enforcement:**
```python
# Apply safety limits
for i in range(6):
    if i == 4:  # Joint 5 has range 0-270
        new_positions[i] = np.clip(new_positions[i], 0, 270)
    else:  # Joints 1-4,6 have range 0-180
        new_positions[i] = np.clip(new_positions[i], 0, 180)
```

### Action Generation

**Key to Movement Mapping:**
```python
self.key_to_joint_delta = {
    'q': (0, +self.config.joint_step),  # Joint 1 +
    'a': (0, -self.config.joint_step),  # Joint 1 -
    'w': (1, +self.config.joint_step),  # Joint 2 +
    's': (1, -self.config.joint_step),  # Joint 2 -
    # ... etc for all joints
}
```

**Action Construction:**
```python
def get_action(self) -> dict:
    # Process keyboard events
    self._drain_pressed_keys()
    
    # Check safety conditions
    if self.position_locked or rate_limited:
        return self._current_action()
    
    # Apply movements
    new_positions = self.current_positions.copy()
    for key_char in self.current_pressed:
        if key_char in self.key_to_joint_delta:
            joint_idx, delta = self.key_to_joint_delta[key_char]
            new_positions[joint_idx] += delta
    
    # Apply limits and update
    self.current_positions = np.clip(new_positions, joint_limits)
    
    # Return individual joint actions
    return {f"servo_{i+1}": self.current_positions[i] for i in range(6)}
```

## Communication Protocol Deep Dive

### Serial Frame Structure

**Standard Command Frame:**
```
Byte 0: Header (0xFF)
Byte 1: Device ID (0xFC)
Byte 2: Length (command length - 1)
Byte 3: Function Code
Byte 4-N: Data payload
Byte N+1: Checksum (sum of bytes 2-N) & 0xFF
```

### Servo Control Protocol

**Individual Servo Command (FUNC_UART_SERVO = 0x20):**
```
Frame: [0xFF][0xFC][0x07][0x20][servo_id][pulse_low][pulse_high][time_low][time_high][checksum]

Example - Move servo 1 to 90°:
- servo_id: 1
- pulse_value: 2000 (calculated from angle)
- run_time: 500ms
Frame: [0xFF][0xFC][0x07][0x20][0x01][0xD0][0x07][0xF4][0x01][checksum]
```

**Array Control Command (FUNC_ARM_CTRL = 0x23):**
```
Frame: [0xFF][0xFC][0x11][0x23][s1_low][s1_high]...[s6_low][s6_high][time_low][time_high][checksum]

Example - Set all servos to 90°:
Frame: [0xFF][0xFC][0x11][0x23][0xD0][0x07][0xD0][0x07][0xD0][0x07][0xD0][0x07][0xD0][0x07][0xD0][0x07][0xF4][0x01][checksum]
```

### Response Processing

**Servo Position Response:**
```python
def __parse_data(self, ext_type, ext_data):
    if ext_type == self.FUNC_UART_SERVO:
        self.__read_id = struct.unpack('B', bytearray(ext_data[0:1]))[0]
        self.__read_val = struct.unpack('h', bytearray(ext_data[1:3]))[0]
    elif ext_type == self.FUNC_ARM_CTRL:
        # Parse all 6 servo positions
        for i in range(6):
            self.__read_arm[i] = struct.unpack('h', bytearray(ext_data[i*2:(i+1)*2]))[0]
        self.__read_arm_ok = 1
```

## Performance Optimizations

### 1. Change Detection

**Problem:** Continuous position commands cause servo stress
**Solution:** Only send commands when positions change >0.5°

### 2. Rate Limiting

**Problem:** Too frequent commands overwhelm hardware
**Solution:** Minimum 100ms between position updates

### 3. Batch Operations

**Problem:** Individual servo commands are slow
**Solution:** Use array commands when possible

### 4. Asynchronous Reading

**Problem:** Blocking reads affect control loop
**Solution:** Background thread for serial data processing

## Error Handling and Recovery

### Connection Errors

```python
def connect(self):
    try:
        if not self.is_connected:
            raise ConnectionError("Rosmaster driver failed to connect")
        self._handshake()
    except Exception as e:
        logging.error(f"Connection failed: {e}")
        # Attempt recovery or graceful degradation
```

### Communication Timeouts

```python
def get_uart_servo_angle(self, s_id):
    timeout = 30
    while timeout > 0:
        if self.__read_id > 0:
            return self._convert_to_angle()
        timeout -= 1
        time.sleep(.001)
    return -1  # Timeout error
```

### Hardware Safety

```python
def send_action(self, action):
    try:
        # Validate action
        self._validate_action(action)
        
        # Send to hardware
        self.motors_bus.sync_write("Goal_Position", action)
        
    except Exception as e:
        logging.error(f"Action failed: {e}")
        # Stop movement for safety
        self.motors_bus.disable_torque()
```

## Integration Points

### LeRobot Framework Integration

**Robot Registration:**
```python
# In src/lerobot/robots/__init__.py
from lerobot.robots.rosmaster.rosmaster import RosmasterRobot
```

**Configuration System:**
```python
# Using draccus for type-safe configuration
@dataclass
class RosmasterRobotConfig:
    com: str = "/dev/myserial"
    calibration_dir: Optional[Path] = None
```

**CLI Integration:**
```bash
python -m lerobot.teleoperate \
    --robot.type=rosmaster \
    --robot.com=/dev/myserial \
    --teleop.type=rosmaster_combined
```

### Data Flow Integration

1. **Teleoperator** generates actions (joint positions)
2. **Robot** validates and processes actions
3. **Motor Bus** optimizes and sends hardware commands
4. **Hardware** executes movements and provides feedback
5. **Robot** reads positions and provides observations
6. **LeRobot** logs data for training/analysis

## Advanced Features

### Calibration Support

```python
def calibrate(self):
    # Move to known reference positions
    reference_positions = [90, 90, 90, 90, 135, 90]
    
    # Record actual vs commanded positions
    calibration_data = {}
    for i, pos in enumerate(reference_positions):
        self.send_action({f"servo_{i+1}": pos})
        time.sleep(1.0)
        actual = self.get_observation()
        calibration_data[f"servo_{i+1}"] = {
            "commanded": pos,
            "actual": actual[f"servo_{i+1}"]
        }
    
    return calibration_data
```

### Multi-Robot Support

```python
class MultiRosmasterRobot:
    def __init__(self, robots_config):
        self.robots = {
            name: RosmasterRobot(**config) 
            for name, config in robots_config.items()
        }
    
    def send_action(self, actions):
        for robot_name, action in actions.items():
            self.robots[robot_name].send_action(action)
```

### Data Recording Integration

```python
def record_episode(self, teleop, robot, duration):
    episode_data = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # Get action from teleoperator
        action = teleop.get_action()
        
        # Send to robot
        robot.send_action(action)
        
        # Record observation
        obs = robot.get_observation()
        
        # Store timestamped data
        episode_data.append({
            "timestamp": time.time(),
            "action": action,
            "observation": obs
        })
        
        time.sleep(0.1)  # 10Hz recording
    
    return episode_data
```

This comprehensive technical documentation covers every aspect of the Rosmaster and Yahboom hardware integration, from low-level serial protocols to high-level LeRobot framework integration.
