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
import time
from typing import Any
import numpy as np
import threading
from queue import Queue

from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.teleoperators.rosmaster_terminal.config import RosmasterTerminalTeleopConfig
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError


class RosmasterTerminalTeleop(Teleoperator):
    """
    Terminal-based teleoperator for Rosmaster robot providing joint-level control.
    
    Commands:
    - set all <angles>: Set all joints (e.g., 'set all 90 120 45 90 90 90')
    - set <joint> <angle>: Set single joint (e.g., 'set servo_1 120')
    - get: Show current positions  
    - help: Show help
    - quit: Exit teleop
    """

    config_class = RosmasterTerminalTeleopConfig
    name = "rosmaster_terminal"

    def __init__(self, config: RosmasterTerminalTeleopConfig):
        super().__init__(config)
        self.config = config
        
        self.input_queue = Queue()
        self.current_positions = np.array([90.0, 90.0, 90.0, 90.0, 90.0, 90.0], dtype=np.float32)
        self.is_running = False
        self.input_thread = None
        self.logs = {}

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
        return self.is_running

    @property
    def is_calibrated(self) -> bool:
        return True

    def connect(self) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(
                "RosmasterTerminalTeleop is already connected."
            )

        if self.config.mock:
            logging.info("🎮 Using mock terminal teleoperator (no real input).")
            self._mock_connected = True
            return

        self.is_running = True
        
        # Start input thread
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
        
        print("\n✅ Rosmaster Terminal Teleoperator Active!")
        print("🎯 Direct joint angle control enabled!")
        self._show_help()
        self._show_current_positions()

    def disconnect(self) -> None:
        if not self.is_connected:
            return
            
        if hasattr(self, '_mock_connected'):
            self._mock_connected = False
            return
            
        print("\n🔌 Disconnecting terminal teleop...")
        self.is_running = False

    def calibrate(self) -> None:
        pass

    def configure(self):
        pass

    def get_action(self) -> dict[str, Any]:
        if not self.is_connected:
            raise DeviceNotConnectedError(
                "RosmasterTerminalTeleop is not connected. Run connect() first."
            )

        if self.config.mock:
            # Return current positions for mock mode
            action = {}
            for i, name in enumerate([f"servo_{j+1}" for j in range(6)]):
                action[name] = self.current_positions[i]
            return action

        self._process_input_queue()

        # Return current positions as individual joint actions
        action = {}
        for i, name in enumerate([f"servo_{j+1}" for j in range(6)]):
            action[name] = self.current_positions[i]
        
        return action

    def _input_loop(self):
        """Main input loop running in separate thread."""
        while self.is_running:
            try:
                command = input("rosmaster> ").strip()
                if command:
                    self.input_queue.put(command)
                    
            except (EOFError, KeyboardInterrupt):
                print("\n🔌 Disconnecting due to interrupt...")
                self.is_running = False
                break
            except Exception as e:
                print(f"❌ Error reading input: {e}")

    def _process_input_queue(self):
        """Process commands from input queue."""
        while not self.input_queue.empty():
            try:
                command = self.input_queue.get_nowait()
                self._process_command(command)
            except Exception as e:
                print(f"❌ Error processing command: {e}")

    def _process_command(self, command: str):
        """Process a terminal command."""
        parts = command.strip().split()
        if not parts:
            return

        cmd = parts[0].lower()

        if cmd == "help":
            self._show_help()
            
        elif cmd == "quit" or cmd == "exit":
            self.is_running = False
            
        elif cmd == "get":
            self._show_current_positions()
            
        elif cmd == "set":
            if len(parts) < 3:
                print("❌ Usage: set <joint> <angle> OR set all <angle1> <angle2> ... <angle6>")
                return
                
            if parts[1].lower() == "all":
                if len(parts) != 8:  # 'set' 'all' + 6 angles
                    print("❌ Usage: set all <servo_1> <servo_2> <servo_3> <servo_4> <servo_5> <servo_6>")
                    return
                    
                try:
                    angles = [float(parts[i+2]) for i in range(6)]
                    
                    # Validate all angles (0-180 degrees)
                    for i, angle in enumerate(angles):
                        if not (0 <= angle <= 180):
                            print(f"❌ Angle {angle}° out of range for servo_{i+1}. Range: [0°, 180°]")
                            return
                    
                    # Set all angles
                    self.current_positions = np.array(angles, dtype=np.float32)
                    print(f"✅ Set all joints: {angles}")
                    
                except ValueError:
                    print("❌ All angles must be numbers.")
                    
            else:
                # Set single joint
                joint = parts[1].lower()
                if not joint.startswith("servo_"):
                    print(f"❌ Unknown joint: {joint}")
                    print("Available joints: servo_1, servo_2, servo_3, servo_4, servo_5, servo_6")
                    return
                    
                try:
                    joint_num = int(joint.split("_")[1]) - 1
                    if not (0 <= joint_num <= 5):
                        print(f"❌ Joint number must be 1-6, got: {joint_num + 1}")
                        return
                        
                    angle = float(parts[2])
                    if not (0 <= angle <= 180):
                        print(f"❌ Angle {angle}° out of range. Range: [0°, 180°]")
                        return
                        
                    self.current_positions[joint_num] = angle
                    print(f"✅ Set {joint} = {angle}°")
                    
                except (ValueError, IndexError):
                    print("❌ Invalid joint name or angle.")
                    
        else:
            print(f"❌ Unknown command: {cmd}")
            print("Type 'help' for available commands.")

    def _show_help(self):
        """Display help information."""
        print("\n📋 Available Commands:")
        print("  set all <angles>        - Set all 6 joints (e.g., 'set all 90 120 45 90 90 90')")
        print("  set <joint> <angle>     - Set single joint (e.g., 'set servo_1 120')")
        print("  get                     - Show current joint positions")
        print("  help                    - Show this help")
        print("  quit                    - Exit teleoperator")
        print("\n📍 Joint Names: servo_1, servo_2, servo_3, servo_4, servo_5, servo_6")
        print("📐 All angles in degrees [0-180]")

    def _show_current_positions(self):
        """Display current joint positions."""
        print("\n📍 Current Joint Positions:")
        for i, angle in enumerate(self.current_positions):
            print(f"  servo_{i+1}: {angle:6.1f}°")

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        pass
