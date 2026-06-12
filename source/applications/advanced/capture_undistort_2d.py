"""
Use camera intrinsics to undistort a 2D image.

The example will prompt the user for whether to capture an image (2D) or a point cloud (3D).
In both instances it will operate on an BGRA image. However, in the 3D case it will extract
the BGRA image from the point cloud. The 2D variant is faster.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

For more information on lens distortion and undistorting the 2D image, check out this tutorial:
https://support.zivid.com/en/latest/camera/reference-articles/color-spaces-and-output-formats.html

"""

from typing import Tuple

import cv2
import numpy as np
import zivid
import zivid.experimental.calibration
from zividsamples.display import display_bgr, display_pointcloud


def _image_to_bgr(image: zivid.Image) -> np.ndarray:
    """Convert a Zivid BGRA image to an OpenCV BGR image.

    Args:
        image: Zivid BGRA image

    Returns:
        bgr: BGR image (HxWx3 ndarray)

    """
    bgra = image.copy_data()
    return cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)


def _get_image_3d(camera: zivid.Camera, settings: zivid.Settings) -> np.ndarray:
    """Capture a point cloud and extract its color image as an OpenCV BGR image.

    Args:
        camera: Zivid Camera handle
        settings: Capture settings

    Returns:
        bgr: BGR image (HxWx3 ndarray)

    """
    print("3D mode")

    print("Capturing frame")
    frame = camera.capture_2d_3d(settings)

    print("Visualizing point cloud")
    display_pointcloud(frame)

    print("Converting to OpenCV BGRA image")
    image = frame.point_cloud().copy_image("bgra_srgb")

    image_file = "Image.png"
    print(f"Saving 2D color image to file: {image_file}")
    image.save(image_file)

    return _image_to_bgr(image)


def _get_image_2d(camera: zivid.Camera, settings_2d: zivid.Settings2D) -> np.ndarray:
    """Capture a 2D frame and return its color image as an OpenCV BGR image.

    Args:
        camera: Zivid Camera handle
        settings_2d: 2D capture settings

    Returns:
        bgr: BGR image (HxWx3 ndarray)

    """
    print("2D mode")

    print("Capturing 2D frame")
    frame_2d = camera.capture_2d(settings_2d)

    print("Getting BGRA image")
    image = frame_2d.image_bgra_srgb()

    print("Converting to OpenCV BGR image")

    image_file = "Image.png"
    print(f"Saving 2D color image to file: {image_file}")
    image.save(image_file)

    return _image_to_bgr(image)


def _reformat_camera_intrinsics(camera_intrinsics: zivid.CameraIntrinsics) -> Tuple[np.ndarray, np.ndarray]:
    """Reformat Zivid camera intrinsics into an OpenCV camera matrix and distortion coefficients.

    Args:
        camera_intrinsics: Zivid camera intrinsics

    Returns:
        camera_matrix: OpenCV camera matrix (3x3 ndarray)
        distortion_coefficients: OpenCV distortion coefficients (1x5 ndarray)

    """
    distortion_coefficients = np.zeros((1, 5), dtype=np.float64)
    camera_matrix = np.zeros((3, 3), dtype=np.float64)

    distortion_coefficients[0, 0] = camera_intrinsics.distortion.k1
    distortion_coefficients[0, 1] = camera_intrinsics.distortion.k2
    distortion_coefficients[0, 2] = camera_intrinsics.distortion.p1
    distortion_coefficients[0, 3] = camera_intrinsics.distortion.p2
    distortion_coefficients[0, 4] = camera_intrinsics.distortion.k3

    camera_matrix[0, 0] = camera_intrinsics.camera_matrix.fx
    camera_matrix[0, 2] = camera_intrinsics.camera_matrix.cx
    camera_matrix[1, 1] = camera_intrinsics.camera_matrix.fy
    camera_matrix[1, 2] = camera_intrinsics.camera_matrix.cy
    camera_matrix[2, 2] = 1

    return camera_matrix, distortion_coefficients


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    command = input('Enter "2d" or "3d" to select mode, then press Enter/Return to confirm\n')
    use_2d = command in ("2d", "2D")

    settings_2d = zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()])

    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=settings_2d,
    )

    bgr = _get_image_2d(camera, settings_2d) if use_2d else _get_image_3d(camera, settings)

    print("Undistorting BGR image")

    if use_2d:
        camera_matrix, distortion_coefficients = _reformat_camera_intrinsics(
            zivid.experimental.calibration.intrinsics(camera, settings_2d)
        )
    else:
        camera_matrix, distortion_coefficients = _reformat_camera_intrinsics(
            zivid.experimental.calibration.intrinsics(camera, settings)
        )

    size = (bgr.shape[1], bgr.shape[0])
    optimal_camera_matrix = cv2.getOptimalNewCameraMatrix(camera_matrix, distortion_coefficients, size, 1, size)[0]

    bgr_undistorted = cv2.undistort(bgr, camera_matrix, distortion_coefficients)
    bgr_undistorted_full = cv2.undistort(bgr, camera_matrix, distortion_coefficients, None, optimal_camera_matrix)

    image_distorted_file = "ImageDistorted.jpg"
    display_bgr(bgr, "Distorted BGR image")
    print(f"Visualizing and saving BGR image to file: {image_distorted_file}")
    cv2.imwrite(image_distorted_file, bgr)

    image_undistorted_file = "ImageUndistorted.jpg"
    display_bgr(bgr_undistorted, "Undistorted BGR image")
    print(f"Visualizing and saving undistorted BGR image to file: {image_undistorted_file}")
    cv2.imwrite(image_undistorted_file, bgr_undistorted)

    image_undistorted_full_file = "ImageUndistortedFull.jpg"
    display_bgr(bgr_undistorted_full, "Undistorted BGR image - full")
    print(f"Visualizing and saving undistorted BGR image (full) to file: {image_undistorted_full_file}")
    cv2.imwrite(image_undistorted_full_file, bgr_undistorted_full)


if __name__ == "__main__":
    _main()
