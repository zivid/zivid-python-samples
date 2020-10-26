"""
This example shows how to capture a 2D image and apply a configurable gamma correction.
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
        description=("Capture 2D image and apply gamma correction\n" "Example:\n\t $ python gamma_correction.py 2"),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("gamma", type=float, help="Gamma correction value")
    return parser.parse_args()


def adjust_gamma(image, gamma: float):
    """Adjust gamma on image.

    Copied from : https://www.pyimagesearch.com/2015/10/05/opencv-gamma-correction/

    Args:
        image: BGR image (HxWx3 darray) to be corrected
        gamma: Gamma setting to be applied

    Returns:
        Gamma adjusted BGR image (HxWx3 darray)

    """
    # Building a lookup table mapping the pixel values [0, 255] to their adjusted gamma values
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    # Applying gamma correction using the lookup table
    return cv2.LUT(image, table)


def _capture_bgr_image(camera):
    """Capture and extract 2D image, then convert from RGBA and return BGR.

    Args:
        camera: Zivid Camera handle

    Returns:
        BGR image (HxWx3 darray)

    """
    print("Configuring Settings")
    settings_2d = zivid.Settings2D(
        acquisitions=[zivid.Settings2D.Acquisition()],
    )
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

    bgr_original = _capture_bgr_image(camera)
    cv2.imwrite("Original.jpg", bgr_original)

    print(f"Applying gamma correction: {user_options.gamma}")
    bgr_adjusted = adjust_gamma(bgr_original, user_options.gamma)
    cv2.imwrite("Adjusted.jpg", bgr_adjusted)

    width = (int)(bgr_original.shape[1] / 2)
    combined_image = np.hstack([bgr_original[:, :width], bgr_adjusted[:, -width:]])
    cv2.imshow("Original on left, adjusted on right", combined_image)
    cv2.waitKey(0)


if __name__ == "__main__":
    _main()
