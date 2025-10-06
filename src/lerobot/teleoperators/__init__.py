#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
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

from .config import TeleoperatorConfig
from .teleoperator import Teleoperator
from .utils import make_teleoperator_from_config

# Import our custom Rosmaster teleoperators to register them
from .rosmaster_keyboard.teleop_rosmaster_keyboard import RosmasterKeyboardTeleop
from .rosmaster_keyboard.configuration_rosmaster_keyboard import RosmasterKeyboardTeleopConfig
from .rosmaster_mecanum.teleop_rosmaster_mecanum import RosmasterMecanumTeleop
from .rosmaster_mecanum.configuration_rosmaster_mecanum import RosmasterMecanumTeleopConfig
from .rosmaster_combined.teleop_rosmaster_combined import RosmasterCombinedTeleop
from .rosmaster_combined.configuration_rosmaster_combined import RosmasterCombinedTeleopConfig
from .rosmaster_terminal.teleop_rosmaster_terminal import RosmasterTerminalTeleop
from .rosmaster_terminal.config import RosmasterTerminalTeleopConfig


# Create module aliases like other teleoperators
from . import rosmaster_keyboard
from . import rosmaster_mecanum
from . import rosmaster_combined
from . import rosmaster_terminal

