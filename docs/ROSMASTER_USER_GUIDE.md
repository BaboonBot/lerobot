# Rosmaster Robot Integration with LeRobot

## Quick Start Guide

### Prerequisites
- Ubuntu/Jetson system with Python 3.10+
- LeRobot installed with virtual environment
- Rosmaster robot connected via USB serial

### Hardware Setup
1. Connect your Rosmaster robot to the computer via USB cable
2. Verify the device appears as `/dev/ttyUSB*` or `/dev/ttyACM*`
3. Create a symlink for consistent device naming:
   ```bash
   sudo ln -sf /dev/ttyUSB0 /dev/myserial
   # or sudo ln -sf /dev/ttyACM0 /dev/myserial
   ```

### Running the Robot

1. **Activate the virtual environment:**
   ```bash
   cd /home/jetson/lerobot
   source .venv/bin/activate
   ```

2. **Run keyboard teleoperation:**
   ```bash
   python -m lerobot.teleoperate \
       --robot.type=rosmaster \
       --robot.com=/dev/myserial \
       --teleop.type=rosmaster_keyboard \
       --fps=10
   ```

### Keyboard Controls

| Key | Action | Joint | Range |
|-----|--------|-------|-------|
| `q` / `a` | Joint 1 +/- | Base rotation | 0-180° |
| `w` / `s` | Joint 2 +/- | Shoulder | 0-180° |
| `e` / `d` | Joint 3 +/- | Elbow | 0-180° |
| `r` / `f` | Joint 4 +/- | Wrist pitch | 0-180° |
| `t` / `g` | Joint 5 +/- | Wrist roll | 0-270° |
| `y` / `h` | Joint 6 +/- | Gripper | 0-180° |
| `SPACE` | Lock/Unlock position | Safety lock | - |
| `ESC` | Disconnect | Shutdown | - |

**Important:** 
- Position is **LOCKED** by default - press `SPACE` to unlock movement
- Step size is 2° per keypress
- Commands are rate-limited to 100ms intervals

### Configuration Options

**Robot Configuration:**
- `--robot.com`: Serial port device (default: `/dev/myserial`)
- `--robot.type`: Must be `rosmaster`

**Teleoperator Configuration:**
- `--teleop.type`: Must be `rosmaster_keyboard`
- `--teleop.joint_step`: Step size in degrees (default: 2.0)

**System Configuration:**
- `--fps`: Control loop frequency (default: 10Hz)

### Safety Features

1. **Position Lock:** Prevents accidental movement - toggle with `SPACE`
2. **Rate Limiting:** Prevents command flooding (100ms minimum between moves)
3. **Joint Limits:** Automatic clamping to safe ranges
4. **Change Detection:** Only sends commands when positions actually change
5. **Torque Control:** Loose torque by default for manual intervention

### Troubleshooting

**Connection Issues:**
```bash
# Check device permissions
ls -la /dev/myserial
sudo chmod 666 /dev/ttyUSB0

# Verify device detection
python -c "from lerobot.robots.rosmaster import RosmasterRobot; print('✓ Import successful')"
```

**No Movement:**
1. Check if position is locked (press `SPACE` to unlock)
2. Verify serial connection
3. Check joint limits
4. Ensure proper device permissions

## Advanced Usage

### Recording Demonstrations
```bash
python -m lerobot.record \
    --robot.type=rosmaster \
    --robot.com=/dev/myserial \
    --teleop.type=rosmaster_keyboard \
    --fps=10 \
    --output-dir=./recordings
```

### Policy Training
```bash
python -m lerobot.train \
    --config=path/to/policy_config.yaml \
    --dataset-path=./recordings
```

### Custom Integration
```python
from lerobot.robots.rosmaster import RosmasterRobot
from lerobot.teleoperators.rosmaster_keyboard import RosmasterKeyboardTeleop

# Initialize robot
robot = RosmasterRobot(com="/dev/myserial")
robot.connect()

# Initialize teleoperator  
teleop = RosmasterKeyboardTeleop()
teleop.connect()

# Control loop
while True:
    action = teleop.get_action()
    robot.send_action(action)
```

## System Architecture

The Rosmaster integration consists of three main components:

1. **Robot Driver** (`src/lerobot/robots/rosmaster/`)
   - Hardware abstraction layer
   - Serial communication management
   - Joint position control

2. **Motor Bus** (`src/lerobot/motors/yahboom/`)
   - Low-level servo communication
   - Change detection optimization
   - Hardware safety features

3. **Teleoperator** (`src/lerobot/teleoperators/rosmaster_keyboard/`)
   - Real-time keyboard input
   - Safety interlocks
   - Action generation

## Technical Specifications

- **Communication:** Serial at 115200 baud
- **Control Rate:** Up to 10Hz (configurable)
- **Position Resolution:** 1° minimum
- **Response Time:** <100ms typical
- **Joint Count:** 6 DOF
- **Safety Features:** Position lock, rate limiting, joint limits
