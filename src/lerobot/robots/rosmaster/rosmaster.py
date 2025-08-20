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
from typing import Any, Dict
from dataclasses import dataclass

import numpy as np

from lerobot.robots import Robot, RobotConfig
from lerobot.motors.motors_bus import Motor, MotorNormMode
from lerobot.motors.yahboom.yahboom import RosmasterMotorsBus

@RobotConfig.register_subclass("rosmaster")
@dataclass
class RosmasterRobotConfig(RobotConfig):
    """Configuration for the Rosmaster Robot."""
    com: str = "/dev/myserial"


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
        self._is_connected = False

    @property
    def observation_features(self) -> Dict[str, Any]:
        """Structure of observation dictionary - positions of 6 joints."""
        return {"joint_positions": (len(self.joint_names), np.float32)}

    @property
    def action_features(self) -> Dict[str, Any]:
        """Structure of action dictionary - individual joint positions."""
        return {name: (1, np.float32) for name in self.joint_names}

    @property
    def is_connected(self) -> bool:
        """Returns True if the robot is connected."""
        return self._is_connected

    def connect(self) -> None:
        """Connect to the Rosmaster robot."""
        print("Connecting to Rosmaster robot...")
        self.motors_bus.connect()
        
        print("Enabling servo torque for robot control...")
        self.motors_bus.enable_torque()
        time.sleep(0.5)
        
        self._is_connected = True
        print("Rosmaster robot connected and ready for movement.")

    @property
    def is_calibrated(self) -> bool:
        """Returns True since calibration is handled by the driver."""
        return self.motors_bus.is_calibrated

    def calibrate(self) -> None:
        """No-op for Rosmaster as calibration is internal."""
        pass

    def configure(self) -> None:
        """Apply configuration - ensure torque is enabled."""
        if not self.is_connected:
            raise RuntimeError("Robot must be connected before configuration.")
        self.motors_bus.enable_torque()

    def get_observation(self) -> Dict[str, Any]:
        """Get current joint positions from the robot."""
        if not self.is_connected:
            raise RuntimeError("Robot is not connected.")

        positions_dict = self.motors_bus.sync_read("Present_Position")
        ordered_positions = np.array(
            [positions_dict[name] for name in self.joint_names], 
            dtype=np.float32
        )
        return {"joint_positions": ordered_positions}

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
                joint_idx = self.joint_names.index(name)
                command_dict[name] = float(current_obs["joint_positions"][joint_idx])

        self.motors_bus.sync_write("Goal_Position", command_dict)
        return action

    def disconnect(self) -> None:
        """Disconnect from the robot."""
        if self.is_connected:
            print("Disconnecting from Rosmaster robot...")
            self.motors_bus.disconnect()
            self._is_connected = False
            print("Rosmaster robot disconnected.")

