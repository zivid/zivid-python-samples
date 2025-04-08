"""
Perform Hand-Eye calibration.

"""

import datetime
from pathlib import Path
from typing import List, Tuple

import numpy as np
import zivid
from zividsamples.save_load_matrix import assert_affine_matrix_and_save


def _enter_robot_pose(index: int) -> zivid.calibration.Pose:
    """Robot pose user input.

    Args:
        index: Robot pose ID

    Returns:
        robot_pose: Robot pose

    """
    inputted = input(
        f"Enter pose with id={index} (a line with 16 space separated values describing 4x4 row-major matrix): "
    )
    elements = inputted.split(maxsplit=15)
    data = np.array(elements, dtype=np.float64).reshape((4, 4))
    robot_pose = zivid.calibration.Pose(data)
    print(f"The following pose was entered:\n{robot_pose}")
    return robot_pose


def _perform_calibration(hand_eye_input: List[zivid.calibration.HandEyeInput]) -> zivid.calibration.HandEyeOutput:
    """Hand-Eye calibration type user input.

    Args:
        hand_eye_input: Hand-Eye calibration input

    Returns:
        hand_eye_output: Hand-Eye calibration result

    """
    while True:
        calibration_type = input("Enter type of calibration, eth (for eye-to-hand) or eih (for eye-in-hand): ").strip()
        if calibration_type.lower() == "eth":
            print(f"Performing eye-to-hand calibration with {len(hand_eye_input)} dataset pairs")
            print("The resulting transform is the camera pose in robot base frame")
            hand_eye_output = zivid.calibration.calibrate_eye_to_hand(hand_eye_input)
            return hand_eye_output
        if calibration_type.lower() == "eih":
            print(f"Performing eye-in-hand calibration with {len(hand_eye_input)} dataset pairs")
            print("The resulting transform is the camera pose in flange (end-effector) frame")
            hand_eye_output = zivid.calibration.calibrate_eye_in_hand(hand_eye_input)
            return hand_eye_output
        print(f"Unknown calibration type: '{calibration_type}'")


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
    settings = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)
    return camera.capture_2d_3d(settings)


def _handle_add_pose(
    current_pose_id: int, hand_eye_input: List, camera: zivid.Camera, calibration_object: str
) -> Tuple[int, List]:
    """Acquire frame with capture assistant.

    Args:
        current_pose_id: Counter of the current pose in the hand-eye calibration dataset
        hand_eye_input: List of hand-eye calibration dataset pairs (poses and point clouds)
        camera: Zivid camera
        calibration_object: m (for ArUco marker(s)) or c (for Zivid checkerboard)

    Returns:
        Tuple[int, List]: Updated current_pose_id and hand_eye_input

    """

    robot_pose = _enter_robot_pose(current_pose_id)

    print("Detecting calibration object in point cloud")

    if calibration_object == "c":

        frame = zivid.calibration.capture_calibration_board(camera)
        detection_result = zivid.calibration.detect_calibration_board(frame)

        if detection_result.valid():
            print("Calibration board detected")
            hand_eye_input.append(zivid.calibration.HandEyeInput(robot_pose, detection_result))
            current_pose_id += 1
        else:
            print(f"Failed to detect calibration board. {detection_result.status_description()}")
    elif calibration_object == "m":

        frame = _assisted_capture(camera)

        marker_dictionary = zivid.calibration.MarkerDictionary.aruco4x4_50
        marker_ids = [1, 2, 3]

        print(f"Detecting arUco marker IDs {marker_ids} from the dictionary {marker_dictionary}")
        detection_result = zivid.calibration.detect_markers(frame, marker_ids, marker_dictionary)

        if detection_result.valid():
            print(f"ArUco marker(s) detected: {len(detection_result.detected_markers())}")
            hand_eye_input.append(zivid.calibration.HandEyeInput(robot_pose, detection_result))
            current_pose_id += 1
        else:
            print(
                "Failed to detect any ArUco markers, ensure that at least one ArUco marker is in the view of the camera"
            )
    return current_pose_id, hand_eye_input


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    current_pose_id = 0
    hand_eye_input = []
    calibrate = False

    while True:
        calibration_object = input(
            "Enter calibration object you are using, m (for ArUco marker(s)) or c (for Zivid checkerboard): "
        ).strip()
        if calibration_object.lower() == "m" or calibration_object.lower() == "c":
            break

    print(
        "Zivid primarily operates with a (4x4) transformation matrix. To convert\n"
        "from axis-angle, rotation vector, roll-pitch-yaw, or quaternion, check out\n"
        "our pose_conversions sample."
    )

    while not calibrate:
        command = input("Enter command, p (to add robot pose) or c (to perform calibration): ").strip()
        if command == "p":
            try:
                current_pose_id, hand_eye_input = _handle_add_pose(
                    current_pose_id, hand_eye_input, camera, calibration_object
                )
            except ValueError as ex:
                print(ex)
        elif command == "c":
            calibrate = True
        else:
            print(f"Unknown command '{command}'")

    calibration_result = _perform_calibration(hand_eye_input)
    transform = calibration_result.transform()
    transform_file_path = Path(Path(__file__).parent / "transform.yaml")
    assert_affine_matrix_and_save(transform, transform_file_path)

    print(
        "Zivid primarily operates with a (4x4) transformation matrix. To convert\n"
        "to axis-angle, rotation vector, roll-pitch-yaw, or quaternion, check out\n"
        "our pose_conversions sample."
    )

    if calibration_result.valid():
        print("Hand-Eye calibration OK")
        print(f"Result:\n{calibration_result}")
    else:
        print("Hand-Eye calibration FAILED")


if __name__ == "__main__":
    _main()
