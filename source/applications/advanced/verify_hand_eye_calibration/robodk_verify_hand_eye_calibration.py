"""
Perform a touch test with a robot to verify Hand-Eye Calibration using the RoboDK interface.

The touch test is performed by a robot equipped with the Pointed Hand-Eye Verification Tool.
The robot touches a corner of the checkerboard on the Zivid calibration board to verify hand-eye calibration.
The sample requires as follows:
- Type of calibration used (eye-in-hand or eye-to-hand)
- YAML file with Hand-Eye transformation
- YAML file with Pointed Hand-Eye Verification Tool transformation
- Capture pose target name used in RoboDK

Note: Make sure to launch your RDK file and connect to the robot through RoboDK before running this script.

You can find the complete tutorial with a detailed explanation at: https://support.zivid.com/en/latest/academy/applications/hand-eye/hand-eye-calibration-verification-via-touch-test.html

More information about RoboDK is available at: https://robodk.com/doc/en/Getting-Started.html

"""

import argparse
import datetime

import numpy as np
import zivid
from robodk import Mat
from robodk.robolink import Item
from sample_utils.robodk_tools import connect_to_robot, get_robot_targets, set_robot_speed_and_acceleration
from sample_utils.save_load_matrix import load_and_assert_affine_matrix


def _capture_and_estimate_calibration_board_pose(camera: zivid.Camera) -> np.ndarray:
    """Capture an image with the Zivid camera using capture assistant, detecting, and estimating the pose of the calibration board.

    Args:
        camera: Zivid camera

    Returns:
        calibration_board_pose: A 4x4 numpy array containing the calibration board pose

    """
    suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
        max_capture_time=datetime.timedelta(milliseconds=800),
        ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
    )

    settings_list = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)
    frame = camera.capture(settings_list)

    calibration_board_pose = zivid.calibration.detect_feature_points(frame).pose().to_matrix()

    return calibration_board_pose


def _get_robot_base_to_calibration_board_transform(
    user_options: argparse.Namespace,
    camera_to_calibration_board_transform: np.ndarray,
    robot: Item,
) -> np.ndarray:
    """Calculating the robot base to the calibration board transform matrix.

    Args:
        user_options: Arguments from user that contain the type of hand-eye calibration done and the path to the matrix that resulted from that calibration
        camera_to_calibration_board_transform: A 4x4 numpy array containing the calibration board pose in the camera frame
        robot: Robot item in open RoboDK rdk file

    Returns:
        robot_base_to_calibration_board_transform: A 4x4 numpy array containing the calibration board pose in the robot base frame

    """
    if user_options.eih:
        print("Loading current robot pose")
        robot_base_to_flange_transform = np.array(robot.Pose()).T
        flange_to_camera_transform = load_and_assert_affine_matrix(user_options.hand_eye_yaml)

        robot_base_to_calibration_board_transform = (
            robot_base_to_flange_transform @ flange_to_camera_transform @ camera_to_calibration_board_transform
        )
    if user_options.eth:
        robot_base_to_camera_transform = load_and_assert_affine_matrix(user_options.hand_eye_yaml)

        robot_base_to_calibration_board_transform = (
            robot_base_to_camera_transform @ camera_to_calibration_board_transform
        )

    return robot_base_to_calibration_board_transform


def _yes_no_prompt(question: str) -> str:
    """Gets a yes or no answer to a given question.

    Args:
        question: A question what requires a yes or no answer

    Returns:
        String containing 'y' or 'n'

    """
    while True:
        response = input(f"{question} (y/n): ")
        if response in ["n", "N", "y", "Y"]:
            return response.lower()
        print("Invalid response. Please respond with either 'y' or 'n'.")


def _options() -> argparse.Namespace:
    """Function to read user arguments.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    type_group = parser.add_mutually_exclusive_group(required=True)
    type_group.add_argument("--eih", "--eye-in-hand", action="store_true", help="eye-in-hand calibration")
    type_group.add_argument("--eth", "--eye-to-hand", action="store_true", help="eye-to-hand calibration")

    parser.add_argument("--ip", required=True, help="IP address of the robot controller")
    parser.add_argument(
        "--target-keyword",
        required=True,
        help="RoboDK target name representing a robot pose at which the calibration board is in the field of view of the camera",
    )
    parser.add_argument(
        "--tool-yaml",
        required=True,
        help="Path to YAML file that represents the Pointed Hand-Eye Verification Tool transformation matrix",
    )
    parser.add_argument(
        "--mounts-yaml",
        required=False,
        help="Path to YAML file that represents the on-arm mounts transformation matrix",
    )
    parser.add_argument(
        "--hand-eye-yaml",
        required=True,
        help="Path to the YAML file that contains the Hand-Eye transformation matrix",
    )

    return parser.parse_args()


def main() -> None:
    app = zivid.Application()
    camera = app.connect_camera()

    user_options = _options()
    rdk, robot = connect_to_robot(user_options.ip)
    set_robot_speed_and_acceleration(robot, speed=120, joint_speed=120, acceleration=120, joint_acceleration=120)

    print("Loading the Pointed Hand-Eye Verification Tool transformation matrix from a YAML file")
    pointed_hand_eye_verification_tool_matrix = load_and_assert_affine_matrix(user_options.tool_yaml)

    if user_options.mounts_yaml:
        print("Loading the on-arm mounts transformation matrix from a YAML file")
        flange_to_on_arm_mounts_transform = load_and_assert_affine_matrix(user_options.mounts_yaml)

        tcp = flange_to_on_arm_mounts_transform @ pointed_hand_eye_verification_tool_matrix
    else:
        tcp = pointed_hand_eye_verification_tool_matrix

    capture_pose = get_robot_targets(rdk, target_keyword=user_options.target_keyword)
    if not capture_pose:
        raise IndexError(
            "The list of poses retrieved from RoboDK is empty...\nMake sure that you have created a Capture Pose and that you introduced the right keyword for it."
        )
    robot.MoveJ(capture_pose[0])

    print("\nPlace the calibration board in the FOV of the camera.")
    input("Press enter to start.")

    while True:
        try:
            print("Detecting the calibration board pose (upper left checkerboard corner)")
            camera_to_calibration_board_transform = _capture_and_estimate_calibration_board_pose(camera)

            print("Calculating the calibration board pose in robot base frame")
            robot_base_to_calibration_board_transform = _get_robot_base_to_calibration_board_transform(
                user_options,
                camera_to_calibration_board_transform,
                robot,
            )

            print("Calculating pose for robot to touch the calibration board")
            touch_pose = robot_base_to_calibration_board_transform @ np.linalg.inv(tcp)

            print("Calculating pose for the robot to approach the calibration board")
            touch_pose_offset = np.identity(4)
            touch_pose_offset[2, 3] = -140
            approach_pose = touch_pose @ touch_pose_offset

            print("Touching calibration board (upper left checkerboard corner)")
            robot.MoveJ(Mat(approach_pose.tolist()))
            robot.MoveL(Mat(touch_pose.tolist()))
            input("\nPress enter to pull back and return to the capture pose...")
            robot.MoveL(Mat(approach_pose.tolist()))
            robot.MoveJ(capture_pose[0])

            print("\nThe board can be moved at this time.")
            answer = _yes_no_prompt("Perform another touch?")
            if answer == "n":
                break

        except RuntimeError as ex:
            print(ex)
            print("Please make sure calibration board is in FOV.")
            input("Press enter to continue.")


if __name__ == "__main__":
    main()
