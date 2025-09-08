#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from functools import cached_property

import numpy as np

from lerobot.cameras import CameraConfig
from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.robots import Robot, RobotConfig
from lerobot.motors.motors_bus import Motor, MotorNormMode
from lerobot.motors.yahboom.yahboom import RosmasterMotorsBus

logger = logging.getLogger(__name__)

@dataclass
@RobotConfig.register_subclass("rosmaster")
class RosmasterRobotConfig(RobotConfig):
    """Configuration for Rosmaster Robot."""
    
    com: str = "/dev/myserial"
    id: str = "rosmaster_arm"
    cameras: Dict[str, CameraConfig] = field(default_factory=dict)


class RosmasterRobot(Robot):
    """LeRobot-compatible class for the Rosmaster robotic arm."""
    
    config_class = RosmasterRobotConfig
    name = "rosmaster"

    def __init__(self, config: RosmasterRobotConfig):
        super().__init__(config=config)

        # Define the 6 joint names for the Rosmaster arm
        self.joint_names = [f"servo_{i+1}" for i in range(6)]

        # Define motors with proper IDs (1-6) matching physical servo IDs
        motors = {
            name: Motor(id=i + 1, model="RosmasterServo", norm_mode=MotorNormMode.DEGREES)
            for i, name in enumerate(self.joint_names)
        }

        # Initialize the motor bus with the specified port
        self.motors_bus = RosmasterMotorsBus(port=config.com, motors=motors)
        
        # Initialize cameras
        self.cameras = make_cameras_from_configs(config.cameras)
        
        self._is_connected = False

    @property
    def _motors_ft(self) -> dict[str, type]:
        """Motor features - individual joint positions as floats."""
        return {name: float for name in self.joint_names}

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        """Camera features with proper shape tuples."""
        camera_features = {}
        for cam_key, camera in self.cameras.items():
            # Get camera config dimensions or use defaults
            if hasattr(camera.config, 'height') and hasattr(camera.config, 'width'):
                height = camera.config.height
                width = camera.config.width
            else:
                height, width = 480, 640  # Default camera resolution
            camera_features[cam_key] = (height, width, 3)  # (H, W, C)
        return camera_features

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        """Structure of observation dictionary - individual joint positions plus camera images."""
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        """Structure of action dictionary - individual joint positions."""
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        """Returns True if the robot is connected."""
        return self._is_connected

    def connect(self, calibrate: bool = True) -> None:
        """Connect to the Rosmaster robot and cameras."""
        print("Connecting to Rosmaster robot...")
        self.motors_bus.connect()
        
        print("Enabling servo torque for robot control...")
        self.motors_bus.enable_torque()
        time.sleep(0.5)
        
        # Handle calibration if needed
        if not self.is_calibrated and calibrate:
            logger.info("Robot is not calibrated. Running calibration...")
            self.calibrate()
        
        # Connect cameras
        print("Connecting cameras...")
        for cam_key, camera in self.cameras.items():
            try:
                camera.connect()
                print(f"  ✓ Connected camera: {cam_key}")
            except Exception as e:
                logger.warning(f"Failed to connect camera {cam_key}: {e}")
        
        self._is_connected = True
        print("Rosmaster robot connected and ready for movement.")

    @property
    def is_calibrated(self) -> bool:
        """Returns True since calibration is handled by the driver."""
        return self.motors_bus.is_calibrated

    def calibrate(self) -> None:
        """No-op for Rosmaster as calibration is internal."""
        logger.info("Rosmaster robot calibration is handled internally by the driver.")
        pass

    def configure(self) -> None:
        """Apply configuration - ensure torque is enabled."""
        if not self.is_connected:
            raise RuntimeError("Robot must be connected before configuration.")
        self.motors_bus.enable_torque()

    def get_observation(self) -> Dict[str, Any]:
        """Get current joint positions and camera images from the robot."""
        if not self.is_connected:
            raise RuntimeError("Robot is not connected.")

        # Get joint positions with error handling
        try:
            positions_dict = self.motors_bus.sync_read("Present_Position")
            
            # Check if we got valid readings for all joints
            missing_joints = [name for name in self.joint_names if name not in positions_dict]
            if missing_joints:
                # Reduce warning frequency - only log every 100 calls to avoid terminal spam
                if not hasattr(self, '_warning_counter'):
                    self._warning_counter = 0
                self._warning_counter += 1
                
                if self._warning_counter % 100 == 1:  # Log first time and every 100th time
                    logger.debug(f"Position read warnings suppressed (common with Rosmaster hardware)")
                
                # Use fallback: try individual reads or use default positions
                for name in missing_joints:
                    try:
                        positions_dict[name] = self.motors_bus.read("Present_Position", name)
                    except Exception as e:
                        # Suppress individual read warnings too - they're very common
                        positions_dict[name] = 90.0  # Default safe position
            
        except Exception as e:
            logger.error(f"Failed to read joint positions: {e}")
            # Return default positions if reading fails
            positions_dict = {name: 90.0 for name in self.joint_names}
        
        # Build observation dictionary with individual joint positions
        obs_dict = {name: float(positions_dict[name]) for name in self.joint_names}
        
        # Get camera images
        for cam_key, camera in self.cameras.items():
            try:
                start_time = time.perf_counter()
                obs_dict[cam_key] = camera.async_read()
                dt_ms = (time.perf_counter() - start_time) * 1e3
                logger.debug(f"Read {cam_key} camera: {dt_ms:.1f}ms")
            except Exception as e:
                logger.warning(f"Failed to read from camera {cam_key}: {e}")
                # You might want to provide a dummy image or skip this camera
                continue
                
        return obs_dict

    def send_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Send action commands to the robot."""
        if not self.is_connected:
            raise RuntimeError("Robot is not connected.")

        # Convert individual joint actions to command dictionary
        command_dict = {}
        for name in self.joint_names:
            if name in action:
                value = action[name]
                # Handle both scalar and array values
                if hasattr(value, '__iter__') and not isinstance(value, str):
                    command_dict[name] = float(value[0])
                else:
                    command_dict[name] = float(value)
            else:
                # Maintain current position if joint not specified
                current_obs = self.get_observation()
                command_dict[name] = float(current_obs[name])

        # Debug: Print what we're sending
        logger.debug(f"Sending command_dict: {command_dict}")
        
        try:
            # Send the actual motor commands
            self.motors_bus.sync_write("Goal_Position", command_dict)
            logger.debug("Motor commands sent successfully")
        except Exception as e:
            logger.error(f"Failed to send motor commands: {e}")
            raise

        return action

    def disconnect(self) -> None:
        """Disconnect from the robot and cameras."""
        if self.is_connected:
            print("Disconnecting from Rosmaster robot...")
            
            # Disconnect cameras
            for cam_key, camera in self.cameras.items():
                try:
                    camera.disconnect()
                    print(f"  ✓ Disconnected camera: {cam_key}")
                except Exception as e:
                    logger.warning(f"Failed to disconnect camera {cam_key}: {e}")
            
            # Disconnect motors
            self.motors_bus.disconnect()
            self._is_connected = False
            print("Rosmaster robot disconnected.")

