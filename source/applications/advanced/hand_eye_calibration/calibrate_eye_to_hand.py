"""Hand-eye calibration sample."""
import datetime
import code

import numpy as np
import zivid


def _acquire_checkerboard_frame(camera):
    print("Configuring settings...")
    settings = zivid.Settings(
        acquisitions=[
            zivid.Settings.Acquisition(
                aperture=8.0, exposure_time=datetime.timedelta(microseconds=20000),
            ),
        ],
        processing=zivid.Settings.Processing(
            filters=zivid.Settings.Processing.Filters(
                smoothing=zivid.Settings.Processing.Filters.Smoothing(
                    gaussian=zivid.Settings.Processing.Filters.Smoothing.Gaussian(
                        enabled=True
                    )
                ),
            )
        ),
    )
    print("Capturing checkerboard image... ")
    return camera.capture(settings)


def _enter_robot_pose(index):
    inputted = input(
        f"Enter pose with id={index} (a line with 16 space separated values"
        " describing 4x4 row-major matrix):"
    )
    elements = inputted.split(maxsplit=15)
    data = np.array(elements, dtype=np.float64).reshape((4, 4))
    robot_pose = zivid.calibration.Pose(data)
    print(f"The following pose was entered:\n{robot_pose}")
    return robot_pose


def _main():
    app = zivid.Application()
    camera = app.connect_camera()

    current_pose_id = 0
    calibration_inputs = list()
    calibrate = False

    while not calibrate:
        command = input(
            "Enter command, p (to add robot pose) or c (to perform calibration):"
        ).strip()
        if command == "p":
            try:
                robot_pose = _enter_robot_pose(current_pose_id)

                frame = _acquire_checkerboard_frame(camera)

                print("Detecting checkerboard square centers... ")
                detection_result = zivid.calibration.detect_feature_points(
                    frame.point_cloud()
                )

                if detection_result:
                    print("OK")
                    calibration_inputs.append(
                        zivid.calibration.HandEyeInput(robot_pose, detection_result)
                    )
                    current_pose_id += 1
                else:
                    print("FAILED")
            except ValueError as ex:
                print(ex)
        elif command == "c":
            calibrate = True
        else:
            print(f"Unknown command '{command}'")

    print("Performing hand-eye calibration...")
    calibration_result = zivid.calibration.calibrate_eye_to_hand(calibration_inputs)
    code.interact(local=locals())
    if calibration_result:
        print("OK")
        print(f"Result:\n{calibration_result}")
    else:
        print("FAILED")


if __name__ == "__main__":
    _main()
