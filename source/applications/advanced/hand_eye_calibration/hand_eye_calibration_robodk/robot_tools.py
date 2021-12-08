"""
# Robot Control Module
This module interfaces with the python API for RoboDK and the RoboDK software.
It can be used to connect to the specified robot, get a list of targets and set robot speeds.
"""

from robolink import Robolink, ITEM_TYPE_ROBOT, RUNMODE_RUN_ROBOT
from robodk import *


def connect_to_robot(robot_ip: str):
    """Sets up the connection to the robot and sets the mode to run,
    such that that robot will accept movement commands
    Args:
        robot_ip: unique IP address associated with robot being used
    Returns:
        Robolink item
        robot control
    """
    rdk = Robolink()
    robot = rdk.ItemUserPick("", ITEM_TYPE_ROBOT)
    if True:
        status = robot.ConnectSafe(
            robot_ip=robot_ip,
            max_attempts=5,
            wait_connection=4,
            callback_abort=None,
        )
        rdk.setRunMode(RUNMODE_RUN_ROBOT)
    print("connected")
    return rdk, robot


def set_robot_movements(robot, speed: int, joint_speed: int, accel: int, joint_accel: int):
    """Sets the speed and acceleration of the Robot
    Args:
        robot
        speed: speed of robot movement
        joint_speed: speed of joint
        accel: total acceleration of robot
        joint_accel: max acceleration of joints
    Returns:
        None
    """
    robot.setSpeed(speed)
    robot.setSpeedJoints(joint_speed)
    # Needs to be low when using 3D printed adapter.
    robot.setAcceleration(accel)
    robot.setAccelerationJoints(joint_accel)

    return None


def get_targets(rdk: Robolink, keyword: str):
    """Extract targets from roboDK, uses keyword to get set of targets. Each target in RoboDK is
    named.
    EX: target 1, target 2, target 3, pose 1, pose 2
    If only 'target' is used for keyword, then only the first 3 items are added to the list from
    the .rdk station file
    Args:
        rdk: robolink robot item
        keyword: string of name in position
    Returns:
        Array of target items
    """
    list_items = rdk.ItemList()
    targets = []

    for item in list_items:
        if keyword in item.Name():
            targets.append(item)
    return targets
