"""
Guide the robot to follow a path on the Zivid Calibration Board.

This code sample makes the robot perform a basic robot guidance task by following a linear path on the Zivid
Calibration Board. The path is projected onto the checkerboard by the projector, and subsequently followed by the tool
of the robot. The projected path forms a "Z" centered on the checkerboard.

The sample requires:
- A Zivid calibration board
- RoboDK and a supported robot
- YAML files that represent the transformation matrices for the tool and hand-eye calibration

Note: Make sure to launch RoboDK and connect to the robot before running this sample.

"""

import argparse
from typing import List

import cv2
import numpy as np
import robodk
import zivid
from zividsamples.robodk_tools import connect_to_robot, set_robot_speed_and_acceleration
from zividsamples.save_load_matrix import load_and_assert_affine_matrix


def _options() -> argparse.Namespace:
    """Function to read user arguments.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    type_group = parser.add_mutually_exclusive_group(required=True)
    type_group.add_argument("--eih", "--eye-in-hand", action="store_true", help="Camera mounted on-arm (eye-in-hand)")
    type_group.add_argument(
        "--eth", "--eye-to-hand", action="store_true", help="Camera mounted stationary (eye-to-hand)"
    )

    parser.add_argument("--ip", required=True, help="IP address of the robot controller")
    parser.add_argument(
        "--tool-yaml",
        required=True,
        help="Path to YAML file that contains the tool tip transformation matrix (tool tip in robot flange frame)",
    )
    parser.add_argument(
        "--hand-eye-yaml",
        required=True,
        help="Path to the YAML file that contains the hand-eye transformation matrix",
    )

    return parser.parse_args()


def _checkerboard_grid() -> List[np.ndarray]:
    """Create a list of points corresponding to the checkerboard corners in a Zivid calibration board.

    Returns:
        List of 3D points for each corner in the checkerboard, in the checkerboard frame

    """
    x = np.arange(0, 7) * 30.0
    y = np.arange(0, 6) * 30.0

    xx, yy = np.meshgrid(x, y)
    z = np.zeros_like(xx)

    points = np.dstack((xx, yy, z)).reshape(-1, 3)

    return list(points)


def _transform_points(points: List[np.ndarray], transform: np.ndarray) -> List[np.ndarray]:
    """Perform a homogenous transformation to every point in 'points' and return the transformed points.

    Args:
        points: List of 3D points to be transformed
        transform: Transformation matrix (4x4)

    Returns:
        List of transformed 3D points

    """
    rotation_matrix = transform[:3, :3]
    translation_vector = transform[:3, 3]

    transformed_points = []
    for point in points:
        transformed_points.append(rotation_matrix @ point + translation_vector)

    return transformed_points


def _points_to_poses(points: List[np.ndarray], rotation_matrix: np.ndarray) -> List[np.ndarray]:
    """Convert a list of 3D points to a list of poses (4x4) using the given rotation matrix.

    Args:
        points: List of 3D points
        rotation_matrix: Rotation matrix (3x3)

    Returns:
        List of poses (4x4) corresponding to each point with the given rotation matrix

    """
    poses = []
    for point in points:
        pose = np.eye(4)
        pose[:3, :3] = rotation_matrix
        pose[:3, 3] = point

        poses.append(pose)

    return poses


def _zivid_logo_from_grid() -> List[int]:
    """Return indices of the grid points that form the Zivid logo.

    Returns:
        List of indices of the grid points that form the Zivid logo

    """
    return [0, 6, 13, 30, 34, 41, 35, 28, 11, 7, 0]


def _generate_tool_poses_from_checkerboard(
    camera: zivid.Camera, base_to_camera_transform: np.ndarray
) -> List[np.ndarray]:
    """Generate a tool path as a list of poses in the camera frame using the checkerboard.

    Args:
        camera: Zivid camera
        base_to_camera_transform: Camera pose in robot base frame (4x4)

    Raises:
        RuntimeError: If the calibration board is not detected

    Returns:
        List of poses (4x4) for the tool path in the robot base

    """
    detection_result = zivid.calibration.detect_calibration_board(camera)
    if not detection_result.valid():
        raise RuntimeError(f"Calibration board not detected! {detection_result.status_description()}")

    camera_to_checkerboard_transform = detection_result.pose().to_matrix()
    base_to_checkerboard_transform = base_to_camera_transform @ camera_to_checkerboard_transform

    grid_points_in_checkerboard_frame = _checkerboard_grid()
    grid_points_in_base_frame = _transform_points(grid_points_in_checkerboard_frame, base_to_checkerboard_transform)
    grid_poses_in_base_frame = _points_to_poses(grid_points_in_base_frame, base_to_checkerboard_transform[:3, :3])

    tool_poses_in_base_frame = [grid_poses_in_base_frame[idx] for idx in _zivid_logo_from_grid()]

    return tool_poses_in_base_frame


def _draw_tool_path(image: np.ndarray, positions: List[List[float]]) -> None:
    """Draw lines between each subsequent position in the image.

    Args:
        image: Image to draw lines in
        positions: List of 2D positions (X,Y) to draw lines between

    """
    for current_position, next_position in zip(positions[:-1], positions[1:]):  # noqa: B905
        if np.nan not in current_position and np.nan not in next_position:
            current_point = (round(current_position[0]), round(current_position[1]))
            next_point = (round(next_position[0]), round(next_position[1]))

            cv2.line(image, current_point, next_point, color=(0, 255, 0, 255), thickness=1)


def _projected_tool_path(camera: zivid.Camera, tool_poses_in_camera_frame: List[np.ndarray]) -> np.ndarray:
    """Returns projected tool path on the checkerboard as a projector image.

    Args:
        camera: Zivid camera
        tool_poses_in_camera_frame: List of poses (4x4) for the tool path

    Returns:
        Projected tool path on the checkerboard as a projector image

    """
    tool_points_in_camera_frame = [pose[:3, 3] for pose in tool_poses_in_camera_frame]
    projector_pixels = zivid.projection.pixels_from_3d_points(camera, tool_points_in_camera_frame)

    projector_resolution = zivid.projection.projector_resolution(camera)

    background_color = (0, 0, 0, 255)
    projector_image = np.full(
        (projector_resolution[0], projector_resolution[1], len(background_color)), background_color, dtype=np.uint8
    )

    _draw_tool_path(projector_image, projector_pixels)

    return projector_image


def _approach_target_pose(robot: robodk.robolink.Item, target_pose: np.ndarray, offset: np.ndarray) -> None:
    """Move the robot to an approach pose near the target pose.

    Args:
        robot: RoboDK robot
        target_pose: Target pose (4x4) to approach
        offset: Offset vector (X,Y,Z) to add to the target pose

    """
    target_pose_offset = np.eye(4)
    target_pose_offset[:3, 3] = offset
    approach_pose = target_pose @ target_pose_offset

    robot.MoveJ(robodk.Mat(approach_pose.tolist()))


def _follow_linear_path(robot: robodk.robolink.Item, flange_waypoints: List[np.ndarray]) -> None:
    """Follow the path given in 'flange_waypoints' in linear mode.

    Args:
        robot: RoboDK robot
        flange_waypoints: List of poses (4x4) for the flange path in robot base frame

    """
    for waypoint in flange_waypoints:
        robot.MoveL(robodk.Mat(waypoint.tolist()))


def _main() -> None:
    app = zivid.Application()

    user_options = _options()

    print("Connecting to robot")
    robot = connect_to_robot(user_options.ip)[1]
    robot.setJointsHome(robot.Joints())
    set_robot_speed_and_acceleration(robot, speed=120, joint_speed=30, acceleration=120, joint_acceleration=120)

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Generating tool path from the checkerboard")
    flange_to_tcp_transform = load_and_assert_affine_matrix(user_options.tool_yaml)
    base_to_flange_transform = np.array(robot.Pose()).T

    if user_options.eih:
        flange_to_camera_transform = load_and_assert_affine_matrix(user_options.hand_eye_yaml)
        base_to_camera_transform = base_to_flange_transform @ flange_to_camera_transform
    else:
        base_to_camera_transform = load_and_assert_affine_matrix(user_options.hand_eye_yaml)

    tool_poses_in_base_frame = _generate_tool_poses_from_checkerboard(camera, base_to_camera_transform)
    flange_poses_in_base_frame = [
        tool_pose_in_base_frame @ np.linalg.inv(flange_to_tcp_transform)
        for tool_pose_in_base_frame in tool_poses_in_base_frame
    ]

    print("Displaying the tool path on the checkerboard")
    tool_poses_in_camera_frame = [
        np.linalg.inv(base_to_camera_transform) @ tool_pose_in_base_frame
        for tool_pose_in_base_frame in tool_poses_in_base_frame
    ]

    projector_image = _projected_tool_path(camera, tool_poses_in_camera_frame)
    projected_image_handle = zivid.projection.show_image_bgra(camera, projector_image)
    input("Press enter to start following the path ...")

    if user_options.eih:
        projected_image_handle.stop()

    _approach_target_pose(robot, flange_poses_in_base_frame[0], offset=np.array([0, 0, -100]))

    _follow_linear_path(robot, flange_poses_in_base_frame)

    robot.MoveJ(robot.JointsHome())


if __name__ == "__main__":
    _main()
