"""
Script to generate a dataset and perform hand-eye calibration using the Robodk interface.
The script communicates with the robot through High speed ethernet server using roboDK.
Each robot pose must be modified to your scene. This is done in roboDK.
"""
from robolink import Robolink, ITEM_TYPE_ROBOT, RUNMODE_RUN_ROBOT
from robodk import *

import handeye
from robot_tools import get_targets, set_robot_movements, connect_to_robot


def _main():

    user_options = handeye._options()

    if user_options.ip:
        rdk, robot = connect_to_robot(user_options.ip)
        targets = get_targets(rdk, user_options.targets)
        robot_speed_accel_limits = [100, 100, 50, 50]
        set_robot_movements(robot, *robot_speed_accel_limits)

    dataset_dir = handeye._generate_dataset(robot, targets)

    if user_options.eih:
        transform, residuals = handeye.perform_hand_eye_calibration("eye-in-hand", dataset_dir)
    else:
        transform, residuals = handeye.perform_hand_eye_calibration("eye-to-hand", dataset_dir)

    handeye._save_hand_eye_results(dataset_dir, transform, residuals)


if __name__ == "__main__":
    _main()
