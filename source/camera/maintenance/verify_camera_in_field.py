"""
Check the dimension trueness of a Zivid camera.

This example shows how to verify the local dimension trueness of a camera.
If the trueness is much worse than expected, the camera may have been damaged by
shock in shipping in handling. If so, look at the CorrectCameraInField sample.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.
"""

import zivid
from zivid.experimental import calibration


def _main() -> None:

    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    # For convenience, print the timestamp of the latest correction
    if calibration.has_camera_correction(camera):
        timestamp = calibration.camera_correction_timestamp(camera)
        print(f"Timestamp of current camera correction: {timestamp.strftime(r'%Y-%m-%d %H:%M:%S')}")
    else:
        print("This camera has no in-field correction written to it.")

    # Gather data
    print("Capturing calibration board")
    detection_result = calibration.detect_feature_points(camera)

    # Prepare data and check that it is appropriate for in-field verification
    infield_input = calibration.InfieldCorrectionInput(detection_result)
    if not infield_input.valid():
        raise RuntimeError(
            f"Capture not valid for in-field verification! Feedback: {infield_input.status_description()}"
        )

    # Show results
    print(f"Successful measurement at {detection_result.centroid()}")
    camera_verification = calibration.verify_camera(infield_input)
    print(
        f"Estimated dimension trueness at measured position: {camera_verification.local_dimension_trueness()*100:.3f}%"
    )


if __name__ == "__main__":
    _main()