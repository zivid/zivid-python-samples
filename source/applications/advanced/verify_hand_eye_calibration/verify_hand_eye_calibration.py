import argparse
import datetime
import time
from typing import List

import numpy as np
import zivid
from robodk import Mat
from sample_utils.robodk_tools import connect_to_robot, get_robot_targets, set_robot_speed_and_acceleration
from sample_utils.save_load_matrix import load_and_assert_affine_matrix
from sample_utils.transformation_matrix import TransformationMatrix


def _assisted_settings(camera: zivid.Camera, max_time_milliseconds: int = 800) -> zivid.Settings:
    """Capturing image with Zivid camera using assisted capture settings.

    Args:
        camera: Zivid camera
        max_time_milliseconds: Maximum capture time allowed in milliseconds

    Returns:
        settings_list: A list containing the acquisitions settings

    """
    suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
        max_capture_time=datetime.timedelta(milliseconds=max_time_milliseconds),
        ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
    )

    settings_list = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)

    return settings_list


def _capture_and_estimate_calibration_board_pose(camera: zivid.Camera, settings: List) -> TransformationMatrix:
    """Capturing, detecting, and estimating the pose of the calibration board.

    Args:
        camera:  Zivid camera
        settings: A list containing the camera settings

    Returns:
        TransformationMatrix object of calibration board pose

    """
    frame = camera.capture(settings)
    calibration_board_pose = zivid.calibration.detect_feature_points(frame.point_cloud()).pose().to_matrix()

    return TransformationMatrix.from_matrix(matrix=np.array(calibration_board_pose))


def _options() -> argparse.Namespace:
    """Function for taking in arguments from user.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", required=True, help="IP address of the robot controller")
    parser.add_argument(
        "--target",
        required=True,
        help="target: RoboDK target name representing a robot pose at which the calibration board is in the field of view of the camera",
    )
    parser.add_argument(
        "--tool-yaml",
        required=True,
        help="Path to YAML file that represents the transformation of the TCP relative to the end effector",
    )
    parser.add_argument(
        "--transform-yaml",
        required=True,
        help="Path to YAML file that contain the hand-eye transformation matrix",
    )

    return parser.parse_args()


def main() -> None:
    app = zivid.Application()
    user_options = _options()
    rdk, robot = connect_to_robot(user_options.ip)
    set_robot_speed_and_acceleration(robot, speed=120, joint_speed=120, acceleration=120, joint_acceleration=120)

    print("Creating the tool point transformation matrix from a YAML file")
    tool_center_point_matrix = load_and_assert_affine_matrix(user_options.tool_yaml)
    end_effector_to_tool_center_point_transform = TransformationMatrix.from_matrix(tool_center_point_matrix)

    capture_pose = get_robot_targets(rdk, target_keyword=user_options.target)

    print("Loading Hand-eye calibration")
    end_effector_to_camera_transform = TransformationMatrix.from_matrix(
        matrix=load_and_assert_affine_matrix(user_options.transform_yaml)
    )

    robot.MoveJ(capture_pose[0])
    camera = app.connect_camera()
    settings = _assisted_settings(camera, max_time_milliseconds=800)

    while True:
        print("\nPut the calibration board in the FOV of the camera.")
        input("Press enter to capture and touch. Press Ctr+C to exit.")
        try:
            print("Detecting the calibration board pose (upper left calibration board corner)")
            camera_to_calibration_board_transform = _capture_and_estimate_calibration_board_pose(camera, settings)

            print("Getting current robot pose")
            robot_base_to_end_effector_transform = TransformationMatrix.from_matrix(matrix=np.array(robot.Pose()).T)

            print("Calculating pose for the robot to approach the calibration board")
            touch_pose_offset = TransformationMatrix(translation=np.array([0, 0, 140]))
            approach_pose = (
                robot_base_to_end_effector_transform
                * end_effector_to_camera_transform
                * camera_to_calibration_board_transform
                * touch_pose_offset.inverse()
                * end_effector_to_tool_center_point_transform.inverse()
            )

            print("Calculating pose for robot to touch the calibration board")
            touch_pose = (
                robot_base_to_end_effector_transform
                * end_effector_to_camera_transform
                * camera_to_calibration_board_transform
                * end_effector_to_tool_center_point_transform.inverse()
            )

            print("Touching calibration board (upper left calibration board corner)")
            robot.MoveJ(Mat(approach_pose.as_matrix().tolist()))
            robot.MoveL(Mat(touch_pose.as_matrix().tolist()))
            time.sleep(1)
            robot.MoveJ(Mat(approach_pose.as_matrix().tolist()))
            robot.MoveJ(capture_pose[0])
        except RuntimeError as ex:
            print(ex)
            print("Please make sure calibration board is in FOV.")


if __name__ == "__main__":
    main()
