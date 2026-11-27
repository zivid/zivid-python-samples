"""
Script to generate a dataset and perform hand-eye calibration using a Universal Robot UR5e robot.
The script communicates with the robot through Real-Time Data Exchange (RTDE) interface.
More information about RTDE:
https://www.universal-robots.com/articles/ur/interface-communication/real-time-data-exchange-rtde-guide/

The entire sample consist of two additional files:
    - universal_robots_hand_eye_script.urp: Robot program script that moves between different poses.
    - robot_communication_file.xml: communication set-up file.

Running the sample requires that you have universal_robots_hand_eye_script.urp on your UR5e robot,
and robot_communication_file.xml in the same repo as this sample. Each robot pose
must be modified to your scene. This is done in universal_robots_hand_eye_script.urp on the robot.

Further explanation of this sample is found in our knowledge base:
https://support.zivid.com/latest/academy/applications/hand-eye/ur5-robot-%2B-python-generate-dataset-and-perform-hand-eye-calibration.html

"""

import argparse
import datetime
import time
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import zivid
from rtde import rtde, rtde_config
from scipy.spatial.transform import Rotation
from zividsamples.hand_eye_session import CalibrationObjectType, HandEyeSession, MarkerConfiguration
from zividsamples.paths import get_sample_data_path


def _options() -> argparse.Namespace:
    """Function for taking in arguments from user.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--eih", "--eye-in-hand", action="store_true", help="eye-in-hand calibration")
    mode_group.add_argument("--eth", "--eye-to-hand", action="store_true", help="eye-to-hand calibration")
    parser.add_argument(
        "--settings-path",
        required=False,
        type=Path,
        help="Path to the camera settings YML file",
    )
    parser.add_argument("--ip", required=True, help="IP address to robot")

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


def _write_robot_state(
    rtde_data: Tuple[rtde.RTDE, rtde.serialize.DataObject],
    finish_capture: bool = False,
    camera_ready: bool = False,
) -> None:
    """Write to robot I/O registers.

    Args:
        rtde_data: Tuple containing computer-robot connection and input package with specific input data registers
        finish_capture: Boolean value to robot_state that q_r scene capture is finished
        camera_ready: Boolean value to robot_state that camera is ready to capture images

    """
    rtde_data[1].input_bit_register_64 = int(finish_capture)
    rtde_data[1].input_bit_register_65 = int(camera_ready)

    rtde_data[0].send(rtde_data[1])


def _initialize_robot_sync(host: str) -> Tuple[rtde.RTDE, rtde.serialize.DataObject]:
    """Set up communication with UR robot.

    Args:
        host: IP address

    Returns:
        con: Connection to robot
        robot_input_data: Package containing the specific input data registers

    Raises:
        RuntimeError: If protocol do not match
        RuntimeError: If script is unable to configure output
        RuntimeError: If synchronization is not possible

    """
    conf = rtde_config.ConfigFile(Path(Path.cwd() / "universal_robots_communication_file.xml"))
    output_names, output_types = conf.get_recipe("out")
    input_names, input_types = conf.get_recipe("in")

    # port 30004 is reserved for rtde
    con = rtde.RTDE(host, 30004)
    con.connect()

    # To ensure that the application is compatible with further versions of UR controller
    if not con.negotiate_protocol_version():
        raise RuntimeError("Protocol do not match")

    if not con.send_output_setup(output_names, output_types, frequency=200):
        raise RuntimeError("Unable to configure output")

    robot_input_data = con.send_input_setup(input_names, input_types)

    if not con.send_start():
        raise RuntimeError("Unable to start synchronization")

    print("Communication initialization completed. \n")

    return con, robot_input_data


def _create_session(user_options: argparse.Namespace) -> HandEyeSession:
    """Create a hand-eye session folder seeded with the configuration from the command line.

    Args:
        user_options: Input arguments

    Returns:
        The created hand-eye session

    """
    session_root = Path.cwd() / "datasets" / datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    marker_configuration: Optional[MarkerConfiguration] = None
    calibration_object = CalibrationObjectType.CHECKERBOARD
    if user_options.calibration_object == "marker":
        calibration_object = CalibrationObjectType.MARKERS
        marker_configuration = MarkerConfiguration(dictionary=user_options.dictionary, marker_ids=user_options.ids)

    return HandEyeSession.create(
        session_root,
        eye_in_hand=user_options.eih,
        calibration_object=calibration_object,
        marker_configuration=marker_configuration,
    )


def _get_frame_and_transform_matrix(
    con: rtde,
    camera: zivid.Camera,
    settings: zivid.Settings,
) -> Tuple[zivid.Frame, np.ndarray]:
    """Capture image with Zivid camera and read robot pose.

    Args:
        con: Connection between computer and robot
        camera: Zivid camera
        settings: Zivid settings

    Returns:
        frame: Zivid frame
        transform: Transformation matrix (4x4)

    """
    frame = camera.capture_2d_3d(settings)
    robot_pose = np.array(con.receive().actual_TCP_pose)

    meters_to_millimeters = 1000
    translation = robot_pose[:3] * meters_to_millimeters
    rotation_vector = robot_pose[3:]
    rotation = Rotation.from_rotvec(rotation_vector)
    transform = np.eye(4)
    transform[:3, :3] = rotation.as_matrix()
    transform[:3, 3] = translation.T

    return frame, transform


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


def _read_robot_state(con: rtde.RTDE) -> rtde.serialize:
    """Receive robot output recipe.

    Args:
        con: Connection between computer and robot

    Returns:
        robot_state: Robot state

    """
    robot_state = con.receive()

    assert robot_state is not None, "Not able to receive robot_state"

    return robot_state


def _image_count(robot_state: rtde.serialize.DataObject) -> int:
    """Read robot output register 24.

    Args:
        robot_state: Robot state

    Returns:
        Number of captured images

    """
    return robot_state.output_int_register_24


def _ready_for_capture(robot_state: rtde.serialize.DataObject) -> bool:
    """Read robot output register 64.

    Args:
        robot_state: Robot state

    Returns:
        Boolean value that states if camera is ready to capture

    """
    return robot_state.output_bit_register_64


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
            raise RuntimeError("Failed to detect feature any ArUco markers from captured frame.")


def _capture_one_frame_and_robot_pose(
    *,
    rtde_data: Tuple[rtde.RTDE, rtde.serialize.DataObject],
    camera: zivid.Camera,
    settings: zivid.Settings,
    session: HandEyeSession,
    image_num: int,
    ready_to_capture: bool,
    user_options: argparse.Namespace,
) -> None:
    """Capture 3D image and robot pose for a given robot posture,
    then signals robot to move to next posture.

    Args:
        rtde_data: Tuple containing computer-robot connection and input package with specific input data registers
        camera: Zivid camera
        settings: Zivid settings
        session: Hand-eye session the pose pair is saved into
        image_num: Image number
        ready_to_capture: Boolean value to robot_state that camera is ready to capture images
        user_options: Input arguments

    """
    frame, transform = _get_frame_and_transform_matrix(rtde_data[0], camera, settings)
    _verify_good_capture(frame, user_options)

    # Signal robot to move to next position, then set signal to low again.
    _write_robot_state(rtde_data=rtde_data, finish_capture=True, camera_ready=ready_to_capture)
    time.sleep(0.1)
    _write_robot_state(rtde_data=rtde_data, finish_capture=False, camera_ready=ready_to_capture)
    session.save_pose_pair(image_num, transform, frame)
    print("Image and pose saved")


def _generate_dataset(
    app: zivid.Application, rtde_data: Tuple[rtde.RTDE, rtde.serialize.DataObject], user_options: argparse.Namespace
) -> HandEyeSession:
    """Generate a hand-eye session based on predefined robot poses.

    Args:
        app: Zivid application instance
        rtde_data: Tuple containing computer-robot connection and input package with specific input data registers
        user_options: Input arguments

    Returns:
        The hand-eye session the dataset is saved into

    """
    camera = app.connect_camera()
    session = _create_session(user_options)

    if user_options.settings_path is None:
        user_options.settings_path = _preset_path(camera)
    settings = zivid.Settings.load(user_options.settings_path)

    # Signal robot that camera is ready
    ready_to_capture = True
    _write_robot_state(rtde_data, finish_capture=False, camera_ready=ready_to_capture)

    robot_state = _read_robot_state(rtde_data[0])

    print(
        "Initial output robot_states: \n"
        f"Image count: {_image_count(robot_state)} \n"
        f"Ready for capture: {_ready_for_capture(robot_state)}\n"
    )

    images_captured = 1
    while _image_count(robot_state) != -1:
        robot_state = _read_robot_state(rtde_data[0])

        if _ready_for_capture(robot_state) and images_captured == _image_count(robot_state):
            print(f"Capture image {_image_count(robot_state)}")
            _capture_one_frame_and_robot_pose(
                rtde_data=rtde_data,
                camera=camera,
                settings=settings,
                session=session,
                image_num=images_captured,
                ready_to_capture=ready_to_capture,
                user_options=user_options,
            )
            images_captured += 1

        time.sleep(0.1)

    _write_robot_state(rtde_data, finish_capture=False, camera_ready=False)
    time.sleep(1.0)
    rtde_data[0].send_pause()
    rtde_data[0].disconnect()

    print(f"\n Data saved to: {session.root}")

    return session


def perform_hand_eye_calibration(
    session: HandEyeSession,
) -> zivid.calibration.HandEyeOutput:
    """Perform hand-eye calibration on the pose pairs in a session.

    Args:
        session: Hand-eye session holding the captured pose pairs

    Returns:
        The hand-eye calibration result

    Raises:
        RuntimeError: If no feature points are detected

    """
    calibration_inputs = []
    for pose_pair in session.load_pose_pairs():
        print(f"Detect feature points from {pose_pair.frame_path.name}")
        frame = zivid.Frame(pose_pair.frame_path)
        if session.calibration_object == CalibrationObjectType.MARKERS:
            detection_result = zivid.calibration.detect_markers(
                frame, session.marker_configuration.marker_ids, session.marker_configuration.dictionary
            )
        else:
            detection_result = zivid.calibration.detect_calibration_board(frame)

        if not detection_result.valid():
            raise RuntimeError(
                f"Failed to detect feature points from frame {pose_pair.frame_path}. {detection_result.status_description()}"
            )

        print(f"Read robot pose {pose_pair.pose_id}")
        calibration_inputs.append(
            zivid.calibration.HandEyeInput(zivid.calibration.Pose(pose_pair.robot_pose), detection_result)
        )

    calibration_type = "eye-in-hand" if session.eye_in_hand else "eye-to-hand"
    print(f"\nPerform {calibration_type} calibration")
    if session.eye_in_hand:
        calibration_result = zivid.calibration.calibrate_eye_in_hand(calibration_inputs)
    else:
        calibration_result = zivid.calibration.calibrate_eye_to_hand(calibration_inputs)

    print("\n\nTransform: \n")
    np.set_printoptions(precision=5, suppress=True)
    print(np.array(calibration_result.transform()))

    print("\n\nResiduals: \n")
    for res in calibration_result.residuals():
        print(
            f"Rotation: {res.rotation():.6f}°   Translation: {res.translation():.6f} mm   "
            f"Spatial extent: {res.spatial_extent():.6f} mm   Point RMSE: {res.point_rmse():.6f} mm"
        )

    return calibration_result


def _main() -> None:
    app = zivid.Application()
    user_options = _options()

    robot_ip_address = user_options.ip
    con, input_data = _initialize_robot_sync(robot_ip_address)
    con.send_start()

    session = _generate_dataset(app, (con, input_data), user_options)

    calibration_result = perform_hand_eye_calibration(session)

    session.save_calibration_result(calibration_result)


if __name__ == "__main__":
    _main()
