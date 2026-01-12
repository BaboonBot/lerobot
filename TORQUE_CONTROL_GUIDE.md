# Rosmaster Torque Control Guide

## Overview
The enhanced Rosmaster teleoperators now support torque enable/disable functionality with automatic position syncing through keyboard inputs. This allows you to:
- **Enable torque**: Motors will resist movement and hold their positions (normal operation)
- **Disable torque**: Motors can be moved freely by hand for manual positioning
- **Position syncing**: When torque is disabled, teleoperator automatically tracks robot's actual positions
- **No snap-back**: When torque is re-enabled, robot holds current positions (no jumping back to old values!)

## Available Teleoperators with Torque Control

### 1. Enhanced Teleoperator (`rosmaster_enhanced`)
A new dedicated teleoperator with torque control.

### 2. Updated Keyboard Teleoperator (`rosmaster_keyboard`) 
The existing keyboard teleoperator now includes torque control.

## Key Mappings

### Joint Control
- `q/a`: Joint 1 (+/-)
- `w/s`: Joint 2 (+/-)  
- `e/d`: Joint 3 (+/-)
- `r/f`: Joint 4 (+/-)
- `t/g`: Joint 5 (+/-)
- `y/h`: Joint 6 (+/-)

### **NEW: Torque Control** 🔥
- `z`: **Enable torque** (motors resist movement - normal operation)
- `x`: **Disable torque** (motors can be moved freely by hand)

### Other Controls
- `SPACE`: Lock/Unlock position control (SAFETY FEATURE)
- `ESC`: Disconnect

## Usage Examples

### Using the Enhanced Teleoperator
```bash
# Method 1: Direct command
PYTHONPATH=/home/jetson/lerobot/src lerobot-teleoperate \
    --robot.type=rosmaster \
    --robot.com=/dev/myserial \
    --robot.id=rosmaster \
    --teleop.type=rosmaster_enhanced \
    --teleop.mock=false

# Method 2: Using the provided script
./run_enhanced_teleop.sh
```

### Using the Updated Keyboard Teleoperator
```bash
PYTHONPATH=/home/jetson/lerobot/src lerobot-teleoperate \
    --robot.type=rosmaster \
    --robot.com=/dev/myserial \
    --robot.id=rosmaster \
    --teleop.type=rosmaster_keyboard \
    --teleop.mock=false
```

## Typical Workflow

1. **Start teleoperation** with either teleoperator
2. **Position control starts LOCKED** for safety
3. Press `SPACE` to **unlock position control**
4. Use joint keys (`q/a`, `w/s`, etc.) to move the robot
5. Press `x` to **disable torque** when you want to manually position the robot
6. **Move the robot manually** - positions sync automatically in real-time
7. Press `z` to **re-enable torque** - robot holds current positions (no snap-back!)
8. Continue with normal teleoperation
9. Press `ESC` to **disconnect** when done

## Safety Notes

⚠️ **Important Safety Information:**
- Position control starts **LOCKED** by default - press `SPACE` to unlock
- When torque is **disabled** (`x` key), you can move the robot manually
- When torque is **enabled** (`z` key), motors will resist manual movement
- Always be careful when switching between modes
- Use the `SPACE` key to lock controls if needed

## Troubleshooting

### If torque commands don't work:
1. Make sure you're using a compatible robot (`rosmaster` type)
2. Verify the robot is properly connected (`/dev/myserial`)
3. Check that the motor bus supports torque control

### If keys don't respond:
1. Make sure the terminal window has focus
2. Verify `pynput` is installed: `pip install pynput`
3. Try pressing `SPACE` to unlock position control

## Technical Details

The enhanced torque control with position syncing works by:

### Torque Control:
1. Teleoperator detects `z` or `x` key presses
2. Adds `torque_enable` or `torque_disable` flags to the action dictionary
3. Robot processes these flags and calls `enable_torque()` or `disable_torque()` on the motor bus
4. Yahboom driver sends appropriate torque commands to the servos

### Position Syncing:
1. Teleoperation loop continuously reads robot's actual positions via `get_observation()`
2. These positions are sent back to teleoperator via `send_feedback()`
3. When torque is disabled, teleoperator updates its internal positions to match robot
4. When torque is re-enabled, teleoperator commands the current (synced) positions
5. Result: No snap-back behavior!

This provides real-time torque control with seamless position synchronization integrated into the existing teleoperation workflow.
