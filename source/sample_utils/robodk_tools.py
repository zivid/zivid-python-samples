"""
Robot Control Module
Module interfaces with the python API for RoboDK and the RoboDK software.
It can be used to connect to the specified robot, get a list of targets and set robot speeds.

"""

from typing import Any, List, Tuple

from robodk.robolink import ITEM_TYPE_ROBOT, RUNMODE_RUN_ROBOT, Item, Robolink


def connect_to_robot(robot_ip: str) -> Tuple[Any, Any]:
    """Sets up the connection to the robot and sets the mode to run,
    such that the robot will accept movement commands.

    Args:
        robot_ip : Unique IP address associated with robot being used

    Returns:
        rdk : Robolink - the link between RoboDK and Python
        robot : Robot item in open RoboDK rdk file

    """
    rdk = Robolink()
    robot = rdk.ItemUserPick("", ITEM_TYPE_ROBOT)
    robot.ConnectSafe(
        robot_ip=robot_ip,
        max_attempts=5,
        wait_connection=4,
        callback_abort=None,
    )
    rdk.setRunMode(RUNMODE_RUN_ROBOT)
    return rdk, robot


def set_robot_speed_and_acceleration(
    robot: Item, speed: int, joint_speed: int, acceleration: int, joint_acceleration: int
) -> None:
    """Sets the speed and acceleration of the Robot.

    Args:
        robot: Robot item in open RoboDK rdk file
        speed: Set max linear speed for robot (mm/s)
        joint_speed: Set max joint speed of robot (deg/s)
        acceleration: Total linear acceleration of robot (mm/s²)
        joint_acceleration: Set max joint acceleration allowed for robot (deg/s²)

    """
    robot.setSpeed(speed)
    robot.setSpeedJoints(joint_speed)
    robot.setAcceleration(acceleration)
    robot.setAccelerationJoints(joint_acceleration)


def get_robot_targets(rdk: Robolink, target_keyword: str) -> List:
    """Extract a set of targets (poses) from roboDK using a keyword.
    If targets in the RoboDK station are named, e.g., 'target 1', 'pose 1', 'target 2', 'target 3', 'pose 2',
    and the keyword used is 'target', then only 'target 1', 'target 2', and 'target 3' are added to the
    list from the .rdk station file.

    Args:
        rdk:  Robolink - the link between RoboDK and Python
        target_keyword: The common name of the targets (poses) in RoboDK station that will be used for the hand-eye dataset

    Returns:
        List: Array of target items

    """
    list_items = rdk.ItemList()
    targets = []

    for item in list_items:
        if target_keyword in item.Name():
            targets.append(item)
    return targets
