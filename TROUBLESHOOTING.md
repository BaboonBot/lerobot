# Rosmaster Recording Troubleshooting & FAQ

## Frequently Asked Questions

### Q: Why do I see "Failed to read angle for motor" warnings?
**A:** This is a common hardware communication issue with the Rosmaster controller. The warnings don't prevent recording - the system gracefully handles these errors by using fallback values. The recording will continue normally and produce valid datasets.

### Q: What's the difference between custom recording and native LeRobot recording?
**A:** 
- **Custom recording script** (`record_rosmaster_data.py`): Simple NumPy-based format, good for basic data collection
- **Native LeRobot recording** (`lerobot-record`): Full LeRobot dataset format with parquet files and MP4 videos, compatible with LeRobot training pipeline

### Q: Can I record without cameras?
**A:** Yes! Use an empty camera configuration:
```bash
--robot.cameras="{}"
```
Or create a no-camera config file with `cameras: {}`.

### Q: Can I upload my datasets to share with others?
**A:** Yes! Use the Hugging Face Hub integration:
```bash
# Setup (one-time)
huggingface-cli login

# Record with automatic upload
lerobot-record \
  --dataset.push_to_hub=true \
  --dataset.repo_id="username/dataset_name" \
  --dataset.private=false \
  ...
```

### Q: How do I make my dataset private?
**A:** Set the private flag during recording:
```bash
--dataset.private=true
```
Or change visibility later:
```bash
huggingface-cli repo visibility username/dataset_name private
```

### Q: How do I add a second camera?
**A:** Include both cameras in the configuration (✅ **Verified Working**):
```bash
--robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}}"
```
**Test Results**: Successfully tested on August 27, 2025 - both cameras record simultaneously to separate MP4 files in the dataset.

### Q: What if my robot is on a different USB port?
**A:** Change the `--robot.com` parameter:
```bash
--robot.com="/dev/ttyUSB1"  # or ttyUSB2, etc.
```

### Q: How do I view the recorded videos?
**A:** Videos are saved as MP4 files in the dataset:
```bash
vlc data/recordings/videos/chunk-000/observation.images.front/episode_000000.mp4
```

### Q: How do I load a dataset from Hugging Face?
**A:** Use the dataset repository ID:
```python
from lerobot.datasets import LeRobotDataset
dataset = LeRobotDataset("username/dataset_name")
```

## Common Error Messages

### "Permission denied" on /dev/ttyUSB0
**Cause:** User doesn't have permission to access serial port
**Solution:**
```bash
sudo usermod -a -G dialout $USER
# Log out and back in, or:
sudo chmod 666 /dev/ttyUSB0
```

### "Camera not found" or camera errors
**Cause:** Camera not available or in use by another process
**Solutions:**
```bash
# Check available cameras
lerobot-find-cameras opencv

# Check if camera is in use
lsof /dev/video0

# Test camera manually
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### "Object of type type is not JSON serializable"
**Cause:** Feature definitions format issue (already fixed in our implementation)
**Solution:** This was resolved by updating the feature definitions in the robot implementation.

### "AttributeError: 'NoneType' object has no attribute 'items'"
**Cause:** Trying to set cameras to `null` instead of empty dict
**Solution:** Use `--robot.cameras="{}"` instead of `--robot.cameras=null`

### "unrecognized arguments: --robot.config_path"
**Cause:** Config path should be top-level argument
**Solution:** Use `--config_path` instead of `--robot.config_path`

### Hugging Face Authentication Errors
**Cause:** Not logged in or invalid token
**Solutions:**
```bash
# Login interactively
huggingface-cli login

# Check login status
huggingface-cli whoami

# Use environment variable
export HUGGINGFACE_HUB_TOKEN="your_token_here"
```

### "Repository not found" on Hub
**Cause:** Repository doesn't exist or access denied
**Solutions:**
```bash
# Create repository first
huggingface-cli create-repo username/dataset_name --type dataset

# Check repository exists
huggingface-cli repo info username/dataset_name
```

### Upload timeout or connection errors
**Cause:** Large dataset or network issues
**Solutions:**
```bash
# Upload in chunks for large datasets
# Reduce episode length or file sizes
# Check internet connection stability
# Try upload during off-peak hours
```

## Hardware Issues

### Robot Not Responding
1. **Check physical connections**
   - USB cable properly connected
   - Robot powered on
   - Green/blue LED indicators active

2. **Check software connections**
   ```bash
   ls -la /dev/ttyUSB*
   lsof /dev/ttyUSB0
   ```

3. **Try different USB ports**
   - Some USB ports may have power issues
   - USB 3.0 vs 2.0 compatibility

### Camera Issues
1. **Camera not detected**
   ```bash
   # Check video devices
   ls -la /dev/video*
   
   # Test with system tools
   cheese  # GNOME camera app
   ```

2. **Poor video quality**
   - Check lighting conditions
   - Adjust camera position
   - Try different resolution settings

3. **Camera lag or stuttering**
   - Reduce FPS: `--dataset.fps=5`
   - Lower resolution
   - Close other applications

4. **Dual-camera performance issues**
   - **Verified Setup**: `/dev/video0` and `/dev/video2` work simultaneously
   - **Performance Impact**: Dual cameras increase CPU/storage usage
   - **Optimization**: Use same resolution/FPS for both cameras
   - **Bandwidth**: USB bandwidth may limit simultaneous high-FPS recording

## Performance Optimization

### High CPU Usage
- Reduce recording FPS
- Lower camera resolution
- Close unnecessary applications
- Use hardware acceleration if available

### Storage Issues
- Monitor disk space during recording
- Use faster storage (SSD)
- Compress old recordings
- Clean up test data regularly

### Memory Issues
- Reduce episode length
- Lower recording FPS
- Close browser and other applications
- Add swap space if needed

## Network and Connectivity

### SSH Recording Sessions
When recording over SSH:
```bash
# Use screen or tmux for persistent sessions
screen -S recording
# or
tmux new -s recording

# Run recording command
lerobot-record ...

# Detach: Ctrl+A, D (screen) or Ctrl+B, D (tmux)
```

### Remote Display
For GUI applications over SSH:
```bash
ssh -X user@jetson
# or
ssh -Y user@jetson
```

## Data Validation

### Check Recording Success
```bash
# List recorded files
ls -la data/recordings/

# Check video files
ls -la data/recordings/videos/chunk-000/

# Verify file sizes (should not be 0 bytes)
du -h data/recordings/videos/chunk-000/observation.images.front/
```

### Validate Data Quality
```python
# Quick data check
from lerobot.datasets import LeRobotDataset
dataset = LeRobotDataset("data/recordings")
print(f"Episodes: {dataset.num_episodes}")
print(f"Duration: {len(dataset)} frames")

# Check episode
episode = dataset[0]
print("Keys:", episode.keys())
```

## Advanced Troubleshooting

### Debug Mode
Add verbose logging to commands:
```bash
# Set debug environment
export LEROBOT_DEBUG=1

# Run with Python debugging
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Your recording code here
"
```

### Hardware Communication Debug
```python
# Test robot communication directly
from lerobot.robots.rosmaster import RosmasterRobot

robot = RosmasterRobot("/dev/ttyUSB0", "test")
robot.connect()
print("Connected:", robot.is_connected)
robot.disconnect()
```

### Camera Debug
```python
# Test camera directly
import cv2
cap = cv2.VideoCapture(0)
print("Camera opened:", cap.isOpened())
ret, frame = cap.read()
print("Frame captured:", ret, frame.shape if ret else "Failed")
cap.release()
```

## System Requirements

### Minimum Specifications
- **CPU**: ARM Cortex-A57 quad-core (Jetson Nano) or equivalent
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 32GB minimum, SSD recommended
- **USB**: USB 2.0 ports for robot and cameras

### Recommended Specifications
- **CPU**: Higher-end ARM or x86_64
- **RAM**: 8GB or more
- **Storage**: Fast SSD with 100GB+ free space
- **USB**: USB 3.0 ports for better camera performance

## Recovery Procedures

### Stuck Recording Session
```bash
# Find and kill process
ps aux | grep lerobot-record
kill -9 <PID>

# Or force kill all python processes (be careful!)
pkill -f lerobot-record
```

### Corrupted Dataset
```bash
# Remove corrupted data
rm -rf data/recordings/corrupted_dataset/

# Start fresh recording
lerobot-record ...
```

### Reset Robot Connection
```bash
# Disconnect and reconnect USB
# Or restart the robot power
# Or reset USB permissions
sudo chmod 666 /dev/ttyUSB0
```

## Contact and Support

For additional help:
1. Check the main `RECORDING_GUIDE.md` for detailed procedures
2. Review the `QUICK_REFERENCE.md` for common commands
3. Check LeRobot documentation and GitHub issues
4. Verify hardware connections and power

Remember: The "Failed to read angle" warnings are normal and don't prevent successful recording!
