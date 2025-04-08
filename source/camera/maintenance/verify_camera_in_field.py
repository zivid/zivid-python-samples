"""
Check the dimension trueness of a Zivid camera.

This example shows how to verify the local dimension trueness of a camera.
If the trueness is much worse than expected, the camera may have been damaged by
shock in shipping or handling. If so, look at the correct_camera_in_field sample sample.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted
in the future without notice.

"""

import zivid
import zivid.experimental.calibration


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    # For convenience, print the timestamp of the latest correction
    if zivid.experimental.calibration.has_camera_correction(camera):
        timestamp = zivid.experimental.calibration.camera_correction_timestamp(camera)
        print(f"Timestamp of current camera correction: {timestamp.strftime(r'%Y-%m-%d %H:%M:%S')}")
    else:
        print("This camera has no infield correction written to it.")

    # Gather data
    print("Capturing calibration board")
    detection_result = zivid.calibration.detect_calibration_board(camera)
    if not detection_result.valid():
        raise RuntimeError(f"Detection failed! Feedback: {detection_result.status_description()}")

    # Prepare data and check that it is appropriate for infield verification
    infield_input = zivid.experimental.calibration.InfieldCorrectionInput(detection_result)
    if not infield_input.valid():
        raise RuntimeError(
            f"Capture not valid for infield verification! Feedback: {infield_input.status_description()}"
        )

    # Show results
    print(f"Successful measurement at {detection_result.centroid()}")
    camera_verification = zivid.experimental.calibration.verify_camera(infield_input)
    print(
        f"Estimated dimension trueness error at measured position: {camera_verification.local_dimension_trueness() * 100:.3f}%"
    )


if __name__ == "__main__":
    _main()
