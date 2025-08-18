#!/usr/bin/env python
import time
from typing import Any, Dict, List

import draccus
import numpy as np

# Import the base Robot class and other necessary components
from lerobot.robots import Robot, RobotConfig
from lerobot.motors.motors_bus import Motor, MotorCalibration, MotorNormMode

# Import the custom MotorsBus you created for the Rosmaster
# from my_project.rosmaster_bus import RosmasterMotorsBus
# For this example, we assume RosmasterMotorsBus is available in the same scope.
from lerobot.motors.yahboom.yahboom import RosmasterMotorsBus

# Step 1: Define a configuration class for your robot
@draccus.wrap()
class RosmasterRobotConfig(RobotConfig):
    """
    Configuration for the Rosmaster Robot.
    """
    # Add a field for the serial port, which is specific to this robot.
    com: str = draccus.field(
        default="/dev/myserial", metadata={"help": "The serial port for the Rosmaster controller."}
    )
    # You can add other robot-specific configs here if needed.


# Step 2: Implement the Robot abstract class
class RosmasterRobot(Robot):
    """
    A LeRobot-compatible class for the Rosmaster robotic arm.
    """
    # Set the required class attributes
    config_class = RosmasterRobotConfig
    name = "rosmaster"

    def __init__(self, config: RosmasterRobotConfig):
        super().__init__(config=config)

        # Define the names of the joints in a fixed order. This is crucial for
        # converting between named dictionaries and ordered numpy arrays.
        self.joint_names = [f"servo_{i+1}" for i in range(6)]

        # Define the motor objects that will be passed to the MotorsBus.
        # The IDs must match the physical servo IDs (1-6).
        motors = {
            name: Motor(id=i + 1, model="RosmasterServo", norm_mode=MotorNormMode.DEGREES)
            for i, name in enumerate(self.joint_names)
        }

        # Instantiate your custom MotorsBus
        self.bus = RosmasterMotorsBus(port=config.com, motors=motors)

        # Internal state to track connection
        self._is_connected = False

    @property
    def observation_features(self) -> Dict[str, Any]:
        """
        Defines the structure of the observation dictionary.
        For the Rosmaster, this is the position of its 6 joints.
        """
        return {
            # Key: "joint_positions", Value: a tuple for shape and the data type.
            "joint_positions": (len(self.joint_names), np.float32)
        }

    @property
    def action_features(self) -> Dict[str, Any]:
        """
        Defines the structure of the action dictionary.
        The action is to command the goal position of the 6 joints.
        """
        return {
            "joint_positions": (len(self.joint_names), np.float32)
        }

    @property
    def is_connected(self) -> bool:
        """Returns True if the robot is connected, False otherwise."""
        return self._is_connected

    def connect(self, calibrate: bool = True) -> None:
        """Establishes connection with the robot."""
        if self.is_connected:
            print("Robot is already connected.")
            return

        print("Connecting to Rosmaster robot...")
        self.bus.connect()
        self._is_connected = True
        print("Rosmaster robot connected.")

        # The Rosmaster doesn't need external calibration, so we just log it.
        if calibrate:
            self.calibrate()

    @property
    def is_calibrated(self) -> bool:
        """Returns True since the Rosmaster driver handles calibration internally."""
        return self.bus.is_calibrated

    def calibrate(self) -> None:
        """
        This is a no-op for the Rosmaster as calibration is internal to the driver.
        """
        print("Rosmaster does not require an external calibration routine. Skipping.")
        pass

    def configure(self) -> None:
        """
        Apply one-time configuration. For the Rosmaster, we ensure torque is enabled.
        """
        if not self.is_connected:
            raise RuntimeError("Robot must be connected before it can be configured.")
        print("Enabling motor torque...")
        self.bus.enable_torque()

    def get_observation(self) -> Dict[str, Any]:
        """
        Retrieve the current observation (joint angles) from the robot.
        """
        if not self.is_connected:
            raise RuntimeError("Robot is not connected. Cannot get observation.")

        # Read the named dictionary of angles from the bus
        positions_dict = self.bus.sync_read("Present_Position")

        # Convert the dictionary to an ordered numpy array
        ordered_positions = np.array(
            [positions_dict[name] for name in self.joint_names], dtype=np.float32
        )

        return {"joint_positions": ordered_positions}

    def send_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an action command (goal joint angles) to the robot.
        """
        if not self.is_connected:
            raise RuntimeError("Robot is not connected. Cannot send action.")

        # Get the commanded joint positions array from the action dictionary
        goal_positions = action["joint_positions"]

        # Convert the numpy array back to a dictionary of named angles
        # that the bus can understand.
        command_dict = {
            name: float(angle) for name, angle in zip(self.joint_names, goal_positions)
        }

        # Send the command to the bus
        self.bus.sync_write("Goal_Position", command_dict)

        # Return the original action, as the driver doesn't provide feedback on clipping.
        return action

    def disconnect(self) -> None:
        """Disconnects from the robot."""
        if self.is_connected:
            print("Disconnecting from Rosmaster robot...")
            self.bus.disconnect()
            self._is_connected = False
            print("Rosmaster robot disconnected.")

# To make this file runnable, you'd need the RosmasterMotorsBus and Rosmaster classes defined above it or imported.
# Assuming they are defined in the same file for this example.

if __name__ == '__main__':
    # --- Example Usage ---
    # This block demonstrates how to use the RosmasterRobot class.

    # 1. Create a configuration object.
    #    You would typically load this from a file or command line.
    config = RosmasterRobotConfig(
        # Make sure to change this to your actual serial port!
        com="/dev/myserial" # For Linux/macOS
        # com="COM3"      # For Windows
    )

    # 2. Instantiate the robot
    robot = RosmasterRobot(config)

    try:
        # 3. Connect to the robot
        robot.connect()

        # 4. Apply initial configuration (e.g., enable torque)
        robot.configure()

        # 5. Get an initial observation
        initial_obs = robot.get_observation()
        print(f"\nInitial Observation (joint_positions): {initial_obs['joint_positions']}")

        # 6. Define an action
        # This action moves the first and last joints to 90 degrees, and the rest to 120.
        action_array = np.array([90, 120, 120, 120, 120, 90], dtype=np.float32)
        action_dict = {"joint_positions": action_array}
        print(f"\nSending Action: {action_dict['joint_positions']}")

        # 7. Send the action
        robot.send_action(action_dict)
        time.sleep(2)  # Wait for the robot to complete the movement

        # 8. Get a new observation to see the result
        final_obs = robot.get_observation()
        print(f"\nFinal Observation (joint_positions): {final_obs['joint_positions']}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

    finally:
        # 9. Always disconnect cleanly
        robot.disconnect()