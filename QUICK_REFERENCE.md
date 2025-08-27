# Rosmaster Recording Quick Reference

## Essential Commands

### Setup Hugging Face (One-time)
```bash
pip install huggingface_hub
huggingface-cli login
```

### Camera Detection
```bash
lerobot-find-cameras opencv
ls -la /dev/video*
```

### Test Teleoperation
```bash
lerobot-teleoperate \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="test_robot" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --display_data=true
```

### Record Data (Single Camera)
```bash
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="my_rosmaster_robot" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --dataset.repo_id="local_user/my_task" \
  --dataset.single_task="Task description" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=10 \
  --dataset.reset_time_s=3 \
  --dataset.fps=10 \
  --dataset.push_to_hub=false \
  --dataset.root="data/recordings" \
  --display_data=true
```

### Record with Hugging Face Upload
```bash
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="my_rosmaster_robot" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --dataset.repo_id="username/my_dataset" \
  --dataset.single_task="Task description" \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=15 \
  --dataset.reset_time_s=5 \
  --dataset.fps=10 \
  --dataset.push_to_hub=true \
  --dataset.private=false \
  --dataset.tags="robotics,rosmaster,imitation-learning" \
  --dataset.root="data/recordings" \
  --display_data=true
```

### Record Data (Dual Camera) - VERIFIED WORKING ✅
```bash
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="my_rosmaster_robot" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --dataset.repo_id="local_user/my_task" \
  --dataset.single_task="Task description" \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=15 \
  --dataset.reset_time_s=5 \
  --dataset.fps=10 \
  --dataset.push_to_hub=false \
  --dataset.root="data/recordings" \
  --display_data=true
```

## Keyboard Controls
- `q/a`: Joint 1 (+/-)  
- `w/s`: Joint 2 (+/-)
- `e/d`: Joint 3 (+/-)
- `r/f`: Joint 4 (+/-)
- `t/g`: Joint 5 (+/-)
- `y/h`: Joint 6 (+/-)
- `SPACE`: Lock/Unlock
- `ESC`: Disconnect

## Common Parameters
- `--dataset.fps=10`: Recording frame rate
- `--dataset.episode_time_s=15`: Episode duration
- `--dataset.num_episodes=5`: Number of episodes
- `--teleop.joint_step=2.0`: Movement step size (degrees)
- `--dataset.push_to_hub=true`: Upload to Hugging Face
- `--dataset.private=false`: Make dataset public
- `--dataset.tags="tag1,tag2"`: Add searchable tags

## Hugging Face Commands
```bash
# Login to Hugging Face
huggingface-cli login

# Upload existing dataset
huggingface-cli upload-folder \
  --repo-id="username/dataset_name" \
  --folder-path="data/recordings" \
  --repo-type="dataset"

# Make dataset private/public
huggingface-cli repo visibility username/dataset_name private
huggingface-cli repo visibility username/dataset_name public
```

## Troubleshooting
```bash
# Check robot connection
ls -la /dev/ttyUSB0
lsof /dev/ttyUSB0

# Check camera connection  
ls -la /dev/video*
lsof /dev/video0

# Fix permissions
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0
```

## File Locations
- Config: `configs/robot/rosmaster.yaml`
- Recordings: `data/recordings/`
- Videos: `data/recordings/videos/chunk-000/`
- Custom script: `record_rosmaster_data.py`
