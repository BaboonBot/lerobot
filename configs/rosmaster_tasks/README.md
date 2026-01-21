# Rosmaster Task-Specific Configurations

This directory contains task-specific JSON configuration files for recording different tasks with the Rosmaster robot.

## How to Use

### Recording with a Task Config

Simply run `lerobot-record` with the `--config` flag:

```bash
lerobot-record --config configs/rosmaster_tasks/reach_cube.json
```

### Key Features

#### Automatic Reset Position

Each task can define a custom `reset_position` for the robot's 6 servos. This array of 6 angles (in degrees) will be automatically applied when resetting between episodes:

```json
"robot": {
  "type": "rosmaster",
  "reset_position": [90, 5, 120, 55, 90, 70]
}
```

When the robot resets between episodes, it will automatically move to this position using `bot.set_uart_servo_angle_array([90, 5, 120, 55, 90, 70])`.

**To disable automatic reset**, set `reset_position` to `null`:
```json
"reset_position": null
```

#### Task-Specific Parameters

Each config can customize:
- **Reset position**: Starting pose for each episode
- **Episode time**: Recording duration per episode
- **Reset time**: Time allowed for manual adjustments after automatic reset
- **Number of episodes**: Total episodes to record
- **Dataset location**: Where to save the data
- **Task description**: Text description for the task

### Creating a New Task Config

1. Copy an existing config file:
   ```bash
   cp configs/rosmaster_tasks/reach_cube.json configs/rosmaster_tasks/my_new_task.json
   ```

2. Edit the new file:
   - Update `dataset.repo_id` to your task name
   - Update `dataset.single_task` description
   - Update `dataset.root` to a new directory
   - **Set your custom `robot.reset_position`** (6 servo angles)
   - Adjust timing parameters as needed

3. Record your new task:
   ```bash
   lerobot-record --config configs/rosmaster_tasks/my_new_task.json
   ```

### Overriding Config Values

You can override any config value from the command line:

```bash
# Record more episodes than configured
lerobot-record --config configs/rosmaster_tasks/reach_cube.json --dataset.num_episodes=100

# Change reset position on the fly
lerobot-record --config configs/rosmaster_tasks/reach_cube.json --robot.reset_position="[45, 10, 90, 60, 45, 80]"

# Disable automatic reset
lerobot-record --config configs/rosmaster_tasks/reach_cube.json --robot.reset_position=null
```

## Example Workflow

### Multi-Task Recording

Record different tasks with different reset positions:

```bash
# Task 1: Reach cube (reset to [90, 5, 120, 55, 90, 70])
lerobot-record --config configs/rosmaster_tasks/reach_cube.json

# Task 2: Navigate (reset to [90, 90, 90, 90, 90, 90])
lerobot-record --config configs/rosmaster_tasks/navigate.json

# Task 3: Pick and place (reset to [90, 20, 100, 60, 90, 50])
lerobot-record --config configs/rosmaster_tasks/pick_place.json
```

Each task will:
1. Start recording
2. Between episodes, automatically reset to the configured position
3. Give you `reset_time_s` seconds to make manual adjustments
4. Continue recording the next episode

## Config File Structure

```json
{
  "robot": {
    "type": "rosmaster",
    "com": "/dev/myserial",
    "cameras": { ... },
    "reset_position": [servo1, servo2, servo3, servo4, servo5, servo6]
  },
  "teleop": {
    "type": "rosmaster_combined"
  },
  "dataset": {
    "repo_id": "username/dataset-name",
    "single_task": "Task description",
    "root": "data/task_recordings",
    "fps": 30,
    "episode_time_s": 30,
    "reset_time_s": 10,
    "num_episodes": 50,
    "video": true,
    "push_to_hub": false
  },
  "display_data": true,
  "play_sounds": true
}
```

## Tips

- **Reset Position**: The 6 values correspond to servos 1-6. Values should be in degrees (typically 0-180).
- **Reset Time**: Give yourself enough time to manually adjust objects in the scene after the robot moves to reset position.
- **Episode Time**: Set based on how long your task typically takes to complete.
- **Version Control**: Keep your config files in git to track different task setups.
