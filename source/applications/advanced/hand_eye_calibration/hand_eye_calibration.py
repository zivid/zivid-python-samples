"""
This example shows how to perform Hand-Eye calibration.
"""

import datetime

import numpy as np
import zivid


def _acquire_checkerboard_frame(camera):
    """Acquire checkerboard frame.

    Args:
        camera: Zivid camera

    Returns:
        frame: Zivid frame

    """
    print("Configuring settings")
    settings = zivid.Settings()
    settings.acquisitions.append(zivid.Settings.Acquisition())
    settings.acquisitions[0].aperture = 8.0
    settings.acquisitions[0].exposure_time = datetime.timedelta(microseconds=20000)
    settings.processing.filters.smoothing.gaussian.enabled = True
    print("Capturing checkerboard image")
    return camera.capture(settings)


def _enter_robot_pose(index):
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


def _perform_calibration(hand_eye_input):
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


def _main():
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

                frame = _acquire_checkerboard_frame(camera)

                print("Detecting checkerboard in point cloud")
                detection_result = zivid.calibration.detect_feature_points(frame.point_cloud())

                if detection_result:
                    print("OK")
                    hand_eye_input.append(zivid.calibration.HandEyeInput(robot_pose, detection_result))
                    current_pose_id += 1
                else:
                    print("FAILED")
            except ValueError as ex:
                print(ex)
        elif command == "c":
            calibrate = True
        else:
            print(f"Unknown command '{command}'")

    calibration_result = _perform_calibration(hand_eye_input)
    if calibration_result.valid():
        print("Hand-Eye calibration OK")
        print(f"Result:\n{calibration_result}")
    else:
        print("Hand-Eye calibration FAILED")


if __name__ == "__main__":
    _main()
