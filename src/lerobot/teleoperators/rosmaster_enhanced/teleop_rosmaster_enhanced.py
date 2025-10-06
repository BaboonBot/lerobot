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

from .configuration_rosmaster_enhanced import RosmasterEnhancedTeleopConfig

PYNPUT_AVAILABLE = True
try:
    from pynput import keyboard
    logging.info("pynput is available for keyboard input.")
except ImportError:
    PYNPUT_AVAILABLE = False
    keyboard = None
    logging.warning("pynput is not available. Using mock keyboard teleoperator.")


class RosmasterEnhancedTeleop(Teleoperator):
    """
    Enhanced keyboard teleoperator for Rosmaster robot with torque control functionality.
    
    Key mapping:
    - q/a: Joint 1 (+/-)
    - w/s: Joint 2 (+/-)  
    - e/d: Joint 3 (+/-)
    - r/f: Joint 4 (+/-)
    - t/g: Joint 5 (+/-)
    - y/h: Joint 6 (+/-)
    
    Torque Control:
    - z: Enable torque (motors can resist movement)
    - x: Disable torque (motors can be moved freely by hand)
    
    Other Controls:
    - SPACE: Lock/Unlock position control (SAFETY FEATURE)
    - ESC: Disconnect
    """

    config_class = RosmasterEnhancedTeleopConfig
    name = "rosmaster_enhanced"

    def __init__(self, config: RosmasterEnhancedTeleopConfig):
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
        
        # Torque control state
        self.torque_enabled = True  # Start with torque enabled
        self.last_torque_state = True  # Track previous torque state
        self.position_sync_enabled = True  # Whether to sync positions when torque disabled
        
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
        # Include both joint positions and torque control commands
        features = {f"servo_{i+1}": (1, np.float32) for i in range(6)}
        # Add special torque control actions
        features["torque_enable"] = bool
        features["torque_disable"] = bool
        return features

    @property
    def feedback_features(self) -> dict:
        # Request position feedback from the robot
        return {f"servo_{i+1}": float for i in range(6)}

    @property
    def is_connected(self) -> bool:
        if self.config.mock or hasattr(self, '_mock_connected'):
            return getattr(self, '_mock_connected', False)
        return self.listener is not None and self.listener.running

    @property
    def is_calibrated(self) -> bool:
        return True

    def connect(self) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(
                "RosmasterEnhancedTeleop is already connected."
            )

        if self.config.mock:
            logging.info("🎮 Using mock enhanced keyboard teleoperator (no real input).")
            self._mock_connected = True
            return

        if PYNPUT_AVAILABLE:
            logging.info("🎮 pynput available - enabling real enhanced keyboard listener.")
            try:
                self.listener = keyboard.Listener(
                    on_press=self._on_press,
                    on_release=self._on_release,
                )
                self.listener.start()
                print("\n✅ Rosmaster Enhanced Keyboard Teleoperator Active!")
                print("🎯 Real keyboard input with torque control enabled!")
                print("Key mappings:")
                print("  q/a: Joint 1 (+/-)")
                print("  w/s: Joint 2 (+/-)")
                print("  e/d: Joint 3 (+/-)")
                print("  r/f: Joint 4 (+/-)")
                print("  t/g: Joint 5 (+/-)")
                print("  y/h: Joint 6 (+/-)")
                print()
                print("Torque Control:")
                print("  z: Enable torque (motors resist movement)")
                print("  x: Disable torque (motors can be moved freely)")
                print()
                print("  SPACE: Lock/Unlock position control (SAFETY FEATURE)")
                print("  ESC: Disconnect")
                print(f"  Joint step: {self.config.joint_step}°")
                
                torque_status = "🟢 ENABLED" if self.torque_enabled else "🔴 DISABLED"
                position_status = "🔒 LOCKED" if self.position_locked else "🔓 UNLOCKED"
                print(f"  Torque: {torque_status}")
                print(f"  Position control: {position_status}")
                
            except Exception as e:
                logging.error(f"Failed to start keyboard listener: {e}")
                raise
        else:
            logging.error("pynput not available - cannot use enhanced keyboard teleoperator.")
            raise RuntimeError("pynput not available")

    def calibrate(self) -> None:
        pass

    def _on_press(self, key):
        if hasattr(key, "char"):
            char = key.char
            self.event_queue.put((char, True))
            
            # Handle torque control commands immediately
            if char == 'z':  # Enable torque
                if not self.torque_enabled:
                    self.torque_enabled = True
                    print("🟢 Torque ENABLED - Motors will resist movement")
                    print("   Position syncing complete - robot will hold current positions")
            elif char == 'x':  # Disable torque
                if self.torque_enabled:
                    self.torque_enabled = False
                    print("🔴 Torque DISABLED - Motors can be moved freely by hand")
                    print("   🔄 Position syncing active - move robot manually to update positions")
                    
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

        if not self.is_connected:
            raise DeviceNotConnectedError(
                "RosmasterEnhancedTeleop is not connected. You need to run `connect()` before `get_action()`."
            )

        # Process keyboard events
        self._drain_pressed_keys()

        current_time = time.perf_counter()

        # Check for mock mode
        if self.config.mock or hasattr(self, '_mock_connected'):
            # Return fixed positions for mock mode
            action = {}
            for i, name in enumerate([f"servo_{j+1}" for j in range(6)]):
                action[name] = self.current_positions[i]
            # Mock mode always returns no torque commands
            action["torque_enable"] = False
            action["torque_disable"] = False
            return action

        # If position is locked, return current positions without changes
        if self.position_locked:
            action = {}
            for i, name in enumerate([f"servo_{j+1}" for j in range(6)]):
                action[name] = self.current_positions[i]
            action["torque_enable"] = False
            action["torque_disable"] = False
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

        # Check if torque commands were triggered this cycle
        torque_enable_cmd = 'z' in self.current_pressed
        torque_disable_cmd = 'x' in self.current_pressed

        # Return action with individual joint positions and torque commands
        action = {}
        for i, name in enumerate([f"servo_{j+1}" for j in range(6)]):
            action[name] = self.current_positions[i]
        
        # Add torque control commands
        action["torque_enable"] = torque_enable_cmd
        action["torque_disable"] = torque_disable_cmd
        
        return action

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        """Receive position feedback from robot and update internal positions."""
        if not self.torque_enabled and self.position_sync_enabled:
            # When torque is disabled, sync our internal positions with robot's actual positions
            for i in range(6):
                servo_name = f"servo_{i+1}"
                if servo_name in feedback:
                    self.current_positions[i] = float(feedback[servo_name])
                    
            # Print position sync info occasionally
            if hasattr(self, '_sync_counter'):
                self._sync_counter += 1
            else:
                self._sync_counter = 1
                
            if self._sync_counter % 50 == 1:  # Print every 50 calls to avoid spam
                print(f"🔄 Syncing positions (torque disabled): "
                      f"J1={self.current_positions[0]:.1f}° "
                      f"J2={self.current_positions[1]:.1f}° "
                      f"J3={self.current_positions[2]:.1f}°...")

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(
                "RosmasterEnhancedTeleop is not connected."
            )
        
        if self.config.mock:
            self._mock_connected = False
            return
            
        if self.listener is not None:
            self.listener.stop()
            print("\n👋 Rosmaster enhanced keyboard teleoperator disconnected.")
