"""
This example shows how to utilize the result of Eye-in-Hand calibration to transform either a (picking) point
coordinates or the entire point cloud from the camera frame to the robot base frame.

The YAML files for this sample can be found under the main instructions for Zivid samples.
"""

from pathlib import Path
import numpy as np
import cv2

from sample_utils.paths import get_sample_data_path


def _assert_valid_matrix(file_name):
    """Check if YAML file is valid.

    Args:
        file_name: Path to YAML file.

    Returns None

    Raises:
        FileNotFoundError: If the YAML file specified by file_name cannot be opened.
        NameError: If the transformation matrix named 'PoseState' is not found in the file.
        ValueError: If the dimensions of the transformation matrix are not 4 x 4.
    """
    file_storage = cv2.FileStorage(str(file_name), cv2.FILE_STORAGE_READ)
    if not file_storage.open(str(file_name), cv2.FILE_STORAGE_READ):
        file_storage.release()
        raise FileNotFoundError(f"Could not open {file_name}")

    pose_state_node = file_storage.getNode("PoseState")

    if pose_state_node.empty():
        file_storage.release()
        raise NameError(f"PoseState not found in file {file_name}")

    shape = pose_state_node.mat().shape
    if shape[0] != 4 or shape[1] != 4:
        file_storage.release()
        raise ValueError(f"Expected 4x4 matrix in {file_name}, but got {shape[0]} x {shape[1]}")


def _read_transform(transform_file):
    """Read transformation matrix from a YAML file.

    Args:
        transform_file: Path to the YAML file.

    Returns:
        transform: Transformation matrix.

    """
    file_storage = cv2.FileStorage(str(transform_file), cv2.FILE_STORAGE_READ)
    transform = file_storage.getNode("PoseState").mat()
    file_storage.release()

    return transform


def _main():

    np.set_printoptions(precision=2)

    # Defining (picking) point in camera frame
    point_in_camera_frame = np.array([81.2, 18.0, 594.6, 1])
    print(f"Point coordinates in camera frame: {point_in_camera_frame[0:3]}")

    eye_in_hand_transform_file = Path() / get_sample_data_path() / "EyeInHandTransform.yaml"
    robot_transform_file = Path() / get_sample_data_path() / "RobotTransform.yaml"
    # Checking if YAML files are valid
    _assert_valid_matrix(eye_in_hand_transform_file)
    _assert_valid_matrix(robot_transform_file)

    print("Reading camera pose in end-effector frame (result of eye-in-hand calibration)")
    transform_end_effector_to_camera = _read_transform(eye_in_hand_transform_file)

    print("Reading end-effector pose in robot base frame")
    transform_base_to_end_effector = _read_transform(robot_transform_file)

    print("Computing camera pose in robot base frame")
    transform_base_to_camera = np.matmul(transform_base_to_end_effector, transform_end_effector_to_camera)

    print("Transforming (picking) point from camera to robot base frame")
    point_in_base_frame = np.matmul(transform_base_to_camera, point_in_camera_frame)

    print(f"Point coordinates in robot base frame: {point_in_base_frame[0:3]}")


if __name__ == "__main__":
    _main()
