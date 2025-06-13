"""
Check the dimension trueness of a Zivid camera from a ZDF file.

This example shows how to verify the local dimension trueness of a camera from a ZDF file. If the trueness is much worse
than expected, the camera may have been damaged by shock in shipping or handling. If so, look at the
correct_camera_in_field sample sample.

Why is verifying camera accuracy from a ZDF file useful?

Let us assume that your system is in production. You want to verify the accuracy of the camera while the system is running.
At the same time, you want to minimize the time the robot and the camera are used for anything else than their main task,
e.g., bin picking. Instead of running a full infield verification live, which consists of capturing, detecting, and
estimating accuracy, you can instead only capture and save results to ZDF files on disk. As the robot and the camera go
back to their main tasks, you can load the ZDF files and verify the accuracy offline, using a different PC than the one
used in production. In addition, you can send these ZDF files to Zivid Customer Success for investigation.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

import zivid
import zivid.experimental.calibration
from zividsamples.paths import get_sample_data_path


def _main() -> None:
    app = zivid.Application()

    file_camera = get_sample_data_path() / "BinWithCalibrationBoard.zfc"
    print(f"Creating virtual camera using file: {file_camera}")
    camera = app.create_file_camera(file_camera)
    # Calibration board can be captured live, while the system is in production, and saved to ZDF file, for later use in
    # offline infield verification

    print("Capturing calibration board")
    frame = zivid.calibration.capture_calibration_board(camera)
    data_file = "FrameWithCalibrationBoard.zdf"
    print(f"Saving frame to file: {data_file}, for later use in offline infield verification")
    frame.save(data_file)

    # The ZDF captured with captureCalibrationBoard(camera) that contains the calibration board can be loaded for
    # offline infield verification

    print(f"Reading frame from file: {data_file}, for offline infield verification")
    frame = zivid.Frame(data_file)
    print("Detecting calibration board")
    detection_result = zivid.calibration.detect_calibration_board(frame)

    infield_input = zivid.experimental.calibration.InfieldCorrectionInput(detection_result)
    if not infield_input.valid():
        raise RuntimeError(
            f"Capture not valid for infield verification! Feedback: {infield_input.status_description()}"
        )

    print(f"Successful measurement at {detection_result.centroid()}")
    camera_verification = zivid.experimental.calibration.verify_camera(infield_input)
    print(
        f"Estimated dimension trueness error at measured position: {camera_verification.local_dimension_trueness() * 100:.3f}%"
    )


if __name__ == "__main__":
    _main()
