"""
Generate a dataset and perform hand-eye calibration using the Robodk interface.

You must modify each robot pose to your scene using the RoboDK GUI interface.

The sample comes with a .rdk sample environment file using a Universal Robots UR5e robot.

To use the sample with your robot an rdk file needs to be created using a model of your robot.
Each pose will need to be created or modified to fit your scene using the RoboDK GUI.
For finding the best poses for hand-eye check out:
https://support.zivid.com/latest/academy/applications/hand-eye/hand-eye-calibration-process.html
Make sure to launch your RDK file and connect to robot through Robodk before running this script.

You can find the complete tutorial with a detailed explanation at:
https://support.zivid.com/en/latest/camera/academy/applications/hand-eye/robodk-%2B-python-generate-dataset-and-perform-hand-eye-calibration.html

More information about RoboDK is available at: https://robodk.com/doc/en/Getting-Started.html

"""

import argparse
import datetime
import time
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import zivid
from robodk.robolink import Item
from zividsamples.hand_eye_session import CalibrationObjectType, HandEyeSession, MarkerConfiguration
from zividsamples.paths import get_sample_data_path
from zividsamples.robodk_tools import connect_to_robot, get_robot_targets, set_robot_speed_and_acceleration


def _create_session(user_options: argparse.Namespace) -> HandEyeSession:
    """Create a hand-eye session folder seeded with the configuration from the command line.

    Args:
        user_options: Input arguments

    Returns:
        The created hand-eye session

    """
    name = input("Input desired name of dataset directory: (enter for default: /datasets/handeye) ")
    directory_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") if name == "" else name
    directory_path = Path(__file__).absolute().parent / "datasets/handeye" / directory_name

    marker_configuration: Optional[MarkerConfiguration] = None
    calibration_object = CalibrationObjectType.CHECKERBOARD
    if user_options.calibration_object == "marker":
        calibration_object = CalibrationObjectType.MARKERS
        marker_configuration = MarkerConfiguration(dictionary=user_options.dictionary, marker_ids=user_options.ids)

    session = HandEyeSession.create(
        directory_path,
        eye_in_hand=user_options.eih,
        calibration_object=calibration_object,
        marker_configuration=marker_configuration,
    )
    print(f"Session created at {directory_path}")
    return session


def _get_frame_and_transform(
    robot: Item, camera: zivid.Camera, settings: zivid.Settings
) -> Tuple[zivid.Frame, np.ndarray]:
    """Capture image with Zivid camera and read robot pose.

    Args:
        robot: Robot item in open RoboDK rdk file
        camera: Zivid camera
        settings: Zivid capture settings

    Returns:
        Zivid frame
        Transformation matrix (4x4)

    """
    frame = camera.capture_2d_3d(settings)
    transform = np.array(robot.Pose()).T
    return frame, transform


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
    settings: zivid.Settings,
    session: HandEyeSession,
    pose_id: int,
    next_target: Item,
    user_options: argparse.Namespace,
) -> None:
    """Captures and saves point cloud at a given robot pose, saves robot pose,
    then signals the robot to move to the next pose.

    Args:
        robot: Robot item in open RoboDK rdk file
        camera: Zivid camera
        settings: Zivid camera settings
        session: Hand-eye session the pose pair is saved into
        pose_id: Pose pair identifier
        next_target: Next pose the robot should move to in sequence
        user_options: Input arguments

    """
    robot.WaitMove()
    # Make sure the robot is completely stopped and no miniscule movement is occurring
    time.sleep(0.2)

    frame, transform = _get_frame_and_transform(robot, camera, settings)

    session.save_pose_pair(pose_id, transform, frame)
    # Verifying capture from previous pose while moving to new pose
    if next_target is not None:
        robot.MoveJ(next_target, blocking=False)
    _verify_good_capture(frame, user_options)
    print(f"Image and pose #{pose_id} saved")


def generate_hand_eye_dataset(
    app: zivid.application, robot: Item, targets: List, user_options: argparse.Namespace
) -> HandEyeSession:
    """Generate a hand-eye session of robot-pose and calibration-object capture pairs.

    Args:
        app: Zivid application instance
        robot: Robot item in open RoboDK rdk file
        targets: List of roboDK targets (poses)
        user_options: Input arguments

    Returns:
        The hand-eye session the data was saved into

    """
    robot.MoveJ(targets.pop(0))
    camera = app.connect_camera()
    if user_options.settings_path is None:
        user_options.settings_path = _preset_path(camera)
    settings = zivid.Settings.load(user_options.settings_path)
    session = _create_session(user_options)
    num_targets = len(targets)
    pose_id = 1
    while not pose_id > num_targets:
        print(f"Capturing calibration object at robot pose {num_targets - len(targets)}")
        _capture_one_frame_and_robot_pose(
            robot=robot,
            camera=camera,
            settings=settings,
            session=session,
            pose_id=pose_id,
            next_target=targets.pop(0) if targets else None,
            user_options=user_options,
        )
        pose_id += 1

    print(f"\n Data saved to: {session.root}")

    return session


def _preset_path(camera: zivid.Camera) -> Path:
    """Get path to preset settings YML file, depending on camera model.

    Args:
        camera: Zivid camera

    Raises:
        ValueError: If unsupported camera model for this code sample

    Returns:
        Path: Zivid 2D and 3D settings YML path

    """
    presets_path = get_sample_data_path() / "Settings"

    if camera.info.model == zivid.CameraInfo.Model.zivid3XL250:
        return presets_path / "Zivid_Three_XL250_DepalletizationQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusMR60:
        return presets_path / "Zivid_Two_Plus_MR60_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusMR130:
        return presets_path / "Zivid_Two_Plus_MR130_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusLR110:
        return presets_path / "Zivid_Two_Plus_LR110_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusM60:
        return presets_path / "Zivid_Two_Plus_M60_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusM130:
        return presets_path / "Zivid_Two_Plus_M130_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusL110:
        return presets_path / "Zivid_Two_Plus_L110_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zividTwo:
        return presets_path / "Zivid_Two_M70_ManufacturingSpecular.yml"
    if camera.info.model == zivid.CameraInfo.Model.zividTwoL100:
        return presets_path / "Zivid_Two_L100_ManufacturingSpecular.yml"

    raise ValueError("Invalid camera model")


def perform_hand_eye_calibration(
    session: HandEyeSession,
) -> zivid.calibration.HandEyeOutput:
    """Perform hand-eye calibration on the pose pairs in a session.

    Args:
        session: Hand-eye session holding the captured pose pairs

    Returns:
        The hand-eye calibration result

    """
    hand_eye_input = []
    for pose_pair in session.load_pose_pairs():
        print(f"Detect feature points from {pose_pair.frame_path.name}")
        frame = zivid.Frame(pose_pair.frame_path)
        if session.calibration_object == CalibrationObjectType.MARKERS:
            detected_features = zivid.calibration.detect_markers(
                frame, session.marker_configuration.marker_ids, session.marker_configuration.dictionary
            )
        else:
            detected_features = zivid.calibration.detect_calibration_board(frame)
        print(f"Read robot pose {pose_pair.pose_id}")
        hand_eye_input.append(
            zivid.calibration.HandEyeInput(zivid.calibration.Pose(pose_pair.robot_pose), detected_features)
        )

    calibration_type = "eye-in-hand" if session.eye_in_hand else "eye-to-hand"
    print(f"\nPerforming {calibration_type} calibration")
    if session.eye_in_hand:
        calibration_result = zivid.calibration.calibrate_eye_in_hand(hand_eye_input)
    else:
        calibration_result = zivid.calibration.calibrate_eye_to_hand(hand_eye_input)

    print("\n\nTransform: \n")
    np.set_printoptions(precision=5, suppress=True)
    print(np.array(calibration_result.transform()))

    print("\n\nResiduals: \n")
    for residual in calibration_result.residuals():
        print(
            f"Rotation: {residual.rotation():.6f}°   Translation: {residual.translation():.6f} mm   "
            f"Spatial extent: {residual.spatial_extent():.6f} mm   Point RMSE: {residual.point_rmse():.6f} mm"
        )

    return calibration_result


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
    parser.add_argument(
        "--settings-path",
        required=False,
        type=Path,
        help="Path to the camera settings YML file",
    )
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

    session = generate_hand_eye_dataset(app, robot, targets, user_options)

    calibration_result = perform_hand_eye_calibration(session)

    session.save_calibration_result(calibration_result)


if __name__ == "__main__":
    _main()
