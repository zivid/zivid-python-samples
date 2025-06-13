"""
Generate a dataset and perform hand-eye calibration using the Robodk interface.

You must modify each robot pose to your scene using the RoboDK GUI interface.

More information about RoboDK:
https://robodk.com/doc/en/Getting-Started.html

The sample comes with a .rdk sample environment file using a Universal Robots UR5e robot.

To use the sample with your robot an rdk file needs to be created using a model of your robot.
Each pose will need to be created or modified to fit your scene using the RoboDK GUI.
For finding the best poses for hand-eye check out:
https://support.zivid.com/latest/academy/applications/hand-eye/hand-eye-calibration-process.html
Make sure to launch your RDK file and connect to robot through Robodk before running this script.

"""

import argparse
import datetime
import time
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import zivid
from robodk.robolink import Item
from zivid.capture_assistant import SuggestSettingsParameters
from zividsamples.robodk_tools import connect_to_robot, get_robot_targets, set_robot_speed_and_acceleration
from zividsamples.save_load_matrix import assert_affine_matrix_and_save, load_and_assert_affine_matrix


def _generate_directory() -> Path:
    """Generate directory where dataset will be stored.

    Returns:
        Directory to where data will be saved

    """
    name = input("Input desired name of dataset directory: (enter for default: /datasets/handeye) ")
    directory_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") if name == "" else name
    directory_path = Path(__file__).absolute().parent / "datasets/handeye" / directory_name
    print(f"Directory generated at {directory_path}")
    if not directory_path.is_dir():
        directory_path.mkdir(parents=True)

    return directory_path


def _get_frame_and_transform(robot: Item, camera: zivid.Camera) -> Tuple[zivid.Frame, np.ndarray]:
    """Capture image with Zivid camera and read robot pose.

    Args:
        robot: Robot item in open RoboDK rdk file
        camera: Zivid camera

    Returns:
        Zivid frame
        Transformation matrix (4x4)

    """
    frame = _assisted_capture(camera)
    transform = np.array(robot.Pose()).T
    return frame, transform


def _save_point_cloud_and_pose(
    save_directory: Path,
    image_and_pose_iterator: int,
    frame: zivid.Frame,
    transform: np.ndarray,
) -> None:
    """Save data to directory.

    Args:
        save_directory: Path to where data will be saved
        image_and_pose_iterator: Image number
        frame: Point cloud stored as ZDF
        transform: Transformation matrix (4x4)

    """
    frame.save(save_directory / f"img{image_and_pose_iterator:02d}.zdf")

    assert_affine_matrix_and_save(transform, save_directory / f"pos{image_and_pose_iterator:02d}.yaml")


def _verify_good_capture(frame: zivid.Frame, user_options: argparse.Namespace) -> None:
    """Verify that calibration object feature points are detected in the frame.

    Args:
        frame: Zivid frame containing point cloud
        user_options: Input arguments

    Raises:
        RuntimeError: If no feature points are detected in frame

    """
    if user_options.calibration_object == "checkerboard":
        detected_features = zivid.calibration.detect_calibration_board(frame)
        if not detected_features.valid():
            raise RuntimeError("Failed to detect Zivid checkerboard from captured frame.")
    if user_options.calibration_object == "marker":
        detected_features = zivid.calibration.detect_markers(frame, user_options.ids, user_options.dictionary)
        if not detected_features.valid():
            raise RuntimeError("Failed to detect any ArUco markers from captured frame.")


def _capture_one_frame_and_robot_pose(
    *,
    robot: Item,
    camera: zivid.Camera,
    save_directory: Path,
    image_and_pose_iterator: int,
    next_target: Item,
    user_options: argparse.Namespace,
) -> None:
    """Captures and saves point cloud at a given robot pose, saves robot pose,
    then signals the robot to move to the next pose.

    Args:
        robot: Robot item in open RoboDK rdk file
        camera: Zivid camera
        save_directory: Path to where data will be saved
        image_and_pose_iterator: Counter for point cloud and pose acquisition sequence
        next_target: Next pose the robot should move to in sequence
        user_options: Input arguments

    """
    robot.WaitMove()
    # Make sure the robot is completely stopped and no miniscule movement is occurring
    time.sleep(0.2)

    frame, transform = _get_frame_and_transform(robot, camera)

    _save_point_cloud_and_pose(save_directory, image_and_pose_iterator, frame, transform)
    # Verifying capture from previous pose while moving to new pose
    if next_target is not None:
        robot.MoveJ(next_target, blocking=False)
    _verify_good_capture(frame, user_options)
    print(f"Image and pose #{image_and_pose_iterator} saved")


def _save_hand_eye_results(save_directory: Path, transform: np.ndarray, residuals: List) -> None:
    """Save transformation and residuals to directory.

    Args:
        save_directory: Path to where data will be saved
        transform: Transformation matrix (4x4)
        residuals: List of residuals

    """
    assert_affine_matrix_and_save(transform, save_directory / "handEyeTransform.yaml")

    file_storage_residuals = cv2.FileStorage(str(save_directory / "residuals.yaml"), cv2.FILE_STORAGE_WRITE)
    residual_list = []
    for res in residuals:
        tmp = list([res.rotation(), res.translation()])
        residual_list.append(tmp)

    file_storage_residuals.write(
        "Per pose residuals for rotation in deg and translation in mm",
        np.array(residual_list),
    )
    file_storage_residuals.release()


def generate_hand_eye_dataset(
    app: zivid.application, robot: Item, targets: List, user_options: argparse.Namespace
) -> Path:
    """Generate dataset of pairs of robot poses and point clouds containing calibration target.
    This dataset is composed of pairs of YML and ZDF files respectively.

    Args:
        app: Zivid application instance
        robot: Robot item in open RoboDK rdk file
        targets: List of roboDK targets (poses)
        user_options: Input arguments

    Returns:
        Path: Save_directory for where data will be saved

    """
    num_targets = len(targets)
    robot.MoveJ(targets.pop(0))
    camera = app.connect_camera()
    save_directory = _generate_directory()
    image_and_pose_iterator = 1
    while not image_and_pose_iterator > num_targets:
        print(f"Capturing calibration object at robot pose {num_targets - len(targets)}")
        _capture_one_frame_and_robot_pose(
            robot=robot,
            camera=camera,
            save_directory=save_directory,
            image_and_pose_iterator=image_and_pose_iterator,
            next_target=targets.pop(0) if targets else None,
            user_options=user_options,
        )
        image_and_pose_iterator += 1

    print(f"\n Data saved to: {save_directory}")

    return save_directory


def _assisted_capture(camera: zivid.Camera, max_time_milliseconds: int = 800) -> zivid.Frame:
    """Capturing image with Zivid camera using assisted capture settings.

    Args:
        camera: Zivid camera
        max_time_milliseconds: Maximum capture time allowed in milliseconds

    Returns:
        Zivid frame

    """
    suggest_settings_parameters = SuggestSettingsParameters(
        max_capture_time=datetime.timedelta(milliseconds=max_time_milliseconds),
        ambient_light_frequency=SuggestSettingsParameters.AmbientLightFrequency.none,
    )
    settings = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)
    return camera.capture_2d_3d(settings)


def perform_hand_eye_calibration(
    calibration_type: str,
    dataset_directory: Path,
    user_options: argparse.Namespace,
) -> Tuple[np.ndarray, List[zivid.calibration.HandEyeResidual]]:
    """Perform hand-eye calibration based on calibration type.

    Args:
        calibration_type: Calibration type, eye-in-hand or eye-to-hand
        dataset_directory: Path to dataset
        user_options: Input arguments

    Returns:
        transform: Transformation matrix (4x4)
        residuals: List of residuals

    Raises:
        ValueError: Invalid calibration type

    """
    hand_eye_input = []
    pose_and_image_iterator = 1

    while True:
        frame_file_path = dataset_directory / f"img{pose_and_image_iterator:02d}.zdf"
        pose_file_path = dataset_directory / f"pos{pose_and_image_iterator:02d}.yaml"

        if frame_file_path.is_file() and pose_file_path.is_file():
            print(f"Detect feature points from img{pose_and_image_iterator:02d}.zdf")

            frame = zivid.Frame(frame_file_path)
            if user_options.calibration_object == "checkerboard":
                detected_features = zivid.calibration.detect_calibration_board(frame)
            else:
                detected_features = zivid.calibration.detect_markers(frame, user_options.ids, user_options.dictionary)
            print(f"Read robot pose from pos{pose_and_image_iterator:02d}.yaml")
            transform = load_and_assert_affine_matrix(pose_file_path)

            detection_result = zivid.calibration.HandEyeInput(zivid.calibration.Pose(transform), detected_features)
            hand_eye_input.append(detection_result)
        else:
            break

        pose_and_image_iterator += 1

    print(f"\nPerforming {calibration_type} calibration")

    if calibration_type == "eye-in-hand":
        calibration_result = zivid.calibration.calibrate_eye_in_hand(hand_eye_input)
    elif calibration_type == "eye-to-hand":
        calibration_result = zivid.calibration.calibrate_eye_to_hand(hand_eye_input)
    else:
        raise ValueError(f"Invalid calibration type: {calibration_type}")

    transform = calibration_result.transform()
    residuals = calibration_result.residuals()

    print("\n\nTransform: \n")
    np.set_printoptions(precision=5, suppress=True)
    print(transform)

    print("\n\nResiduals: \n")
    for residual in residuals:
        print(f"Rotation: {residual.rotation():.6f}   Translation: {residual.translation():.6f}")

    return transform, residuals


def options() -> argparse.Namespace:
    """Function for taking in arguments from user.

    Returns:
        eih or eth: eye-in-hand or eye-to-hand
        ip: IP address of the robot controller
        target_keyword: The common name of the targets (poses) in RoboDK station that will be used for the hand-eye dataset
        calibration:object: marker (for ArUco marker(s)) or checkerboard (for Zivid checkerboard)
        dictionary: ArUco marker dictionary
        ids: List of ArUco marker IDs

    """
    parser = argparse.ArgumentParser(description=__doc__)
    type_group = parser.add_mutually_exclusive_group(required=True)

    type_group.add_argument("--eih", "--eye-in-hand", action="store_true", help="eye-in-hand calibration")
    type_group.add_argument("--eth", "--eye-to-hand", action="store_true", help="eye-to-hand calibration")
    parser.add_argument("--ip", required=True, help="IP address of the robot controller")
    parser.add_argument(
        "--target-keyword",
        required=True,
        help='This is the keyword shared for naming all poses used for hand-eye dataset, i.e. if we have: "Target 1", "Target 2", ... , "Target N". Then we should use "Target"',
    )
    subparsers = parser.add_subparsers(dest="calibration_object", required=True, help="Calibration object type")
    subparsers.add_parser("checkerboard", help="Use checkerboard for calibration")
    marker_parser = subparsers.add_parser("marker", help="Use marker for calibration")
    marker_parser.add_argument(
        "--dictionary",
        required=True,
        choices=list(zivid.calibration.MarkerDictionary.valid_values()),
        help="Dictionary used for marker calibration",
    )
    marker_parser.add_argument("--ids", nargs="+", required=True, type=int, help="IDs used for marker calibration")

    return parser.parse_args()


def _main() -> None:
    app = zivid.Application()

    user_options = options()

    rdk, robot = connect_to_robot(user_options.ip)

    targets = get_robot_targets(rdk, user_options.target_keyword)

    #  NOTE! Verify safe operation speeds and accelerations for your robot
    set_robot_speed_and_acceleration(robot, speed=100, joint_speed=100, acceleration=50, joint_acceleration=50)

    dataset_dir = generate_hand_eye_dataset(app, robot, targets, user_options)

    if user_options.eih:
        transform, residuals = perform_hand_eye_calibration("eye-in-hand", dataset_dir, user_options)
    else:
        transform, residuals = perform_hand_eye_calibration("eye-to-hand", dataset_dir, user_options)

    _save_hand_eye_results(dataset_dir, transform, residuals)


if __name__ == "__main__":
    _main()
