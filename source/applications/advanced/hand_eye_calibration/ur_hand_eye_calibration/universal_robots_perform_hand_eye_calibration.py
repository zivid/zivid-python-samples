"""
Script to generate a dataset and perform hand-eye calibration using a Universal Robot UR5e robot.
The script communicates with the robot through Real-Time Data Exchange (RTDE) interface.
More information about RTDE:
https://www.universal-robots.com/how-tos-and-faqs/how-to/ur-how-tos/real-time-data-exchange-rtde-guide-22229/

The entire sample consist of two additional files:
    - universal_robots_hand_eye_script.urp: Robot program script that moves between different poses.
    - robot_communication_file.xml: communication set-up file.

Running the sample requires that you have universal_robots_hand_eye_script.urp on your UR5e robot,
and robot_communication_file.xml in the same repo as this sample. Each robot pose
must be modified to your scene. This is done in universal_robots_hand_eye_script.urp on the robot.

Further explanation of this sample is found in our knowledge base:
https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/103481384/
"""
import argparse
from pathlib import Path
import time
import datetime

import cv2
import numpy as np
from scipy.spatial.transform import Rotation
import zivid
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config


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

    return parser.parse_args()


def _write_robot_state(con: rtde, input_data, finish_capture: bool = False, camera_ready: bool = False):
    """Write to robot I/O registrer

    Args:
        con: Connection between computer and robot
        input_data: Input package containing the specific input data registers
        finish_capture: Boolean value to robot_state that q_r scene capture is finished
        camera_ready: Boolean value to robot_state that camera is ready to capture images
    """

    input_data.input_bit_register_64 = int(finish_capture)
    input_data.input_bit_register_65 = int(camera_ready)

    con.send(input_data)


def _initialize_robot_sync(host: str):
    """Set up communication with UR robot

    Args:
        host: IP address

    Returns:
        Connection to robot
        Package containing the specific input data registers

    Raises:
        RuntimeError: if protocol do not match
        RuntimeError: if script is unable to configure output
        RuntimeError: if synchronization is not possible
    """

    conf = rtde_config.ConfigFile(Path(Path.cwd() / "universal_robots_communication_file.xml"))
    output_names, output_types = conf.get_recipe("out")
    input_names, input_types = conf.get_recipe("in")

    # port 30004 is reserved for rtde
    con = rtde.RTDE(host, 30004)
    con.connect()

    # To ensure that the application is compatable with further versions of UR controller
    if not con.negotiate_protocol_version():
        raise RuntimeError("Protocol do not match")

    if not con.send_output_setup(output_names, output_types, frequency=200):
        raise RuntimeError("Unable to configure output")

    robot_input_data = con.send_input_setup(input_names, input_types)

    if not con.send_start():
        raise RuntimeError("Unable to start synchronization")

    print("Communication initialization completed. \n")

    return con, robot_input_data


def _save_zdf_and_pose(save_dir: Path, image_num: int, frame: zivid.Frame, transform: np.array):
    """Save data to folder

    Args:
        save_dir: Directory to save data
        image_num: Image number
        frame: Point cloud stored as .zdf
        transform: 4x4 transformation matrix
    """

    frame.save(save_dir / f"img{image_num:02d}.zdf")

    file_storage = cv2.FileStorage(str(save_dir / f"pos{image_num:02d}.yaml"), cv2.FILE_STORAGE_WRITE)
    file_storage.write("PoseState", transform)
    file_storage.release()


def _generate_folder():
    """Generate folder where dataset weill be stored

    Returns:
        Directory to where data will be saved
    """

    location_dir = Path.cwd() / "datasets" / datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if not location_dir.is_dir():
        location_dir.mkdir(parents=True)

    return location_dir


def _get_frame_and_transform_matrix(con: rtde, camera: zivid.Camera, settings: zivid.Settings):
    """Capture image with Zivid camera and read robot pose

    Args:
        con: Connection between computer and robot
        camera: Zivid camera
        settings: Zivid settings

    Returns:
        Zivid frame
        4x4 tranformation matrix
    """

    frame = camera.capture(settings)
    robot_pose = np.array(con.receive().actual_TCP_pose)

    translation = robot_pose[:3] * 1000
    rotation_vector = robot_pose[3:]
    rotation = Rotation.from_rotvec(rotation_vector)
    transform = np.eye(4)
    transform[:3, :3] = rotation.as_matrix()
    transform[:3, 3] = translation.T

    return frame, transform


def _camera_settings() -> zivid.Settings:
    """Set camera settings

    Returns:
        Zivid Settings
    """
    return zivid.Settings(
        acquisitions=[
            zivid.Settings.Acquisition(
                aperture=8.0,
                exposure_time=datetime.timedelta(microseconds=10000),
                brightness=1.0,
                gain=1,
            )
        ],
        processing=zivid.Settings.Processing(
            filters=zivid.Settings.Processing.Filters(
                smoothing=zivid.Settings.Processing.Filters.Smoothing(
                    gaussian=zivid.Settings.Processing.Filters.Smoothing.Gaussian(enabled=True)
                )
            )
        ),
    )


def _read_robot_state(con: rtde):
    """Recieve robot output recipe

    Args:
        con: Connection between computer and robot

    Returns:
        Robot state
    """

    robot_state = con.receive()

    assert robot_state is not None, "Not able to recieve robot_state"

    return robot_state


def pose_from_datastring(datastring: str):
    """Extract pose from yaml file saved by openCV

    Args:
        datastring: String of text from .yaml file

    Returns:
        Robotic pose as zivid Pose class
    """

    string = datastring.split("data:")[-1].strip().strip("[").strip("]")
    pose_matrix = np.fromstring(string, dtype=np.float, count=16, sep=",").reshape((4, 4))
    return zivid.calibration.Pose(pose_matrix)


def _save_hand_eye_results(save_dir: Path, transform: np.array, residuals: list):
    """Save transformation and residuals to folder

    Args:
        save_dir: Path to where data will be saved
        transform: 4x4 transformation matrix
        residuals: List of residuals
    """

    file_storage_transform = cv2.FileStorage(str(save_dir / "transformation.yaml"), cv2.FILE_STORAGE_WRITE)
    file_storage_transform.write("PoseState", transform)
    file_storage_transform.release()

    file_storage_residuals = cv2.FileStorage(str(save_dir / "residuals.yaml"), cv2.FILE_STORAGE_WRITE)
    residual_list = []
    for res in residuals:
        tmp = list([res.translation(), res.translation()])
        residual_list.append(tmp)

    file_storage_residuals.write(
        "Per pose residuals for rotation in deg and translation in mm",
        np.array(residual_list),
    )
    file_storage_residuals.release()


def _image_count(robot_state):
    """Read robot output register 24

    Args:
        robot_state: Robot state

    Returns:
        Number of captured images
    """
    return robot_state.output_int_register_24


def _ready_for_capture(robot_state):
    """Read robot output register 64

    Args:
        robot_state: Robot state

    Returns:
        Boolean value that states if camera is ready to capture
    """
    return robot_state.output_bit_register_64


def _verify_good_capture(frame: zivid.Frame):
    """Verify that checkeroard featurepoints are detected in the frame

    Args:
        frame: Zivid frame containing point cloud

    Raises:
        RuntimeError: If no feature points are detected in frame
    """

    point_cloud = frame.point_cloud()
    detected_features = zivid.calibration.detect_feature_points(point_cloud)

    if not detected_features:
        raise RuntimeError("Failed to detect feature points from captured frame.")


def _capture_one_frame_and_robot_pose(
    con: rtde,
    camera: zivid.Camera,
    settings: zivid.Settings,
    save_dir: Path,
    input_data,
    image_num: int,
    ready_to_capture: bool,
):
    """Capture 3D image and robot pose for a given robot posture,
    then signals robot to move to next posture

    Args:
        con: Connection between computer and robot
        camera: Zivid camera
        settings: Zivid settings
        save_dir: Path to where data will be saved
        input_data: Input package containing the specific input data registers
        image_num: Image number
        ready_to_capture: Boolean value to robot_state that camera is ready to capture images
    """

    frame, transform = _get_frame_and_transform_matrix(con, camera, settings)
    _verify_good_capture(frame)

    # Signal robot to move to next position, then set signal to low again.
    _write_robot_state(con, input_data, finish_capture=True, camera_ready=ready_to_capture)
    time.sleep(0.1)
    _write_robot_state(con, input_data, finish_capture=False, camera_ready=ready_to_capture)
    _save_zdf_and_pose(save_dir, image_num, frame, transform)
    print("Image and pose saved")


def _generate_dataset(con: rtde, input_data):
    """Generate dataset based on predefined robot poses

    Args:
        con: Connection between computer and robot
        input_data: Input package containing the specific input data registers

    Returns:
        Directory to where dataset is saved
    """

    with zivid.Application() as app:
        with app.connect_camera() as camera:

            settings = _camera_settings()
            save_dir = _generate_folder()

            # Signal robot that camera is ready
            ready_to_capture = True
            _write_robot_state(con, input_data, finish_capture=False, camera_ready=ready_to_capture)

            robot_state = _read_robot_state(con)

            print(
                "Initial output robot_states: \n"
                f"Image count: {_image_count(robot_state)} \n"
                f"Ready for capture: {_ready_for_capture(robot_state)}\n"
            )

            images_captured = 1
            while _image_count(robot_state) != -1:
                robot_state = _read_robot_state(con)

                if _ready_for_capture(robot_state) and images_captured == _image_count(robot_state):
                    print(f"Capture image {_image_count(robot_state)}")
                    _capture_one_frame_and_robot_pose(
                        con,
                        camera,
                        settings,
                        save_dir,
                        input_data,
                        images_captured,
                        ready_to_capture,
                    )
                    images_captured += 1

                time.sleep(0.1)

    _write_robot_state(con, input_data, finish_capture=False, camera_ready=False)
    time.sleep(1.0)
    con.send_pause()
    con.disconnect()

    print(f"\n Data saved to: {save_dir}")

    return save_dir


def perform_hand_eye_calibration(mode: str, data_dir: Path):
    """Perform had-eye calibration based on mode

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
            detection_result = zivid.calibration.detect_feature_points(point_cloud)

            if not detection_result.valid():
                raise RuntimeError(f"Failed to detect feature points from frame {frame_file}")

            print(f"Read robot pose from pos{idata:02d}.yaml")
            with open(pose_file) as file:
                pose = pose_from_datastring(file.read())

            calibration_inputs.append(zivid.calibration.HandEyeInput(pose, detection_result))
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


def _main():

    user_options = _options()

    robot_ip_address = user_options.ip
    con, input_data = _initialize_robot_sync(robot_ip_address)
    con.send_start()

    dataset_dir = _generate_dataset(con, input_data)

    if user_options.eih:
        transform, residuals = perform_hand_eye_calibration("eye-in-hand", dataset_dir)
    else:
        transform, residuals = perform_hand_eye_calibration("eye-to-hand", dataset_dir)

    _save_hand_eye_results(dataset_dir, transform, residuals)


if __name__ == "__main__":
    _main()
