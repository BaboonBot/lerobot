#!/usr/bin/env python3
"""
Data recording script for Rosmaster robot using LeRobot framework.

This script records demonstrations that include:
- Joint positions
- Camera images (if configured)
- Timestamped episodes
- Metadata

Usage:
    python record_rosmaster_data.py --task exploration --episodes 5
    python record_rosmaster_data.py --task pick_and_place --episodes 10 --output-dir my_dataset
"""

import argparse
import sys
import os
import time
from pathlib import Path

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lerobot.robots.rosmaster import RosmasterRobotConfig  
from lerobot.teleoperators.rosmaster_keyboard import RosmasterKeyboardTeleopConfig
from lerobot.robots.utils import make_robot_from_config
from lerobot.teleoperators.utils import make_teleoperator_from_config


def record_episode(robot, teleop, episode_num, max_steps=200, fps=30):
    """Record a single episode of demonstration data."""
    print(f"\n🎬 Recording Episode {episode_num}")
    print("=" * 50)
    print("📋 Instructions:")
    print("  1. Press SPACE to unlock robot movement")
    print("  2. Demonstrate the task using keyboard controls")
    print("  3. Press ESC when episode is complete")
    print("  4. Episode will auto-end after max steps")
    print("\n⏱️  Starting in 3 seconds...")
    
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("🔴 RECORDING STARTED!")
    
    # Storage for episode data
    episode_data = {
        'observations': [],
        'actions': [],
        'timestamps': [],
        'metadata': {
            'episode_num': episode_num,
            'start_time': time.time(),
            'fps': fps,
            'max_steps': max_steps
        }
    }
    
    step_count = 0
    start_time = time.time()
    
    try:
        while step_count < max_steps:
            step_start = time.time()
            
            # Get action from teleoperator
            action = teleop.get_action()
            
            # Send action to robot
            robot.send_action(action)
            
            # Get observation from robot  
            observation = robot.get_observation()
            
            # Store data
            episode_data['observations'].append(observation)
            episode_data['actions'].append(action)
            episode_data['timestamps'].append(time.time() - start_time)
            
            step_count += 1
            
            # Display progress
            if step_count % 30 == 0:  # Every second at 30fps
                elapsed = time.time() - start_time
                print(f"\r📊 Step {step_count:3d}/{max_steps} | Time: {elapsed:.1f}s | Recording...", end="", flush=True)
            
            # Maintain FPS
            step_duration = time.time() - step_start
            sleep_time = (1.0 / fps) - step_duration
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print(f"\n⏹️  Recording stopped by user at step {step_count}")
    except Exception as e:
        if "disconnecting" in str(e).lower():
            print(f"\n✅ Episode completed at step {step_count}")
        else:
            print(f"\n❌ Error during recording: {e}")
            raise
    
    # Finalize episode metadata
    episode_data['metadata']['end_time'] = time.time()
    episode_data['metadata']['duration'] = time.time() - start_time
    episode_data['metadata']['steps_recorded'] = step_count
    
    print(f"\n📈 Episode {episode_num} Summary:")
    print(f"   📏 Steps: {step_count}")
    print(f"   ⏱️  Duration: {episode_data['metadata']['duration']:.1f}s")
    print(f"   🎯 Average FPS: {step_count/episode_data['metadata']['duration']:.1f}")
    
    return episode_data


def save_episode_data(episode_data, output_dir, episode_num):
    """Save episode data to files."""
    episode_dir = output_dir / f"episode_{episode_num:03d}"
    episode_dir.mkdir(parents=True, exist_ok=True)
    
    import numpy as np
    import json
    from PIL import Image
    
    # Save observations and actions as numpy arrays
    observations = episode_data['observations']
    actions = episode_data['actions']
    timestamps = np.array(episode_data['timestamps'])
    
    # Extract joint positions
    joint_positions = np.array([obs['joint_positions'] for obs in observations])
    
    # Save joint data
    np.save(episode_dir / "joint_positions.npy", joint_positions)
    np.save(episode_dir / "timestamps.npy", timestamps)
    
    # Save actions (convert to consistent format)
    action_array = []
    for action in actions:
        # Convert individual joint actions to array format
        action_vec = [action.get(f"servo_{i+1}", 0.0) for i in range(6)]
        action_array.append(action_vec)
    action_array = np.array(action_array)
    np.save(episode_dir / "actions.npy", action_array)
    
    # Save camera images if present
    camera_dirs = {}
    for cam_key in ['front', 'wrist']:  # Known camera keys
        if cam_key in observations[0]:
            cam_dir = episode_dir / f"camera_{cam_key}"
            cam_dir.mkdir(exist_ok=True)
            camera_dirs[cam_key] = cam_dir
    
    for step, obs in enumerate(observations):
        for cam_key, cam_dir in camera_dirs.items():
            if cam_key in obs:
                image = obs[cam_key]
                if image is not None:
                    pil_image = Image.fromarray(image)
                    pil_image.save(cam_dir / f"frame_{step:06d}.jpg", quality=85)
    
    # Save metadata
    with open(episode_dir / "metadata.json", 'w') as f:
        json.dump(episode_data['metadata'], f, indent=2)
    
    print(f"💾 Episode {episode_num} saved to: {episode_dir}")
    return episode_dir


def main():
    parser = argparse.ArgumentParser(description="Record demonstration data for Rosmaster robot")
    
    parser.add_argument("--task", type=str, default="exploration", 
                       help="Task name (exploration, pick_and_place, or custom)")
    parser.add_argument("--episodes", type=int, default=3,
                       help="Number of episodes to record")
    parser.add_argument("--max-steps", type=int, default=200,
                       help="Maximum steps per episode")
    parser.add_argument("--fps", type=int, default=30,
                       help="Recording frequency (Hz)")
    parser.add_argument("--output-dir", type=str, default="data/recordings",
                       help="Output directory for recorded data")
    parser.add_argument("--with-cameras", action="store_true",
                       help="Include camera data in recordings")
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🤖 Rosmaster Data Recording")
    print("=" * 60)
    print(f"📝 Task: {args.task}")
    print(f"📹 Episodes: {args.episodes}")
    print(f"📊 Max steps per episode: {args.max_steps}")
    print(f"⚡ Recording FPS: {args.fps}")
    print(f"💾 Output directory: {output_dir}")
    print(f"📷 Cameras: {'Enabled' if args.with_cameras else 'Disabled'}")
    
    # Configure robot with or without cameras
    if args.with_cameras:
        camera_configs = {
            "front": {
                "type": "opencv",
                "index_or_path": "/dev/video0",
                "fps": 30,
                "width": 640,
                "height": 480,
                "color_mode": "rgb",
                "rotation": 0
            },
            "wrist": {
                "type": "opencv",  
                "index_or_path": "/dev/video2",
                "fps": 30,
                "width": 640,
                "height": 480,
                "color_mode": "rgb",
                "rotation": 0
            }
        }
    else:
        camera_configs = {}
    
    # Create robot and teleoperator configs
    robot_config = RosmasterRobotConfig(
        id=f"{args.task}_robot",
        com="/dev/ttyUSB0",
        cameras=camera_configs
    )
    
    teleop_config = RosmasterKeyboardTeleopConfig(
        id="recording_teleop",
        joint_step=2.0,  # Smaller steps for precise recording
        mock=False
    )
    
    # Create robot and teleoperator
    print("\n🔌 Creating robot and teleoperator...")
    robot = make_robot_from_config(robot_config)
    teleop = make_teleoperator_from_config(teleop_config)
    
    try:
        # Connect devices
        print("🔗 Connecting robot...")
        robot.connect(calibrate=True)
        print("✅ Robot connected!")
        
        print("🔗 Connecting teleoperator...")
        teleop.connect()
        print("✅ Teleoperator connected!")
        
        # Record episodes
        all_episodes = []
        for episode_num in range(1, args.episodes + 1):
            episode_data = record_episode(
                robot, teleop, episode_num, 
                max_steps=args.max_steps, 
                fps=args.fps
            )
            
            # Save episode
            episode_dir = save_episode_data(episode_data, output_dir, episode_num)
            all_episodes.append(episode_dir)
            
            if episode_num < args.episodes:
                print(f"\n⏸️  Episode {episode_num} complete. Press ENTER for next episode or Ctrl+C to stop...")
                try:
                    input()
                except KeyboardInterrupt:
                    print(f"\n🛑 Recording stopped after {episode_num} episodes.")
                    break
        
        # Create dataset summary
        dataset_info = {
            "task": args.task,
            "total_episodes": len(all_episodes),
            "recording_fps": args.fps,
            "max_steps_per_episode": args.max_steps,
            "with_cameras": args.with_cameras,
            "robot_config": "rosmaster",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "episodes": [str(ep.name) for ep in all_episodes]
        }
        
        import json
        with open(output_dir / "dataset_info.json", 'w') as f:
            json.dump(dataset_info, f, indent=2)
        
        print(f"\n🎉 Recording Complete!")
        print(f"📁 Dataset saved to: {output_dir}")
        print(f"📊 Total episodes: {len(all_episodes)}")
        print(f"📷 Camera data: {'Included' if args.with_cameras else 'Not included'}")
        
    except Exception as e:
        print(f"\n❌ Error during recording: {e}")
        raise
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        try:
            teleop.disconnect()
            print("✅ Teleoperator disconnected")
        except:
            pass
        try:
            robot.disconnect()  
            print("✅ Robot disconnected")
        except:
            pass
        print("👋 Recording session ended")


if __name__ == "__main__":
    main()
