# Rosmaster Robot Recording Guide

This guide documents all the processes for recording data with the Rosmaster robot using both custom recording scripts and the native LeRobot recording system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Camera Setup](#camera-setup)
3. [Robot Configuration](#robot-configuration)
4. [Custom Recording Script](#custom-recording-script)
5. [Native LeRobot Recording](#native-lerobot-recording)
6. [Publishing to Hugging Face Hub](#publishing-to-hugging-face-hub)
7. [Troubleshooting](#troubleshooting)
8. [Data Analysis](#data-analysis)

## Prerequisites

### Hardware Requirements
- Yahboom Rosmaster robot arm (6-DOF)
- USB-to-serial adapter connected to `/dev/ttyUSB0`
- OpenCV compatible cameras (USB or built-in)
- Jetson Nano or compatible Linux system

### Software Requirements
- Python 3.10+
- LeRobot framework installed
- Required Python packages:
  ```bash
  pip install opencv-python numpy matplotlib tqdm
  ```

### Environment Setup
1. Ensure robot is connected via USB serial port
2. Verify camera devices are available
3. Check user permissions for device access

## Camera Setup

### 1. Detect Available Cameras
```bash
# Find available OpenCV cameras
lerobot-find-cameras opencv

# Check video devices manually
ls -la /dev/video*
```

### 2. Test Camera Functionality
```bash
# Test camera with v4l2
v4l2-ctl --list-devices

# Quick camera test with OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera working:', cap.isOpened()); cap.release()"
```

### 3. Camera Configuration
Available cameras on typical setup:
- `/dev/video0` - Front/primary camera (640x480, 30fps)
- `/dev/video2` - Secondary camera (if available)

## Robot Configuration

### 1. Basic Robot Config (`configs/robot/rosmaster.yaml`)
```yaml
# Configuration for Rosmaster Robot
type: rosmaster
id: rosmaster_1

# Serial port configuration
com: "/dev/ttyUSB0"

# Camera configuration
cameras:
  front:
    type: opencv
    index_or_path: "/dev/video0"
    fps: 30
    width: 640
    height: 480
    color_mode: rgb
    rotation: 0
  wrist:  # Optional second camera
    type: opencv  
    index_or_path: "/dev/video2"
    fps: 30
    width: 640
    height: 480
    color_mode: rgb
    rotation: 0
```

### 2. No-Camera Config (`configs/robot/rosmaster_no_cameras.yaml`)
```yaml
# Configuration for Rosmaster Robot without cameras
type: rosmaster
id: rosmaster_1
com: "/dev/ttyUSB0"
cameras: {}  # Empty cameras for testing
```

## Custom Recording Script

### 1. Script Location
File: `record_rosmaster_data.py`

### 2. Usage
```bash
# Basic recording with default settings
python3 record_rosmaster_data.py

# Custom recording with specific parameters
python3 record_rosmaster_data.py --episodes 5 --duration 30 --fps 20
```

### 3. Script Features
- **Episode-based recording**: Records data in discrete episodes
- **Camera integration**: Captures images from connected cameras
- **Joint position logging**: Records robot joint states
- **Action logging**: Captures keyboard teleop commands
- **Automatic data saving**: Saves to NumPy format with metadata
- **Real-time visualization**: Optional data display during recording

### 4. Output Structure
```
data/
├── episode_000.npz         # Episode data
├── episode_000_metadata.json  # Episode metadata
├── episode_001.npz
├── episode_001_metadata.json
└── ...
```

### 5. Data Format
Each `.npz` file contains:
- `observations`: Joint positions and camera images
- `actions`: Teleop commands
- `timestamps`: Time information
- `episode_info`: Episode metadata

## Native LeRobot Recording

### 1. Command Structure
```bash
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="my_rosmaster_robot" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --dataset.repo_id="local_user/rosmaster_recording" \
  --dataset.single_task="Task description" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=10 \
  --dataset.reset_time_s=3 \
  --dataset.fps=10 \
  --dataset.push_to_hub=false \
  --dataset.root="data/lerobot_recordings" \
  --display_data=true
```

### 2. Parameter Breakdown

#### Robot Parameters
- `--robot.type=rosmaster`: Specifies robot type
- `--robot.com="/dev/ttyUSB0"`: Serial port for robot communication
- `--robot.id="my_rosmaster_robot"`: Unique robot identifier
- `--robot.cameras="{...}"`: Camera configuration in JSON format

#### Teleop Parameters
- `--teleop.type=rosmaster_keyboard`: Keyboard teleoperation
- `--teleop.joint_step=2.0`: Step size for joint movements (degrees)

#### Dataset Parameters
- `--dataset.repo_id="local_user/dataset_name"`: Dataset identifier
- `--dataset.single_task="description"`: Task description
- `--dataset.num_episodes=N`: Number of episodes to record
- `--dataset.episode_time_s=N`: Duration of each episode (seconds)
- `--dataset.reset_time_s=N`: Reset time between episodes (seconds)
- `--dataset.fps=N`: Recording frame rate
- `--dataset.push_to_hub=false`: Don't upload to HuggingFace Hub
- `--dataset.root="path"`: Local storage directory

#### Display Parameters
- `--display_data=true`: Show real-time data during recording

### 3. Camera Configuration Formats

#### Single Camera
```bash
--robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}"
```

#### Multiple Cameras
```bash
--robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}}"
```

**✅ Verified Working**: Dual-camera recording has been successfully tested and confirmed working on Jetson Nano with Rosmaster robot. Both camera feeds are captured simultaneously and encoded to separate MP4 files.

#### Using Config File
```bash
--config_path="/path/to/rosmaster.yaml"
```

### 4. Keyboard Controls During Recording
- `q/a`: Joint 1 (+/-)
- `w/s`: Joint 2 (+/-)
- `e/d`: Joint 3 (+/-)
- `r/f`: Joint 4 (+/-)
- `t/g`: Joint 5 (+/-)
- `y/h`: Joint 6 (+/-)
- `SPACE`: Lock/Unlock position (safety feature)
- `ESC`: Disconnect and stop recording

### 5. Output Structure
```
data/lerobot_recordings/
├── data/
│   └── chunk-000/
│       └── train-00000-of-00001.parquet  # Tabular data
├── meta/
│   ├── info.json                         # Dataset metadata
│   └── stats.safetensors                 # Dataset statistics
└── videos/
    └── chunk-000/
        └── observation.images.front/
            └── episode_000000.mp4       # Video data
```

### 6. Data Format
The native LeRobot format includes:
- **Parquet files**: Structured data (joint positions, actions, timestamps)
- **MP4 videos**: Camera feeds with proper synchronization
- **Metadata**: Dataset information and statistics
- **HuggingFace compatibility**: Ready for model training

## Publishing to Hugging Face Hub

### 1. Setup Hugging Face Authentication

#### Install Hugging Face CLI (if not already installed)
```bash
pip install huggingface_hub
```

#### Login to Hugging Face
```bash
# Interactive login
huggingface-cli login

# Or using token directly
huggingface-cli login --token YOUR_HF_TOKEN

# Alternative: set environment variable
export HUGGINGFACE_HUB_TOKEN="your_token_here"
```

#### Get your token from:
1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "Write" permissions
3. Copy the token for authentication

### 2. Recording with Automatic Upload

#### Enable Hub Upload During Recording
```bash
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="my_rosmaster_robot" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --dataset.repo_id="username/rosmaster_dataset" \
  --dataset.single_task="Pick and place demonstration" \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=15 \
  --dataset.reset_time_s=5 \
  --dataset.fps=10 \
  --dataset.push_to_hub=true \
  --dataset.private=false \
  --dataset.tags="robotics,imitation-learning,rosmaster" \
  --dataset.root="data/recordings" \
  --display_data=true
```

#### Key Parameters for Hub Upload
- `--dataset.push_to_hub=true`: Enable automatic upload
- `--dataset.repo_id="username/dataset_name"`: Your HF username and dataset name
- `--dataset.private=false`: Make dataset public (use `true` for private)
- `--dataset.tags="tag1,tag2,tag3"`: Add searchable tags

### 3. Manual Upload of Existing Datasets

#### Upload Local Dataset to Hub
```bash
# Using huggingface-cli
huggingface-cli upload-folder \
  --repo-id="username/my_dataset" \
  --folder-path="data/recordings" \
  --repo-type="dataset" \
  --create-pr=false
```

#### Upload with Python Script
```python
from huggingface_hub import HfApi, create_repo
from lerobot.datasets import LeRobotDataset

# Load your local dataset
dataset = LeRobotDataset("data/recordings")

# Create repository on Hub (if doesn't exist)
api = HfApi()
repo_id = "username/my_rosmaster_dataset"

try:
    create_repo(
        repo_id=repo_id,
        repo_type="dataset",
        private=False,  # Set to True for private datasets
        exist_ok=True
    )
    print(f"Repository {repo_id} ready")
except Exception as e:
    print(f"Repository creation: {e}")

# Upload dataset
dataset.push_to_hub(
    repo_id=repo_id,
    private=False,
    tags=["robotics", "imitation-learning", "rosmaster", "6dof-arm"]
)
```

### 4. Dataset Naming Conventions

#### Recommended Naming Format
```
username/robot_task_description
```

#### Examples:
- `myuser/rosmaster_pick_place` - Pick and place tasks
- `myuser/rosmaster_stacking` - Object stacking demonstrations  
- `myuser/rosmaster_assembly` - Assembly task recordings
- `lab_name/rosmaster_manipulation_v1` - Lab dataset with version

#### Dataset Repository Structure on Hub
```
your_dataset/
├── README.md                    # Auto-generated dataset card
├── data/
│   └── chunk-000/
│       └── train-*.parquet     # Data files
├── videos/
│   └── chunk-000/
│       └── observation.*.mp4   # Video files
└── meta/
    ├── info.json              # Dataset metadata
    └── stats.safetensors      # Statistics
```

### 5. Dataset Metadata and Documentation

#### Automatic Dataset Card Generation
When uploading, LeRobot automatically creates a README.md with:
- Dataset description
- Task information
- Recording details
- Usage examples
- Citation information

#### Custom Dataset Card Template
```yaml
---
license: apache-2.0
tags:
- robotics
- imitation-learning
- rosmaster
- 6dof-arm
task_categories:
- robotics
language:
- en
size_categories:
- 1K<n<10K
---

# Rosmaster Robot Dataset

## Dataset Description
This dataset contains demonstrations of a 6-DOF Rosmaster robot arm performing [describe your task].

## Task Information
- **Robot**: Yahboom Rosmaster 6-DOF arm
- **Task**: [Your specific task]
- **Environment**: [Describe setup]
- **Episodes**: [Number] episodes
- **Duration**: [Total time]

## Recording Setup
- **Cameras**: Front camera (640x480, 30fps)
- **Control**: Keyboard teleoperation
- **Framework**: LeRobot
- **Recording FPS**: 10

## Usage
```python
from lerobot.datasets import LeRobotDataset
dataset = LeRobotDataset("username/dataset_name")
```

## Citation
If you use this dataset, please cite:
[Your citation information]
```

### 6. Dataset Versioning and Updates

#### Version Control with Git
```bash
# Clone your dataset repository
git clone https://huggingface.co/datasets/username/my_dataset
cd my_dataset

# Add new episodes
# ... record more data locally ...

# Upload updates
huggingface-cli upload-folder \
  --repo-id="username/my_dataset" \
  --folder-path="new_episodes/" \
  --repo-type="dataset"

# Or commit changes
git add .
git commit -m "Add 10 new episodes of improved demonstrations"
git push
```

#### Creating Dataset Versions
```bash
# Tag a specific version
git tag v1.0
git push origin v1.0

# Reference specific versions
# users can then load: dataset@v1.0
```

### 7. Privacy and Access Control

#### Private Datasets
```bash
# Record with private upload
lerobot-record \
  ... \
  --dataset.push_to_hub=true \
  --dataset.private=true \
  ...

# Or make existing dataset private
huggingface-cli repo visibility username/dataset_name private
```

#### Organization Datasets
```bash
# Upload to organization
--dataset.repo_id="organization_name/dataset_name"
```

#### Access Tokens for Private Datasets
```python
from lerobot.datasets import LeRobotDataset

# Load private dataset with token
dataset = LeRobotDataset(
    "username/private_dataset",
    use_auth_token="your_token_here"
)
```

### 8. Dataset Quality and Standards

#### Pre-Upload Checklist
- [ ] **Data Quality**: Review episodes for quality
- [ ] **Metadata**: Complete task descriptions
- [ ] **File Organization**: Proper directory structure
- [ ] **Documentation**: Clear README and usage examples
- [ ] **Tags**: Relevant and searchable tags
- [ ] **License**: Appropriate license selection

#### Quality Guidelines
```python
# Validate dataset before upload
from lerobot.datasets import LeRobotDataset

dataset = LeRobotDataset("data/recordings")

# Check basic stats
print(f"Episodes: {dataset.num_episodes}")
print(f"Total frames: {len(dataset)}")
print(f"Episode lengths: {[len(ep) for ep in dataset.episode_indices]}")

# Verify data completeness
sample = dataset[0]
print("Data keys:", sample.keys())
print("Image shape:", sample['observation.images.front'].shape)
```

### 9. Collaborative Datasets

#### Multi-User Contributions
```bash
# Organization workflow
# 1. Create organization dataset
huggingface-cli create-repo \
  --organization="lab_name" \
  --repo-type="dataset" \
  rosmaster_collaborative

# 2. Each user contributes episodes
lerobot-record \
  --dataset.repo_id="lab_name/rosmaster_collaborative" \
  --dataset.push_to_hub=true \
  ...

# 3. Merge and organize contributions
```

#### Dataset Splits and Subsets
```python
# Create train/validation splits
from lerobot.datasets import LeRobotDataset

# Load full dataset
full_dataset = LeRobotDataset("username/full_dataset")

# Create subsets
train_episodes = list(range(0, 80))  # First 80 episodes
val_episodes = list(range(80, 100))  # Last 20 episodes

# Upload subsets
train_dataset = full_dataset.select_episodes(train_episodes)
train_dataset.push_to_hub("username/dataset_train")

val_dataset = full_dataset.select_episodes(val_episodes)
val_dataset.push_to_hub("username/dataset_val")
```

### 10. Dataset Discovery and Sharing

#### Finding Existing Datasets
```python
from huggingface_hub import list_datasets

# Search for robotics datasets
datasets = list_datasets(
    filter="robotics",
    sort="downloads"
)

# Search for LeRobot datasets
lerobot_datasets = list_datasets(
    author="lerobot-community",
    sort="trending"
)
```

#### Community Guidelines
- **Descriptive Names**: Use clear, descriptive dataset names
- **Rich Metadata**: Include comprehensive task descriptions
- **Quality Data**: Ensure demonstrations are of good quality
- **Documentation**: Provide clear usage instructions
- **Licensing**: Use appropriate open licenses when possible

### 11. Example Complete Workflow

#### Recording and Publishing Pipeline
```bash
# 1. Authenticate with Hugging Face
huggingface-cli login

# 2. Record dataset with automatic upload
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="lab_rosmaster_01" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --dataset.repo_id="mylab/rosmaster_pick_place_v1" \
  --dataset.single_task="Pick objects from table and place in target locations" \
  --dataset.num_episodes=50 \
  --dataset.episode_time_s=20 \
  --dataset.reset_time_s=5 \
  --dataset.fps=10 \
  --dataset.push_to_hub=true \
  --dataset.private=false \
  --dataset.tags="robotics,imitation-learning,manipulation,rosmaster,pick-place" \
  --dataset.root="data/pick_place_recordings" \
  --display_data=true

# 3. Verify upload
echo "Dataset available at: https://huggingface.co/datasets/mylab/rosmaster_pick_place_v1"

# 4. Test loading from Hub
python3 -c "
from lerobot.datasets import LeRobotDataset
dataset = LeRobotDataset('mylab/rosmaster_pick_place_v1')
print(f'Successfully loaded {dataset.num_episodes} episodes')
"
```

This completes the comprehensive guide for publishing LeRobot datasets to Hugging Face Hub, enabling easy sharing and collaboration in the robotics community.

## Troubleshooting

### Common Issues

#### 1. Camera Not Found
```bash
# Check available cameras
ls -la /dev/video*
lerobot-find-cameras opencv

# Test camera access
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

#### 2. Serial Port Permission Denied
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and back in

# Or change permissions temporarily
sudo chmod 666 /dev/ttyUSB0
```

#### 3. Robot Communication Errors
- Check physical connections
- Verify robot is powered on
- Try different USB ports
- Check for conflicting processes:
  ```bash
  lsof /dev/ttyUSB0
  ```

#### 4. Position Reading Warnings
The warnings like "Failed to read angle for motor" are common and don't prevent recording:
- Robot hardware communication issues
- System gracefully handles fallbacks
- Recording continues with default/last-known positions

#### 5. Camera Connection Issues
```bash
# Check camera is not in use
lsof /dev/video0

# Test with different applications
cheese  # GNOME camera app
```

### Performance Optimization

#### 1. Reduce CPU Load
- Lower recording FPS: `--dataset.fps=5`
- Reduce camera resolution
- Close unnecessary applications

#### 2. Storage Optimization
- Use faster storage for recording
- Monitor disk space during long recordings
- Compress older recordings

## Data Analysis

### 1. Viewing Recorded Data

#### Custom Script Data
```python
import numpy as np
import json

# Load episode data
data = np.load('data/episode_000.npz')
with open('data/episode_000_metadata.json', 'r') as f:
    metadata = json.load(f)

print("Episode info:", metadata)
print("Data keys:", list(data.keys()))
print("Observations shape:", data['observations'].shape)
```

#### Native LeRobot Data
```python
from lerobot.datasets import LeRobotDataset

# Load dataset
dataset = LeRobotDataset("data/lerobot_recordings")
print("Dataset info:", dataset.info)
print("Number of episodes:", dataset.num_episodes)

# Access episode data
episode = dataset[0]
print("Episode keys:", episode.keys())
```

### 2. Data Visualization

#### View Recorded Videos
```bash
# Play recorded video
vlc data/lerobot_recordings/videos/chunk-000/observation.images.front/episode_000000.mp4
```

#### Plot Joint Trajectories
Use the provided visualization scripts to analyze joint movements and camera data.

## Best Practices

### 1. Recording Sessions
- Start with short episodes (5-10 seconds) for testing
- Gradually increase episode length for real tasks
- Record multiple demonstrations of the same task
- Include diverse scenarios and edge cases

### 2. Data Quality
- Ensure good lighting for cameras
- Minimize background motion
- Perform smooth, deliberate movements
- Include both successful and failed attempts

### 3. Storage Management
- Regularly backup important recordings
- Clean up test recordings to save space
- Use descriptive dataset names and task descriptions
- Document recording conditions and setup

### 4. Safety
- Use position lock (SPACE key) when not actively demonstrating
- Keep reset/emergency stop procedures ready
- Monitor robot for unusual behavior
- Ensure clear workspace around robot

## Example Recording Session

### Complete Workflow
```bash
# 1. Check system status
lerobot-find-cameras opencv
ls -la /dev/ttyUSB0

# 2. Test teleoperation first
lerobot-teleoperate \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="test_robot" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --display_data=true

# 3. Record actual data
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="my_rosmaster_robot" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --dataset.repo_id="local_user/pick_and_place" \
  --dataset.single_task="Pick up object and place in target location" \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=15 \
  --dataset.reset_time_s=5 \
  --dataset.fps=10 \
  --dataset.push_to_hub=false \
  --dataset.root="data/pick_and_place_demo" \
  --display_data=true

# 4. Verify recorded data
ls -la data/pick_and_place_demo/
```

### Dual-Camera Recording (Verified Working)
```bash
# Record with both front and wrist cameras simultaneously
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="dual_camera_rosmaster" \
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}}" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --dataset.repo_id="local_user/dual_camera_demo" \
  --dataset.single_task="Dual camera recording demonstration with front and wrist views" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=15 \
  --dataset.reset_time_s=5 \
  --dataset.fps=10 \
  --dataset.push_to_hub=false \
  --dataset.root="data/dual_camera_recordings" \
  --display_data=true

# Expected output structure:
# data/dual_camera_recordings/
# ├── data/chunk-000/episode_000000.parquet
# ├── videos/chunk-000/
# │   ├── observation.images.front/episode_000000.mp4
# │   └── observation.images.wrist/episode_000000.mp4
# └── meta/info.json
```

**✅ Test Results (August 27, 2025):**
- Both cameras (`/dev/video0` and `/dev/video2`) connected successfully
- Simultaneous recording of 15-second episode completed
- 149 frames captured at 10 FPS with dual camera feeds
- Both video streams encoded successfully to MP4 format
- Keyboard teleoperation working throughout recording session
- Dataset created in proper LeRobot format with dual video streams
