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


@TeleoperatorConfig.register_subclass("rosmaster_mecanum")
@dataclass
class RosmasterMecanumTeleopConfig(TeleoperatorConfig):
    """Configuration for Rosmaster mecanum wheel teleoperator."""
    
    # Movement step size for mecanum wheels
    movement_step: float = 0.3  # Linear velocity step size (m/s)
    rotation_step: float = 1.0  # Angular velocity step size (rad/s)
    
    # Mock mode for testing without hardware
    mock: bool = False
