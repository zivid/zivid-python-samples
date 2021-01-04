"""
This example shows how to capture a 2D image with a configurable gamma correction.
"""

import argparse
import numpy as np
import cv2
import zivid


def _options():
    """Configure and take command line arguments from user

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(
        description=(
            "Capture 2D image with gamma correction (0.25 to 1.5)\n" "Example:\n\t $ python gamma_correction.py 0.6"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("gamma", type=float, help="Gamma correction value")
    return parser.parse_args()


def _capture_bgr_image(camera, gamma):
    """Capture and extract 2D image, then convert from RGBA and return BGR.

    Args:
        camera: Zivid Camera handle
        gamma: Gamma correction value

    Returns:
        BGR image (HxWx3 darray)

    """
    print("Configuring Settings")
    settings_2d = zivid.Settings2D(
        acquisitions=[zivid.Settings2D.Acquisition()],
    )
    settings_2d.processing.color.gamma = gamma

    print("Capturing 2D frame")
    with camera.capture(settings_2d) as frame_2d:
        image = frame_2d.image_rgba()
        rgba = image.copy_data()
        bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
        return bgr


def _main():
    app = zivid.Application()

    user_options = _options()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Capturing without gamma correction")
    bgr_original = _capture_bgr_image(camera, 1.0)
    cv2.imwrite("Original.jpg", bgr_original)

    print(f"Capturing with gamma correction: {user_options.gamma}")
    bgr_adjusted = _capture_bgr_image(camera, user_options.gamma)
    cv2.imwrite("Adjusted.jpg", bgr_adjusted)

    width = (int)(bgr_original.shape[1] / 2)
    combined_image = np.hstack([bgr_original[:, :width], bgr_adjusted[:, -width:]])
    cv2.imshow("Original on left, adjusted on right", combined_image)
    print("Press any key to continue")
    cv2.waitKey(0)


if __name__ == "__main__":
    _main()
