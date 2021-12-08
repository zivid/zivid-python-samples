"""
Script to generate a dataset and perform hand-eye calibration using the RoboDK virtual interface and robot control
The script communicates with the robot over TCP through the RoboDK interface
More information about RoboDK:
https://robodk.com/doc/en/Getting-Started.html

The entire sample also has two additional filess:
    - an .rdk sample environment using a UR5
    - a robot model file of a UR5

To use the sample with your robot an rdk file needs to be created using a model of your robot.
Each pose will need to be created or modified to fit your scene. This is done using the RoboDK GUI.

Further explanation of this sample is found in our knowledge base:
(Will add replacement link)
"""

import argparse
from pathlib import Path
import time
import datetime

import cv2
import numpy as np
from robodk import *

import zivid
from zivid.capture_assistant import SuggestSettingsParameters
from robolink import Robolink


def _options():
    """Function for taking in arguments from user
    Returns:
        Arguments from user
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode_group = parser.add_mutually_exclusive_group(required=True)

    mode_group.add_argument("--eih", "--eye-in-hand", action="store_true", help="eye-in-hand calibration")
    mode_group.add_argument("--eth", "--eye-to-hand", action="store_true", help="eye-to-hand calibration")

    parser.add_argument("--ip", required=True, help="IP address to robot")
    parser.add_argument(
        "--targets", required=True, help="Name of targets to use for calibration, i.e. 'target', 'wall_target'"
    )

    return parser.parse_args()


def assistedCapture(camera, maxtime=4000):
    """
    Capture image with Zivid camera

    Args:
        camera: Zivid camera
        maxtime: Maximum capture time allowed
    Returns:
        Zivid frame
    """

    suggest_settings_parameters = SuggestSettingsParameters(
        max_capture_time=datetime.timedelta(milliseconds=maxtime),
        ambient_light_frequency=SuggestSettingsParameters.AmbientLightFrequency.none,
    )

    settings_list = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)

    frame = camera.capture(settings_list)
    return frame


def _get_frame_and_transform_matrix(robot, cam: zivid.Camera):
    """Capture image with Zivid camera and read robot pose
    Args:
        robot: robolink robot item
        cam: Zivid camera
    Returns:
        Zivid frame
        4x4 tranformation matrix
    """
    frame = assistedCapture(cam)
    transform = np.array(robot.Pose()).T
    return frame, transform


def pose_from_datastring(datastring: str):
    """Extract pose from yaml file saved by openCV
    Args:
        datastring: String of text from .yaml file
    Returns:
        Robotic pose as zivid Pose class
    """
    string = datastring.split("data:")[-1].strip().strip("[").strip("]")
    pose_matrix = np.fromstring(string, dtype=np.float64, count=16, sep=",").reshape((4, 4))
    return zivid.calibration.Pose(pose_matrix)


def _save_hand_eye_results(save_dir: Path, transform: np.array, residuals: list):
    """Save transformation and residuals to folder
    Args:
        save_dir: Path to where data will be saved
        transform: 4x4 transformation matrix
        residuals: List of residuals
    Returns:
        None
    """
    file_storage_transform = cv2.FileStorage(str(save_dir / "transformation.yaml"), cv2.FILE_STORAGE_WRITE)
    file_storage_transform.write("PoseState", transform)
    file_storage_transform.release()

    file_storage_residuals = cv2.FileStorage(str(save_dir / "residuals.yaml"), cv2.FILE_STORAGE_WRITE)
    residual_list = []
    for res in residuals:
        tmp = list([res.rotation(), res.translation()])
        residual_list.append(tmp)

    file_storage_residuals.write(
        "Per pose residuals for rotation in deg and translation in mm",
        np.array(residual_list),
    )
    file_storage_residuals.release()


def _save_zdf_and_pose(save_dir: Path, image_num: int, frame: zivid.Frame, transform: np.array):
    """Save data to folder
    Args:
        save_dir: Directory to save data
        image_num: Image number
        frame: Point cloud stored as .zdf
        transform: 4x4 transformation matrix
    Returns:
        None
    """
    frame.save(save_dir / f"img{image_num:02d}.zdf")

    file_storage = cv2.FileStorage(str(save_dir / f"pos{image_num:02d}.yaml"), cv2.FILE_STORAGE_WRITE)
    file_storage.write("PoseState", transform)
    file_storage.release()


def _verify_good_capture(frame: zivid.Frame):
    """Verify that checkerboard featurepoints are detected in the frame
    Args:
        frame: Zivid frame containing point cloud
    Raises:
        RuntimeError: If no feature points are detected in frame
    Returns:
        None
    """
    detected_features = zivid.calibration.detect_feature_points(frame.point_cloud())
    if not detected_features.valid():
        raise RuntimeError("Failed to detect feature points from captured frame.")


def _capture_one_frame_and_robot_pose(robot, cam: zivid.Camera, save_dir: Path, image_num: int, next_target):
    """Capture 3D image and robot pose for a given robot posture,
    then signals robot to move to next posture
    Args:
        robot: robolink robot item
        cam: Zivid camera
        save_dir: Path to where data will be saved
        image_num: Image number
        next target: target from roboDK to move to
    Returns:
        None
    """
    robot.WaitMove()
    time.sleep(0.05)
    frame, transform = _get_frame_and_transform_matrix(robot, cam)
    _save_zdf_and_pose(save_dir, image_num, frame, transform)
    # Move and verify capture at the same time.
    if next_target is not None:
        robot.MoveJ(next_target, blocking=False)
    _verify_good_capture(frame)
    print(f"Image and pose #{image_num} saved")


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


def perform_hand_eye_calibration(mode: str, data_dir: Path):
    """Perform hand-eye calibration based on mode
    Args:
        mode: Calibration mode, eye-in-hand or eye-to-hand
        data_dir: Path to dataset
    Returns:
        4x4 transformation matrix
        List of residuals
    Raises:
        RuntimeError: If no feature points are detected
        ValueError: If calibration mode is invalid
    """
    # setup zivid
    app = zivid.Application()

    calibration_inputs = []
    idata = 1
    while True:
        frame_file = data_dir / f"img{idata:02d}.zdf"
        pose_file = data_dir / f"pos{idata:02d}.yaml"

        if frame_file.is_file() and pose_file.is_file():

            print(f"Detect feature points from img{idata:02d}.zdf")
            point_cloud = zivid.Frame(frame_file).point_cloud()

            detected_features = zivid.calibration.detect_feature_points(point_cloud)

            if not detected_features.valid():
                raise RuntimeError(f"Failed to detect feature points from frame {frame_file}")

            print(f"Read robot pose from pos{idata:02d}.yaml")
            with open(pose_file) as file:
                pose = pose_from_datastring(file.read())

            detection_result = zivid.calibration.HandEyeInput(pose, detected_features)
            calibration_inputs.append(detection_result)
        else:
            break

        idata += 1

    print(f"\nPerform {mode} calibration")

    if mode == "eye-in-hand":
        calibration_result = zivid.calibration.calibrate_eye_in_hand(calibration_inputs)
    elif mode == "eye-to-hand":
        calibration_result = zivid.calibration.calibrate_eye_to_hand(calibration_inputs)
    else:
        raise ValueError(f"Invalid calibration mode: {mode}")

    transform = calibration_result.transform()
    residuals = calibration_result.residuals()

    print("\n\nTransform: \n")
    np.set_printoptions(precision=5, suppress=True)
    print(transform)

    print("\n\nResiduals: \n")
    for res in residuals:
        print(f"Rotation: {res.rotation():.6f}   Translation: {res.translation():.6f}")

    return transform, residuals


# def _assert_valid_matrix(file_name):
#     """Check if YAML file is valid.

#     Args:
#         file_name: Path to YAML file.

#     Returns:
#         None

#     Raises:
#         FileNotFoundError: If the YAML file specified by file_name cannot be opened.
#         NameError: If the transformation matrix named 'PoseState' is not found in the file.
#         ValueError: If the dimensions of the transformation matrix are not 4 x 4.
#     """
#     file_storage = cv2.FileStorage(str(file_name), cv2.FILE_STORAGE_READ)
#     if not file_storage.open(str(file_name), cv2.FILE_STORAGE_READ):
#         file_storage.release()
#         raise FileNotFoundError(f"Could not open {file_name}")

#     pose_state_node = file_storage.getNode("PoseState")

#     if pose_state_node.empty():
#         file_storage.release()
#         raise NameError(f"PoseState not found in file {file_name}")

#     shape = pose_state_node.mat().shape
#     if shape[0] != 4 or shape[1] != 4:
#         file_storage.release()
#         raise ValueError(f"Expected 4x4 matrix in {file_name}, but got {shape[0]} x {shape[1]}")


# def assert_matrix_and_read_transform(file_name):
#     """Check if YAML file is valid and read transformation matrix from it.
#     Args:
#         file_name: Path to YAML file.
#     Returns:
#         transform: Transformation matrix.
#     """
#     _assert_valid_matrix(file_name)
#     T_hand_to_eye = _read_transform(file_name)
#     return T_hand_to_eye
