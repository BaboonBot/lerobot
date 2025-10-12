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

from .configuration_rosmaster_mecanum import RosmasterMecanumTeleopConfig

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
    logging.info("pynput is available for keyboard input.")
except ImportError:
    PYNPUT_AVAILABLE = False
    keyboard = None
    logging.warning("pynput is not available. Using mock keyboard teleoperator.")


class RosmasterMecanumTeleop(Teleoperator):
    """
    Mecanum wheel teleoperator for Rosmaster robot providing base movement control.
    
    Key mapping for mecanum wheel control:
    - w/s: Forward/Backward movement (v_x)
    - a/d: Left/Right strafe movement (v_y)
    - q/e: Rotate left/right (v_z)
    """

    config_class = RosmasterMecanumTeleopConfig
    name = "rosmaster_mecanum"

    def __init__(self, config: RosmasterMecanumTeleopConfig):
        super().__init__(config)
        self.config = config
        
        self.event_queue = Queue()
        self.current_pressed = {}
        self.listener = None
        self.logs = {}
        
        # Initialize mecanum wheel velocities (all stopped)
        self.current_velocities = np.array([0.0, 0.0, 0.0], dtype=np.float32)  # [v_x, v_y, v_z]
        
        # Movement control to prevent sudden movements
        self.last_command_time = 0
        self.command_rate_limit = 0.05  # Minimum 50ms between velocity changes
        self.movement_locked = True  # Start with movement locked for safety
        
        # Key mapping for mecanum wheel control
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

    @property
    def action_features(self) -> dict:
        # Return mecanum wheel velocities
        return {
            "v_x": (1, np.float32),
            "v_y": (1, np.float32), 
            "v_z": (1, np.float32)
        }

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
                "RosmasterMecanumTeleop is already connected."
            )

        if self.config.mock:
            logging.info("🎮 Using mock mecanum teleoperator (no real input).")
            self._mock_connected = True
            return

        if PYNPUT_AVAILABLE:
            logging.info("🎮 pynput available - enabling real keyboard listener for mecanum wheels.")
            try:
                self.listener = keyboard.Listener(
                    on_press=self._on_press,
                    on_release=self._on_release,
                )
                self.listener.start()
                print("\n✅ Rosmaster Mecanum Wheel Teleoperator Active!")
                print("🚗 Real keyboard input enabled for base movement!")
                print("Key mappings:")
                print("  w/s: Forward/Backward")
                print("  a/d: Strafe Left/Right")
                print("  q/e: Rotate Left/Right")
                print("  SPACE: Lock/Unlock movement (prevents accidental movement)")
                print("  ESC: Disconnect")
                print(f"  Movement step: {self.config.movement_step} m/s")
                print(f"  Rotation step: {self.config.rotation_step} rad/s")
                print("  ⚠️  Movement is LOCKED by default - press SPACE to unlock!")
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
            # Toggle movement lock/unlock
            self.movement_locked = not self.movement_locked
            status = "🔒 LOCKED" if self.movement_locked else "🔓 UNLOCKED"
            print(f"Movement control: {status}")

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
                "RosmasterMecanumTeleop is not connected. You need to run `connect()` before `get_action()`."
            )

        if self.config.mock:
            # Return zero velocities for mock mode
            return {"v_x": 0.0, "v_y": 0.0, "v_z": 0.0}

        self._drain_pressed_keys()

        # Check if movement is locked
        if self.movement_locked:
            # Return zero velocities without any changes
            action = {
                "v_x": 0.0,
                "v_y": 0.0, 
                "v_z": 0.0
            }
            return action

        # Apply movement based on currently pressed keys
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

        # Update current velocities
        self.current_velocities = new_velocities
        self.last_command_time = current_time

        self.logs["read_vel_dt_s"] = time.perf_counter() - before_read_t

        # Return action with mecanum wheel velocities
        action = {
            "v_x": float(self.current_velocities[0]),
            "v_y": float(self.current_velocities[1]),
            "v_z": float(self.current_velocities[2])
        }
        
        return action

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        pass

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(
                "RosmasterMecanumTeleop is not connected."
            )
        
        if self.config.mock:
            self._mock_connected = False
            return
            
        if self.listener is not None:
            self.listener.stop()
            print("\n👋 Rosmaster mecanum wheel teleoperator disconnected.")
