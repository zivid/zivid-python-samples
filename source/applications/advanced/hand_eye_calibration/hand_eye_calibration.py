"""
Perform Hand-Eye calibration.

"""

import datetime
from pathlib import Path
from typing import List

import numpy as np
import zivid
from sample_utils.save_load_matrix import assert_affine_matrix_and_save


def _enter_robot_pose(index: int) -> zivid.calibration.Pose:
    """Robot pose user input.

    Args:
        index: Robot pose ID

    Returns:
        robot_pose: Robot pose

    """
    inputted = input(
        f"Enter pose with id={index} (a line with 16 space separated values describing 4x4 row-major matrix):"
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
        calibration_type = input("Enter type of calibration, eth (for eye-to-hand) or eih (for eye-in-hand):").strip()
        if calibration_type.lower() == "eth":
            print("Performing eye-to-hand calibration")
            hand_eye_output = zivid.calibration.calibrate_eye_to_hand(hand_eye_input)
            return hand_eye_output
        if calibration_type.lower() == "eih":
            print("Performing eye-in-hand calibration")
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
    return camera.capture(settings)


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    current_pose_id = 0
    hand_eye_input = []
    calibrate = False

    while not calibrate:
        command = input("Enter command, p (to add robot pose) or c (to perform calibration):").strip()
        if command == "p":
            try:
                robot_pose = _enter_robot_pose(current_pose_id)

                frame = _assisted_capture(camera)

                print("Detecting checkerboard in point cloud")
                detection_result = zivid.calibration.detect_feature_points(frame.point_cloud())

                if detection_result.valid():
                    print("Calibration board detected")
                    hand_eye_input.append(zivid.calibration.HandEyeInput(robot_pose, detection_result))
                    current_pose_id += 1
                else:
                    print(
                        "Failed to detect calibration board, ensure that the entire board is in the view of the camera"
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

    if calibration_result.valid():
        print("Hand-Eye calibration OK")
        print(f"Result:\n{calibration_result}")
    else:
        print("Hand-Eye calibration FAILED")


if __name__ == "__main__":
    _main()
