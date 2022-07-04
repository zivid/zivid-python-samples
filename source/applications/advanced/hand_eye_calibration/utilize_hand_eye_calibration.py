"""
Transform single data point or entire point cloud from camera frame to robot base frame using Hand-Eye calibration
matrix.

This example shows how to utilize the result of Hand-Eye calibration to transform either (picking) point coordinates
or the entire point cloud from the camera frame to the robot base frame.

For both Eye-To-Hand and Eye-In-Hand, there is a Zivid gem placed approx. 500 mm away from the robot base (see below).
The (picking) point is the Zivid gem centroid, defined as image coordinates in the camera frame and hard-coded
in this code example. Open the ZDF files in Zivid Studio to inspect the gem's 2D and corresponding 3D coordinates.

Eye-To-Hand
- ZDF file: ZividGemEyeToHand.zdf
- 2D image coordinates: (1035,255)
- Corresponding 3D coordinates: (37.77 -145.92 1227.1)
- Corresponding 3D coordinates (robot base frame): (-12.4  514.37 -21.79)

Eye-In-Hand:
- ZDF file: ZividGemEyeInHand.zdf
- 2D image coordinates: (1460,755)
- Corresponding 3D coordinates (camera frame): (83.95  28.84 305.7)
- Corresponding 3D coordinates (robot base frame): (531.03  -5.44 164.6)

For verification, check that the Zivid gem centroid 3D coordinates are the same as above after the transformation.

The YAML files for this sample can be found under the main instructions for Zivid samples.
"""

from pathlib import Path

import cv2
import numpy as np
import zivid
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

    while True:
        robot_camera_configuration = input(
            "Enter type of calibration, eth (for eye-to-hand) or eih (for eye-in-hand):"
        ).strip()

        if robot_camera_configuration.lower() == "eth":

            file_name = "ZividGemEyeToHand.zdf"

            # The (picking) point is defined as image coordinates in camera frame. It is hard-coded for the
            # ZividGemEyeToHand.zdf (1035,255) X: 37.77 Y: -145.92 Z: 1227.1
            image_coordinate_x = 1035
            image_coordinate_y = 255

            eye_to_hand_transform_file = Path() / get_sample_data_path() / "EyeToHandTransform.yaml"
            # Checking if YAML files are valid
            _assert_valid_matrix(eye_to_hand_transform_file)

            print("Reading camera pose in robot base frame (result of eye-to-hand calibration)")
            transform_base_to_camera = _read_transform(eye_to_hand_transform_file)

            break

        if robot_camera_configuration.lower() == "eih":

            file_name = "ZividGemEyeInHand.zdf"

            # The (picking) point is defined as image coordinates in camera frame. It is hard-coded for the
            # ZividGemEyeInHand.zdf (1460,755) X: 83.95 Y: 28.84 Z: 305.7
            image_coordinate_x = 1460
            image_coordinate_y = 755

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

            break

        print("Entered unknown Hand-Eye calibration type")

    with zivid.Application():

        data_file = Path() / get_sample_data_path() / file_name
        print(f"Reading point cloud from file: {data_file}")
        frame = zivid.Frame(data_file)
        point_cloud = frame.point_cloud()

        while True:
            command = input("Enter command, s (to transform single point) or p (to transform point cloud): ").strip()

            if command.lower() == "s":

                print("Transforming single point")

                xyz = point_cloud.copy_data("xyz")

                point_in_camera_frame = np.array(
                    [
                        xyz[image_coordinate_y, image_coordinate_x, 0],
                        xyz[image_coordinate_y, image_coordinate_x, 1],
                        xyz[image_coordinate_y, image_coordinate_x, 2],
                        1,
                    ]
                )
                print(f"Point coordinates in camera frame: {point_in_camera_frame[0:3]}")

                print("Transforming (picking) point from camera to robot base frame")
                point_in_base_frame = np.matmul(transform_base_to_camera, point_in_camera_frame)

                print(f"Point coordinates in robot base frame: {point_in_base_frame[0:3]}")

                break

            if command.lower() == "p":

                print("Transforming point cloud")

                point_cloud.transform(transform_base_to_camera)

                save_file = "ZividGemTransformed.zdf"
                print(f"Saving frame to file: {save_file}")
                frame.save(save_file)

                break

            print("Entered unknown command")


if __name__ == "__main__":
    _main()
