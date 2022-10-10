"""
Capture 2D image with gamma correction.

"""

import argparse

import cv2
import numpy as np
import zivid


def _options() -> argparse.Namespace:
    """Configure and take command line arguments from user.

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


def _capture_bgr_image(camera: zivid.Camera, gamma: float) -> np.ndarray:
    """Capture and extract 2D image, then convert from RGBA and return BGR.

    Args:
        camera: Zivid Camera handle
        gamma: Gamma correction value

    Returns:
        bgr: BGR image (HxWx3 ndarray)

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


def _combine_images(image_one: np.ndarray, image_two: np.ndarray) -> np.ndarray:
    """Column-wise concatenate each half of two images together as one.

    Args:
        image_one: Left side of concatenated image
        image_two: Right side of concatenated image

    Returns:
        combined_image: Combined halves of each image

    """
    width = (int)(image_one.shape[1] / 2)
    combined_image = np.hstack([image_one[:, :width], image_two[:, -width:]])

    return combined_image


def _display_bgr(image: np.ndarray, bgr_name: str) -> None:
    """Display BGR image using OpenCV.

    Args:
        image: BGR image to be displayed
        bgr_name: Name of the OpenCV window

    """
    cv2.imshow(bgr_name, image)
    print("Press any key to continue")
    cv2.waitKey(0)


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

    print(f"Displaying color image before and after gamma correction: {user_options.gamma}")
    combined_image = _combine_images(bgr_original, bgr_adjusted)
    _display_bgr(combined_image, "Original on left, adjusted on right")


if __name__ == "__main__":
    _main()
