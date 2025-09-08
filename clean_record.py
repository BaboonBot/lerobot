#!/usr/bin/env python3
"""
Clean recording script that suppresses non-essential warnings for a cleaner terminal experience.
"""

import logging
import warnings
import sys
import os

# Suppress specific warnings that clutter the terminal
warnings.filterwarnings("ignore", category=UserWarning, module="torchcodec")

# Set logging levels to reduce clutter
logging.getLogger("yahboom").setLevel(logging.ERROR)
logging.getLogger("rosmaster").setLevel(logging.ERROR)
logging.getLogger("lerobot.motors").setLevel(logging.ERROR)
logging.getLogger("lerobot.robots.rosmaster").setLevel(logging.ERROR)

# Now import and run the regular recording
if __name__ == "__main__":
    # Pass all command line arguments to the regular recording script
    os.system(f"python -m lerobot.record {' '.join(sys.argv[1:])}")
