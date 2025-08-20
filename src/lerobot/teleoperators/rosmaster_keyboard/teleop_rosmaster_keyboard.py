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

import logging
import numpy as np
import time
from queue import Queue
from typing import Any

from lerobot.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError
from lerobot.teleoperators.teleoperator import Teleoperator

from .configuration_rosmaster_keyboard import RosmasterKeyboardTeleopConfig

PYNPUT_AVAILABLE = True
try:
    from pynput import keyboard
except ImportError:
    PYNPUT_AVAILABLE = False
    logging.warning("pynput is not available. Using mock keyboard teleoperator.")


class RosmasterKeyboardTeleop(Teleoperator):
    """
    Keyboard teleoperator for Rosmaster robot providing joint-level control.
    
    Key mapping:
    - q/a: Joint 1 (+/-)
    - w/s: Joint 2 (+/-)  
    - e/d: Joint 3 (+/-)
    - r/f: Joint 4 (+/-)
    - t/g: Joint 5 (+/-)
    - y/h: Joint 6 (+/-)
    """

    config_class = RosmasterKeyboardTeleopConfig
    name = "rosmaster_keyboard"

    def __init__(self, config: RosmasterKeyboardTeleopConfig):
        super().__init__(config)
        self.config = config
        
        self.event_queue = Queue()
        self.current_pressed = {}
        self.listener = None
        self.logs = {}
        
        # Initialize joint positions (middle position)
        self.current_positions = np.array([90.0, 90.0, 90.0, 90.0, 90.0, 90.0], dtype=np.float32)
        self.target_positions = self.current_positions.copy()
        
        # Movement control to prevent sudden movements
        self.last_command_time = 0
        self.command_rate_limit = 0.1  # Minimum 100ms between position changes
        self.position_locked = True  # Start with positions locked
        
        # Key mapping for joint control
        self.key_to_joint_delta = {
            'q': (0, +self.config.joint_step),  # Joint 1 +
            'a': (0, -self.config.joint_step),  # Joint 1 -
            'w': (1, +self.config.joint_step),  # Joint 2 +
            's': (1, -self.config.joint_step),  # Joint 2 -
            'e': (2, +self.config.joint_step),  # Joint 3 +
            'd': (2, -self.config.joint_step),  # Joint 3 -
            'r': (3, +self.config.joint_step),  # Joint 4 +
            'f': (3, -self.config.joint_step),  # Joint 4 -
            't': (4, +self.config.joint_step),  # Joint 5 +
            'g': (4, -self.config.joint_step),  # Joint 5 -
            'y': (5, +self.config.joint_step),  # Joint 6 +
            'h': (5, -self.config.joint_step),  # Joint 6 -
        }

    @property
    def action_features(self) -> dict:
        # Return individual joint positions to match the robot's expectation
        return {f"servo_{i+1}": (1, np.float32) for i in range(6)}

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
                "RosmasterKeyboardTeleop is already connected."
            )

        if self.config.mock:
            logging.info("🎮 Using mock keyboard teleoperator (no real input).")
            self._mock_connected = True
            return

        if PYNPUT_AVAILABLE:
            logging.info("🎮 pynput available - enabling real keyboard listener.")
            try:
                self.listener = keyboard.Listener(
                    on_press=self._on_press,
                    on_release=self._on_release,
                )
                self.listener.start()
                print("\n✅ Rosmaster Keyboard Teleoperator Active!")
                print("🎯 Real keyboard input enabled!")
                print("Key mappings:")
                print("  q/a: Joint 1 (+/-)")
                print("  w/s: Joint 2 (+/-)")
                print("  e/d: Joint 3 (+/-)")
                print("  r/f: Joint 4 (+/-)")
                print("  t/g: Joint 5 (+/-)")
                print("  y/h: Joint 6 (+/-)")
                print("  SPACE: Lock/Unlock position (prevents accidental movement)")
                print("  ESC: Disconnect")
                print(f"  Step size: {self.config.joint_step}°")
                print("  ⚠️  Position is LOCKED by default - press SPACE to unlock!")
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

    def _on_press(self, key):
        if hasattr(key, "char"):
            self.event_queue.put((key.char, True))
        elif key == keyboard.Key.space:
            # Toggle position lock/unlock
            self.position_locked = not self.position_locked
            status = "🔒 LOCKED" if self.position_locked else "🔓 UNLOCKED"
            print(f"Position control: {status}")

    def _on_release(self, key):
        if hasattr(key, "char"):
            self.event_queue.put((key.char, False))
        if key == keyboard.Key.esc:
            logging.info("ESC pressed, disconnecting.")
            self.disconnect()

    def _drain_pressed_keys(self):
        """Update current pressed keys from the event queue."""
        while not self.event_queue.empty():
            key_char, is_pressed = self.event_queue.get_nowait()
            if is_pressed:
                self.current_pressed[key_char] = True
            else:
                self.current_pressed.pop(key_char, None)

    def configure(self):
        pass

    def get_action(self) -> dict[str, Any]:
        before_read_t = time.perf_counter()
        current_time = time.time()

        if not self.is_connected:
            raise DeviceNotConnectedError(
                "RosmasterKeyboardTeleop is not connected. You need to run `connect()` before `get_action()`."
            )

        if self.config.mock:
            # Return current positions for mock mode
            return {"joint_positions": self.current_positions.copy()}

        self._drain_pressed_keys()

        # Check if position is locked
        if self.position_locked:
            # Return current positions without any changes
            action = {}
            for i, name in enumerate([f"servo_{j+1}" for j in range(6)]):
                action[name] = self.current_positions[i]
            return action

        # Rate limiting to prevent too frequent commands
        if current_time - self.last_command_time < self.command_rate_limit:
            # Return current positions without changes
            action = {}
            for i, name in enumerate([f"servo_{j+1}" for j in range(6)]):
                action[name] = self.current_positions[i]
            return action

        # Apply movement based on currently pressed keys
        new_positions = self.current_positions.copy()
        movements = []
        position_changed = False
        
        for key_char in self.current_pressed:
            if key_char in self.key_to_joint_delta:
                joint_idx, delta = self.key_to_joint_delta[key_char]
                new_positions[joint_idx] += delta
                movements.append(f"J{joint_idx+1}{'+'if delta > 0 else '-'}")
                position_changed = True

        # Only update if there was actual movement
        if position_changed:
            # Apply safety limits (0-180 degrees for joints 1-4,6 and 0-270 for joint 5)
            for i in range(6):
                if i == 4:  # Joint 5 (servo_5) has range 0-270
                    new_positions[i] = np.clip(new_positions[i], 0, 270)
                else:  # Joints 1-4,6 have range 0-180
                    new_positions[i] = np.clip(new_positions[i], 0, 180)
            
            # Update current positions and command time
            self.current_positions = new_positions
            self.last_command_time = current_time

        self.logs["read_pos_dt_s"] = time.perf_counter() - before_read_t

        # Return action with individual joint positions
        action = {}
        for i, name in enumerate([f"servo_{j+1}" for j in range(6)]):
            action[name] = self.current_positions[i]
        
        return action

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        pass

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(
                "RosmasterKeyboardTeleop is not connected."
            )
        
        if self.config.mock:
            self._mock_connected = False
            return
            
        if self.listener is not None:
            self.listener.stop()
            print("\n👋 Rosmaster keyboard teleoperator disconnected.")
