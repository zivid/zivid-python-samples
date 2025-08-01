"""
Perform a touch test with a robot to verify Hand-Eye Calibration using the RoboDK interface.

The touch test is performed by a robot equipped with the Pointed Hand-Eye Verification Tool.
The robot touches the Zivid calibration object to verify hand-eye calibration.
The sample requires as follows:
- Type of calibration used (eye-in-hand or eye-to-hand)
- YAML file with Hand-Eye transformation matrix
- YAML file with Pointed Hand-Eye Verification Tool transformation matrix
- Capture pose target name used in RoboDK
- Calibration object used (Zivid calibration board or ArUco marker)

Note: Make sure to launch your RDK file and connect to the robot through RoboDK before running this script.

You can find the complete tutorial with a detailed explanation at: https://support.zivid.com/en/latest/academy/applications/hand-eye/hand-eye-calibration-verification-via-touch-test.html

More information about RoboDK is available at: https://robodk.com/doc/en/Getting-Started.html

"""

import argparse
import datetime
from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
import zivid
import zivid.experimental.calibration
from robodk import Mat
from robodk.robolink import Item
from zividsamples.display import display_rgb
from zividsamples.robodk_tools import connect_to_robot, get_robot_targets, set_robot_speed_and_acceleration
from zividsamples.save_load_matrix import load_and_assert_affine_matrix


def _assisted_capture(camera: zivid.Camera) -> zivid.Frame:
    """Acquire frame with capture assistant.

    Args:
        camera: Zivid camera

    Returns:
        frame: Zivid frame

    """
    suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
        max_capture_time=datetime.timedelta(milliseconds=800),
        ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
    )

    settings_list = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)

    return camera.capture_2d_3d(settings_list)


def _estimate_calibration_object_pose(frame: zivid.Frame, user_options: argparse.Namespace) -> np.ndarray:
    """Detect and estimate the pose of the calibration object.

    Args:
        frame: Zivid frame
        user_options: Input arguments

    Returns:
        calibration_object_pose: A 4x4 numpy array containing the calibration object pose

    """

    if user_options.calibration_object == "checkerboard":
        print("Detecting the Zivid calibration board pose (upper left checkerboard corner)")
        calibration_object_pose = zivid.calibration.detect_calibration_board(frame).pose().to_matrix()
    else:
        print("Detecting the ArUco marker pose (center of the marker)")

        calibration_object_pose = (
            zivid.calibration.detect_markers(frame, user_options.id, user_options.dictionary)
            .detected_markers()[0]
            .pose.to_matrix()
        )

    return calibration_object_pose


def _get_base_to_calibration_object_transform(
    user_options: argparse.Namespace,
    camera_to_calibration_object_transform: np.ndarray,
    robot: Item,
) -> np.ndarray:
    """Calculating the robot base to the calibration object transformation matrix.

    Args:
        user_options: Arguments from user that contain the type of hand-eye calibration done and the path to the transformation matrix that resulted from that calibration
        camera_to_calibration_object_transform: A 4x4 numpy array containing the calibration object pose in the camera frame
        robot: Robot item in open RoboDK rdk file

    Returns:
        base_to_calibration_object_transform: A 4x4 numpy array containing the calibration object pose in the robot base frame

    Raises:
        ValueError: If an invalid calibration type is selected

    """
    if user_options.eih:
        print("Loading current robot pose")
        base_to_flange_transform = np.array(robot.Pose()).T
        flange_to_camera_transform = load_and_assert_affine_matrix(Path(user_options.hand_eye_yaml))

        base_to_calibration_object_transform = (
            base_to_flange_transform @ flange_to_camera_transform @ camera_to_calibration_object_transform
        )
    elif user_options.eth:
        base_to_camera_transform = load_and_assert_affine_matrix(Path(user_options.hand_eye_yaml))

        base_to_calibration_object_transform = base_to_camera_transform @ camera_to_calibration_object_transform
    else:
        raise ValueError("Invalid calibration type. Please choose either eye-in-hand or eye-to-hand.")

    return base_to_calibration_object_transform


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


def _coordinate_system_line(
    bgra_image: np.ndarray,
    first_point: Tuple[int, int],
    second_point: Tuple[int, int],
    line_color: Tuple[int, int, int],
) -> None:
    """Draw a line on a BGRA image.

    Args:
        bgra_image: BGRA image.
        first_point: Pixel coordinates of the first end point.
        second_point: Pixel coordinates of the second end point.
        line_color: Line color.
    """

    line_thickness = 4
    line_type = cv2.LINE_8
    cv2.line(bgra_image, first_point, second_point, line_color, line_thickness, line_type)


def _zivid_camera_matrix_to_opencv_camera_matrix(camera_matrix: zivid.CameraIntrinsics.CameraMatrix) -> np.ndarray:
    """Convert camera matrix from Zivid to OpenCV.

    Args:
        camera_matrix: Camera matrix in Zivid format.

    Returns:
        camera_matrix_opencv: Camera matrix in OpenCV format.
    """

    return np.array(
        [[camera_matrix.fx, 0.0, camera_matrix.cx], [0.0, camera_matrix.fy, camera_matrix.cy], [0.0, 0.0, 1.0]]
    )


def _zivid_distortion_coefficients_to_opencv_distortion_coefficients(
    distortion_coeffs: zivid.CameraIntrinsics.Distortion,
) -> np.ndarray:
    """Convert distortion coefficients from Zivid to OpenCV.

    Args:
        distortion_coeffs: Camera distortion coefficients in Zivid format.

    Returns:
        distortion_coeffs_opencv: Camera distortion coefficients in OpenCV format.
    """

    return np.array(
        [distortion_coeffs.k1, distortion_coeffs.k2, distortion_coeffs.p1, distortion_coeffs.p2, distortion_coeffs.k3]
    )


def _move_point(
    origin_in_camera_frame: np.ndarray, offset_in_object_frame: np.ndarray, calibration_object_pose: np.ndarray
) -> np.ndarray:
    """Move a coordinate system origin point given a direction and an offset to create a coordinate system axis point.

    Args:
        origin_in_camera_frame: 3D coordinates of the coordinate system origin point.
        offset_in_object_frame: 3D coordinates of the offset to move the coordinate system origin point to.
        calibration_object_pose: Transformation matrix (calibration object in camera frame).

    Returns:
        translated_point: 3D coordinates of coordinate system axis point.
    """

    rotation_matrix = calibration_object_pose[:3, :3]
    offset_rotated = np.dot(rotation_matrix, offset_in_object_frame)
    return origin_in_camera_frame + offset_rotated


def _get_coordinate_system_points(
    frame: zivid.Frame, calibration_object_pose: np.ndarray, size_of_axis: float
) -> Dict[str, Tuple[int, int]]:
    """Get pixel coordinates of the coordinate system origin and axes.

    Args:
        frame: Zivid frame containing point cloud.
        calibration_object_pose: Transformation matrix (calibration object in camera frame).
        size_of_axis: Coordinate system axis length in mm.

    Returns:
        frame_points: Pixel coordinates of the coordinate system origin and axes.
    """

    intrinsics = zivid.experimental.calibration.estimate_intrinsics(frame)
    cv_camera_matrix = _zivid_camera_matrix_to_opencv_camera_matrix(intrinsics.camera_matrix)
    cv_dist_coeffs = _zivid_distortion_coefficients_to_opencv_distortion_coefficients(intrinsics.distortion)

    origin_position = np.array(
        [calibration_object_pose[0, 3], calibration_object_pose[1, 3], calibration_object_pose[2, 3]]
    )
    x_axis_direction = _move_point(origin_position, np.array([size_of_axis, 0.0, 0.0]), calibration_object_pose)
    y_axis_direction = _move_point(origin_position, np.array([0.0, size_of_axis, 0.0]), calibration_object_pose)
    z_axis_direction = _move_point(origin_position, np.array([0.0, 0.0, size_of_axis]), calibration_object_pose)

    points_to_project = np.array([origin_position, x_axis_direction, y_axis_direction, z_axis_direction])
    projected_points = cv2.projectPoints(points_to_project, np.zeros(3), np.zeros(3), cv_camera_matrix, cv_dist_coeffs)[
        0
    ]

    projected_points = projected_points.reshape(-1, 2)
    return {
        "origin_point": (int(projected_points[0][0]), int(projected_points[0][1])),
        "x_axis_point": (int(projected_points[1][0]), int(projected_points[1][1])),
        "y_axis_point": (int(projected_points[2][0]), int(projected_points[2][1])),
        "z_axis_point": (int(projected_points[3][0]), int(projected_points[3][1])),
    }


def _draw_coordinate_system(frame: zivid.Frame, calibration_object_pose: np.ndarray, bgra_image: np.ndarray) -> None:
    """Draw a coordinate system on a BGRA image.

    Args:
        frame: Zivid frame containing point cloud.
        calibration_object_pose: Transformation matrix (calibration object in camera frame).
        bgra_image: BGRA image.

    """

    size_of_axis = 30.0  # each axis has 30 mm of length

    print("Acquiring frame points")
    frame_points = _get_coordinate_system_points(frame, calibration_object_pose, size_of_axis)

    origin_point = frame_points["origin_point"]
    z = frame_points["z_axis_point"]
    y = frame_points["y_axis_point"]
    x = frame_points["x_axis_point"]

    print("Drawing Z axis")
    _coordinate_system_line(bgra_image, origin_point, z, (255, 0, 0))

    print("Drawing Y axis")
    _coordinate_system_line(bgra_image, origin_point, y, (0, 255, 0))

    print("Drawing X axis")
    _coordinate_system_line(bgra_image, origin_point, x, (0, 0, 255))

    display_rgb(rgb=cv2.cvtColor(bgra_image, cv2.COLOR_BGRA2RGB))


def _options() -> argparse.Namespace:
    """Function to read user arguments.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    type_group = parser.add_mutually_exclusive_group(required=True)
    type_group.add_argument("--eih", "--eye-in-hand", action="store_true", help="eye-in-hand configuration")
    type_group.add_argument("--eth", "--eye-to-hand", action="store_true", help="eye-to-hand configuration")
    parser.add_argument("--ip", required=True, help="IP address of the robot controller")
    parser.add_argument(
        "--target-keyword",
        required=True,
        help="RoboDK target name representing a robot pose at which the calibration object is in the field of view of the camera",
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
    subparsers = parser.add_subparsers(dest="calibration_object", required=True, help="Calibration object type")
    subparsers.add_parser("checkerboard", help="Verify using Zivid calibration board")
    marker_parser = subparsers.add_parser("marker", help="Verify using ArUco marker")
    marker_parser.add_argument(
        "--dictionary",
        required=True,
        choices=list(zivid.calibration.MarkerDictionary.valid_values()),
        help="Dictionary of the targeted ArUco marker",
    )
    marker_parser.add_argument(
        "--id", nargs=1, required=True, type=int, help="ID of ArUco marker to be used for verification"
    )

    return parser.parse_args()


def _main() -> None:

    app = zivid.Application()
    camera = app.connect_camera()

    user_options = _options()
    rdk, robot = connect_to_robot(user_options.ip)
    #  NOTE! Verify safe operation speeds and accelerations for your robot!
    set_robot_speed_and_acceleration(robot, speed=100, joint_speed=100, acceleration=50, joint_acceleration=50)

    print("Loading the Pointed Hand-Eye Verification Tool transformation matrix from a YAML file")
    tool_base_to_tool_tip_transform = load_and_assert_affine_matrix(Path(user_options.tool_yaml))

    if user_options.mounts_yaml:
        print("Loading the on-arm mounts transformation matrix from a YAML file")
        flange_to_tool_base_transform = load_and_assert_affine_matrix(Path(user_options.mounts_yaml))

        flange_to_tcp_transform = flange_to_tool_base_transform @ tool_base_to_tool_tip_transform
    else:
        flange_to_tcp_transform = tool_base_to_tool_tip_transform

    capture_pose = get_robot_targets(rdk, target_keyword=user_options.target_keyword)
    if not capture_pose:
        raise IndexError(
            "The list of poses retrieved from RoboDK is empty...\nMake sure that you have created a Capture Pose and that you introduced the right keyword for it."
        )
    robot.MoveJ(capture_pose[0])

    print("\nPlace the calibration object in the FOV of the camera.")
    input("Press enter to start.")

    while True:
        try:
            frame = _assisted_capture(camera)
            bgra_image = frame.point_cloud().copy_data("bgra_srgb")
            camera_to_calibration_object_transform = _estimate_calibration_object_pose(frame, user_options)

            print("Calculating the calibration object pose in robot base frame")
            base_to_calibration_object_transform = _get_base_to_calibration_object_transform(
                user_options,
                camera_to_calibration_object_transform,
                robot,
            )

            print("Calculating pose for robot to touch the calibration object")
            touch_pose = base_to_calibration_object_transform @ np.linalg.inv(flange_to_tcp_transform)

            print("Calculating pose for the robot to approach the calibration object")
            touch_pose_offset = np.identity(4)
            touch_pose_offset[2, 3] = -140
            approach_pose = touch_pose @ touch_pose_offset

            _draw_coordinate_system(frame, camera_to_calibration_object_transform, bgra_image)
            input("\nClose the window and press enter to the touch the calibration object...")

            print("Touching calibration object")
            robot.MoveJ(Mat(approach_pose.tolist()))
            robot.MoveL(Mat(touch_pose.tolist()))
            input("\nPress enter to pull back and return to the capture pose...")
            robot.MoveL(Mat(approach_pose.tolist()))
            robot.MoveJ(capture_pose[0])

            print("\nThe calibration object can be moved at this time.")
            answer = _yes_no_prompt("Perform another touch?")
            if answer == "n":
                break

        except RuntimeError as ex:
            print(ex)
            print("Please make sure calibration object is in FOV.")
            input("Press enter to continue.")


if __name__ == "__main__":
    _main()
