# Rosmaster Robot - Quick Guide

Simple guide for teleoperation and recording with the Rosmaster robot.

## 🚀 Essential Commands

### 1. Teleoperate the Robot
```bash
lerobot-teleoperate \
  --robot.type=rosmaster \
  --robot.com="/dev/myserial" \
  --robot.cameras="{wrist: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}, front: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_combined \
  --teleop.joint_step=2.0 \
  --teleop.movement_step=0.3 \
  --teleop.rotation_step=0.5 \
  --display_data=true
```

### 2. Record Dataset
```bash
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/myserial" \
  --robot.cameras="{wrist: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}, front: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_combined \
  --teleop.joint_step=2.0 \
  --teleop.movement_step=0.3 \
  --teleop.rotation_step=0.5 \
  --dataset.repo_id="local_user/my_recording" \
  --dataset.single_task="Pick and place" \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=15 \
  --dataset.fps=10 \
  --dataset.root="data/recordings" \
  --display_data=true
```

## 🎮 Keyboard Controls

### Movement (Mecanum Wheels)
- `W/S` - Forward/Backward
- `A/D` - Strafe Left/Right  
- `Q/E` - Rotate Left/Right

### Arm Joints
- `T/G` - Joint 1 (Base rotation)
- `Y/H` - Joint 2 (Shoulder)
- `U/J` - Joint 3 (Elbow)
- `I/K` - Joint 4 (Wrist pitch)
- `O/L` - Joint 5 (Wrist roll)
- `P/;` - Joint 6 (Gripper)

### Safety
- `SPACE` - Lock/Unlock controls
- `ESC` - Disconnect and exit

## 🔧 Quick Setup

### Check Hardware
```bash
# Check robot connection
ls -la /dev/myserial

# Check cameras
ls -la /dev/video*
lerobot-find-cameras opencv
```

### Adjust Settings
- **Change camera paths**: Replace `/dev/video0` and `/dev/video2` with your camera devices
- **Change robot port**: Replace `/dev/myserial` with your robot's serial port
- **Adjust FPS**: Change `fps: 30` to lower values (like `10`) for better performance
- **Adjust resolution**: Change `width` and `height` values as needed

## 📹 Camera Options

### Single Camera
```bash
--robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}"
```

### Dual Cameras (Recommended)
```bash
--robot.cameras="{wrist: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}, front: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}}"
```

### No Cameras
```bash
--robot.cameras="{}"
```

## 📊 Recording Settings

Adjust these parameters in the record command:

```bash
--dataset.repo_id="local_user/my_recording"     # Dataset name
--dataset.single_task="Task description"        # What the robot is doing
--dataset.num_episodes=5                        # How many episodes to record
--dataset.episode_time_s=15                     # Seconds per episode
--dataset.fps=10                                # Frames per second
--dataset.root="data/recordings"                # Where to save data
```

### Upload to Hugging Face (Optional)
```bash
# First login (one-time)
huggingface-cli login

# Then add these to record command:
--dataset.repo_id="your_username/dataset_name"
--dataset.push_to_hub=true
--dataset.private=false
```

## 🚨 Common Issues

### "Failed to read angle" Warnings
- **Normal behavior** - ignore these warnings
- Recording still works correctly

### Camera Not Found
```bash
# List available cameras
ls -la /dev/video*

# Test camera
lerobot-find-cameras opencv
```

### Display Not Working
```bash
# Check/set display environment
echo $DISPLAY
export DISPLAY=:0
```

## 📁 Data Location

Recorded datasets are saved in:
```
data/recordings/local_user/my_recording/
├── data/chunk-000/train-*.parquet        # Robot data
├── videos/chunk-000/observation.*.mp4    # Camera videos
└── meta/info.json                        # Metadata
```

## 💡 Quick Tips

1. **Always test teleoperation first** before recording
2. **Start with short episodes** (10-15 seconds)
3. **Use 10 FPS** for stable recording
4. **Check disk space** before recording
5. **"Failed to read angle" warnings are normal** - keep going!

---

**Ready to go!** Run the teleoperate command first to test, then start recording.
