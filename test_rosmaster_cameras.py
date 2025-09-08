#!/usr/bin/env python3

"""
Test script for Rosmaster robot camera integration
"""

import time
from pathlib import Path
from PIL import Image
import numpy as np

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.cameras.configs import ColorMode, Cv2Rotation
from src.lerobot.robots.rosmaster.rosmaster import RosmasterRobotConfig, RosmasterRobot


def test_cameras_only():
    """Test cameras without connecting to robot motors"""
    print("=== Testing Cameras Only ===")
    
    # Create camera configs
    camera_configs = {
        "front": OpenCVCameraConfig(
            index_or_path="/dev/video0",
            fps=30,
            width=640,
            height=480,
            color_mode=ColorMode.RGB,
            rotation=Cv2Rotation.NO_ROTATION
        ),
        "wrist": OpenCVCameraConfig(
            index_or_path="/dev/video2", 
            fps=30,
            width=640,
            height=480,
            color_mode=ColorMode.RGB,
            rotation=Cv2Rotation.NO_ROTATION
        )
    }
    
    # Create robot config with cameras (but don't connect motors)
    config = RosmasterRobotConfig(
        com="/dev/myserial",  # Won't be used since we're not connecting
        cameras=camera_configs
    )
    
    robot = RosmasterRobot(config)
    
    try:
        # Connect only cameras
        print("Connecting cameras...")
        for cam_key, camera in robot.cameras.items():
            camera.connect()
            print(f"  ✓ Connected camera: {cam_key}")
        
        # Test capturing images
        print("\nCapturing test images...")
        output_dir = Path("outputs/camera_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(5):
            print(f"  Capture {i+1}/5...")
            for cam_key, camera in robot.cameras.items():
                image = camera.async_read()
                print(f"    {cam_key}: {image.shape}, dtype: {image.dtype}")
                
                # Save image
                pil_image = Image.fromarray(image)
                pil_image.save(output_dir / f"{cam_key}_frame_{i:03d}.jpg")
            
            time.sleep(0.1)
        
        print(f"\n✓ Images saved to {output_dir}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect cameras
        for cam_key, camera in robot.cameras.items():
            try:
                camera.disconnect()
                print(f"  ✓ Disconnected camera: {cam_key}")
            except:
                pass


def test_full_robot():
    """Test full robot with cameras and motors"""
    print("\n=== Testing Full Robot ===")
    
    # Load config from YAML
    from lerobot.robots import make_robot_from_yaml
    
    try:
        robot = make_robot_from_yaml("configs/robot/rosmaster.yaml")
        robot.connect()
        
        print("Getting observations with cameras...")
        for i in range(3):
            obs = robot.get_observation()
            print(f"  Observation {i+1}:")
            print(f"    Joint positions: {obs['joint_positions']}")
            for cam_key in robot.cameras.keys():
                if cam_key in obs:
                    print(f"    {cam_key} image: {obs[cam_key].shape}")
            time.sleep(0.5)
        
        robot.disconnect()
        print("✓ Full robot test completed")
        
    except Exception as e:
        print(f"Error in full robot test: {e}")


if __name__ == "__main__":
    # Test cameras first (safer)
    test_cameras_only()
    
    # Uncomment to test full robot with motors
    # test_full_robot()
