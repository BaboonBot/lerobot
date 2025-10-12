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
from queue import Queue
from typing import Any

import numpy as np

from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError
from lerobot.teleoperators.teleoperator import Teleoperator

from .configuration_rosmaster_combined import RosmasterCombinedTeleopConfig

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
    logging.info("pynput is available for keyboard input.")
except ImportError:
    PYNPUT_AVAILABLE = False
    keyboard = None
    logging.warning("pynput is not available. Using mock keyboard teleoperator.")


class RosmasterCombinedTeleop(Teleoperator):
    """
    Combined teleoperator for Rosmaster robot providing both mecanum wheel and arm control.
    
    Mecanum wheel controls:
    - w/s: Forward/Backward movement (v_x)
    - a/d: Left/Right strafe movement (v_y)
    - q/e: Rotate left/right (v_z)
    
    Arm joint controls:
    - t/g: Joint 1 (+/-) - Base rotation
    - y/h: Joint 2 (+/-) - Shoulder
    - u/j: Joint 3 (+/-) - Elbow
    - i/k: Joint 4 (+/-) - Wrist pitch
    - o/l: Joint 5 (+/-) - Wrist roll
    - p/;: Joint 6 (+/-) - Gripper
    """

    config_class = RosmasterCombinedTeleopConfig
    name = "rosmaster_combined"

    def __init__(self, config: RosmasterCombinedTeleopConfig):
        super().__init__(config)
        self.config = config
        
        self.event_queue = Queue()
        self.current_pressed = {}
        self.listener = None
        self.logs = {}
        
        # Initialize joint positions (middle position for safety)
        self.current_positions = np.array([90.0, 90.0, 90.0, 90.0, 90.0, 90.0], dtype=np.float32)
        
        # Initialize mecanum wheel velocities (all stopped)
        self.current_velocities = np.array([0.0, 0.0, 0.0], dtype=np.float32)  # [v_x, v_y, v_z]
        
        # Movement control to prevent sudden movements
        self.last_command_time = 0
        self.command_rate_limit = 0.05  # Minimum 50ms between commands
        self.control_locked = True  # Start with everything locked for safety
        
        # Key mapping for mecanum wheel control (WASDQE)
        self.key_to_velocity_delta = {
            # Forward/Backward (v_x)
            'w': (0, +self.config.movement_step),  # Forward
            's': (0, -self.config.movement_step),  # Backward
            
            # Left/Right strafe (v_y) 
            'a': (1, +self.config.movement_step),  # Strafe left
            'd': (1, -self.config.movement_step),  # Strafe right
            
            # Rotation (v_z)
            'q': (2, +self.config.rotation_step),   # Rotate left
            'e': (2, -self.config.rotation_step),   # Rotate right
        }
        
        # Key mapping for joint control (TG YH UJ IK OL P;)
        self.key_to_joint_delta = {
            # Joint 1 - Base rotation
            't': (0, +self.config.joint_step),  # Joint 1 +
            'g': (0, -self.config.joint_step),  # Joint 1 -
            
            # Joint 2 - Shoulder
            'y': (1, +self.config.joint_step),  # Joint 2 +
            'h': (1, -self.config.joint_step),  # Joint 2 -
            
            # Joint 3 - Elbow
            'u': (2, +self.config.joint_step),  # Joint 3 +
            'j': (2, -self.config.joint_step),  # Joint 3 -
            
            # Joint 4 - Wrist pitch
            'i': (3, +self.config.joint_step),  # Joint 4 +
            'k': (3, -self.config.joint_step),  # Joint 4 -
            
            # Joint 5 - Wrist roll
            'o': (4, +self.config.joint_step),  # Joint 5 +
            'l': (4, -self.config.joint_step),  # Joint 5 -
            
            # Joint 6 - Gripper
            'p': (5, +self.config.joint_step),  # Joint 6 +
            ';': (5, -self.config.joint_step),  # Joint 6 -
        }

    @property
    def action_features(self) -> dict:
        # Return both joint positions and mecanum wheel velocities
        joint_features = {f"servo_{i+1}": (1, np.float32) for i in range(6)}
        mecanum_features = {
            "v_x": (1, np.float32),
            "v_y": (1, np.float32), 
            "v_z": (1, np.float32)
        }
        return {**joint_features, **mecanum_features}

    @property
    def feedback_features(self) -> dict:
        return {}

    @property
    def is_connected(self) -> bool:
        if self.config.mock or hasattr(self, '_mock_connected'):
            return getattr(self, '_mock_connected', False)
        return PYNPUT_AVAILABLE and isinstance(self.listener, keyboard.Listener) and self.listener.is_alive()

    @property
    def is_calibrated(self) -> bool:
        return True

    def connect(self) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(
                "RosmasterCombinedTeleop is already connected."
            )

        if self.config.mock:
            logging.info("🎮 Using mock combined teleoperator (no real input).")
            self._mock_connected = True
            return

        if PYNPUT_AVAILABLE:
            logging.info("🎮 pynput available - enabling real keyboard listener for combined control.")
            try:
                self.listener = keyboard.Listener(
                    on_press=self._on_press,
                    on_release=self._on_release,
                )
                self.listener.start()
                print("\n✅ Rosmaster Combined Teleoperator Active!")
                print("🤖 Real keyboard input enabled for arm + base control!")
                print()
                print("Mecanum Wheel Controls (Base Movement):")
                print("  w/s: Forward/Backward")
                print("  a/d: Strafe Left/Right")
                print("  q/e: Rotate Left/Right")
                print()
                print("Arm Joint Controls:")
                print("  t/g: Joint 1 (+/-) - Base rotation")
                print("  y/h: Joint 2 (+/-) - Shoulder")
                print("  u/j: Joint 3 (+/-) - Elbow")
                print("  i/k: Joint 4 (+/-) - Wrist pitch")
                print("  o/l: Joint 5 (+/-) - Wrist roll")
                print("  p/;: Joint 6 (+/-) - Gripper")
                print()
                print("  SPACE: Lock/Unlock all controls (SAFETY FEATURE)")
                print("  ESC: Disconnect")
                print(f"  Joint step: {self.config.joint_step}°")
                print(f"  Movement step: {self.config.movement_step} m/s")
                print(f"  Rotation step: {self.config.rotation_step} rad/s")
                print("  ⚠️  All controls are LOCKED by default - press SPACE to unlock!")
                print()
            except Exception as e:
                logging.error(f"❌ Failed to start keyboard listener: {e}")
                logging.warning("🎮 Falling back to mock mode")
                self.listener = None
                self._mock_connected = True
        else:
            logging.warning("❌ pynput not available - using mock teleoperator.")
            self.listener = None
            self._mock_connected = True

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    def _on_press(self, key):
        if hasattr(key, "char"):
            self.event_queue.put((key.char, True))
        elif key == keyboard.Key.space:
            # Toggle control lock/unlock for both arm and mecanum wheels
            self.control_locked = not self.control_locked
            status = "🔒 LOCKED" if self.control_locked else "🔓 UNLOCKED"
            print(f"All controls (arm + base): {status}")

    def _on_release(self, key):
        if hasattr(key, "char"):
            self.event_queue.put((key.char, False))
        if key == keyboard.Key.esc:
            logging.info("ESC pressed, disconnecting.")
            self.disconnect()

    def _drain_pressed_keys(self):
        """Process all pending keyboard events."""
        while not self.event_queue.empty():
            try:
                key_char, is_pressed = self.event_queue.get_nowait()
                if is_pressed:
                    self.current_pressed[key_char] = True
                else:
                    self.current_pressed.pop(key_char, None)
            except:
                break

    def get_action(self) -> dict[str, Any]:
        before_read_t = time.perf_counter()
        current_time = time.time()

        if not self.is_connected:
            raise DeviceNotConnectedError(
                "RosmasterCombinedTeleop is not connected. You need to run `connect()` before `get_action()`."
            )

        if self.config.mock:
            # Return default values for mock mode
            action = {}
            # Joint positions
            for i in range(6):
                action[f"servo_{i+1}"] = self.current_positions[i]
            # Mecanum velocities
            action["v_x"] = 0.0
            action["v_y"] = 0.0
            action["v_z"] = 0.0
            return action

        self._drain_pressed_keys()

        # Check if controls are locked
        if self.control_locked:
            # Return current positions and zero velocities
            action = {}
            # Joint positions (maintain current)
            for i in range(6):
                action[f"servo_{i+1}"] = self.current_positions[i]
            # Mecanum velocities (zero)
            action["v_x"] = 0.0
            action["v_y"] = 0.0
            action["v_z"] = 0.0
            return action

        # Rate limiting to prevent too frequent commands
        if current_time - self.last_command_time < self.command_rate_limit:
            # Return current state without changes
            action = {}
            # Joint positions
            for i in range(6):
                action[f"servo_{i+1}"] = self.current_positions[i]
            # Mecanum velocities
            action["v_x"] = float(self.current_velocities[0])
            action["v_y"] = float(self.current_velocities[1])
            action["v_z"] = float(self.current_velocities[2])
            return action

        # Process joint movements
        new_positions = self.current_positions.copy()
        joint_movements = []
        joint_position_changed = False
        
        for key_char in self.current_pressed:
            if key_char in self.key_to_joint_delta:
                joint_idx, delta = self.key_to_joint_delta[key_char]
                new_positions[joint_idx] += delta
                joint_movements.append(f"J{joint_idx+1}{'+'if delta > 0 else '-'}")
                joint_position_changed = True

        # Apply joint safety limits
        if joint_position_changed:
            for i in range(6):
                if i == 4:  # Joint 5 (servo_5) has range 0-270
                    new_positions[i] = np.clip(new_positions[i], 0, 270)
                else:  # Joints 1-4,6 have range 0-180
                    new_positions[i] = np.clip(new_positions[i], 0, 180)
            
            self.current_positions = new_positions

        # Process mecanum wheel movements
        new_velocities = np.array([0.0, 0.0, 0.0], dtype=np.float32)  # Reset to zero
        
        for key_char in self.current_pressed:
            if key_char in self.key_to_velocity_delta:
                velocity_idx, delta = self.key_to_velocity_delta[key_char]
                new_velocities[velocity_idx] += delta

        # Apply velocity limits for safety
        # X3 robot limits: v_x=[-1.0, 1.0], v_y=[-1.0, 1.0], v_z=[-5, 5]
        new_velocities[0] = np.clip(new_velocities[0], -1.0, 1.0)   # v_x
        new_velocities[1] = np.clip(new_velocities[1], -1.0, 1.0)   # v_y 
        new_velocities[2] = np.clip(new_velocities[2], -5.0, 5.0)   # v_z

        self.current_velocities = new_velocities
        self.last_command_time = current_time

        self.logs["read_combined_dt_s"] = time.perf_counter() - before_read_t

        # Return combined action with both joint positions and mecanum velocities
        action = {}
        
        # Joint positions
        for i in range(6):
            action[f"servo_{i+1}"] = float(self.current_positions[i])
        
        # Mecanum velocities
        action["v_x"] = float(self.current_velocities[0])
        action["v_y"] = float(self.current_velocities[1])
        action["v_z"] = float(self.current_velocities[2])
        
        return action

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        pass

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(
                "RosmasterCombinedTeleop is not connected."
            )
        
        if self.config.mock:
            self._mock_connected = False
            return
            
        if self.listener is not None:
            self.listener.stop()
            print("\n👋 Rosmaster combined teleoperator disconnected.")
