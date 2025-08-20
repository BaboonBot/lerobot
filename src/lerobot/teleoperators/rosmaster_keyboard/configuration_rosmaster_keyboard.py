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

from dataclasses import dataclass

from lerobot.teleoperators.config import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("rosmaster_keyboard")
@dataclass
class RosmasterKeyboardTeleopConfig(TeleoperatorConfig):
    """Configuration for Rosmaster keyboard teleoperator."""
    
    # Joint control step size in degrees
    joint_step: float = 2.0  # Reduced from 5.0 to 2.0 for smoother control
    
    # Mock mode for testing without hardware
    mock: bool = False
