#!/usr/bin/env python3
"""
Simple data viewer for recorded Rosmaster episodes.
"""

import numpy as np
import json
import sys
from pathlib import Path

def view_episode(episode_dir):
    """View the contents of a recorded episode."""
    episode_path = Path(episode_dir)
    
    print(f"📁 Episode: {episode_path.name}")
    print("=" * 50)
    
    # Load metadata
    if (episode_path / "metadata.json").exists():
        with open(episode_path / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        print("📊 Metadata:")
        print(f"   Episode: {metadata['episode_num']}")
        print(f"   Duration: {metadata['duration']:.2f}s")
        print(f"   Steps: {metadata['steps_recorded']}")
        print(f"   FPS: {metadata['fps']}")
        print()
    
    # Load and display joint data
    if (episode_path / "joint_positions.npy").exists():
        joint_positions = np.load(episode_path / "joint_positions.npy")
        print("🦾 Joint Positions:")
        print(f"   Shape: {joint_positions.shape}")
        print(f"   Range: [{joint_positions.min():.1f}°, {joint_positions.max():.1f}°]")
        print(f"   First frame: {joint_positions[0]}")
        print(f"   Last frame:  {joint_positions[-1]}")
        print()
    
    # Load and display action data
    if (episode_path / "actions.npy").exists():
        actions = np.load(episode_path / "actions.npy")
        print("🎮 Actions:")
        print(f"   Shape: {actions.shape}")
        print(f"   Range: [{actions.min():.1f}°, {actions.max():.1f}°]")
        print(f"   First action: {actions[0]}")
        print(f"   Last action:  {actions[-1]}")
        print()
    
    # Check for camera data
    camera_dirs = list(episode_path.glob("camera_*"))
    if camera_dirs:
        print("📷 Camera Data:")
        for cam_dir in camera_dirs:
            cam_name = cam_dir.name.replace("camera_", "")
            num_images = len(list(cam_dir.glob("*.jpg")))
            print(f"   {cam_name}: {num_images} images")
        print()
    
    # Load timestamps
    if (episode_path / "timestamps.npy").exists():
        timestamps = np.load(episode_path / "timestamps.npy")
        print("⏱️  Timestamps:")
        print(f"   Duration: {timestamps[-1] - timestamps[0]:.2f}s")
        print(f"   Average FPS: {len(timestamps) / (timestamps[-1] - timestamps[0]):.1f}")


def main():
    if len(sys.argv) > 1:
        episode_dir = sys.argv[1]
    else:
        # Default to latest episode
        recordings_dir = Path("data/recordings")
        if recordings_dir.exists():
            episodes = sorted(recordings_dir.glob("episode_*"))
            if episodes:
                episode_dir = episodes[-1]
            else:
                print("❌ No episodes found in data/recordings")
                return
        else:
            print("❌ No recordings directory found")
            return
    
    view_episode(episode_dir)


if __name__ == "__main__":
    main()
