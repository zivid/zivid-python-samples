"""
Illuminate checkerboard (Zivid Calibration Board) corners by getting checkerboard pose
from the API and transforming the desired points to projector pixel coordinates.

The checkerboard pose is determined first and then used to estimate the coordinates of corners
in the camera frame. These points are then passed to the API to get the corresponding projector pixels.
The projector pixel coordinates are then used to draw markers at the correct locations before displaying
the image using the projector.

"""

from datetime import timedelta
from typing import List, Tuple

import cv2
import numpy as np
import zivid


def _checkerboard_grid() -> List[np.ndarray]:
    """Create a list of points corresponding to the checkerboard corners in a Zivid calibration board.

    Returns:
        points: List of 4D points (X,Y,Z,W) for each corner in the checkerboard, in the checkerboard frame

    """
    x = np.arange(0, 7) * 30.0
    y = np.arange(0, 6) * 30.0

    xx, yy = np.meshgrid(x, y)
    z = np.zeros_like(xx)
    w = np.ones_like(xx)

    points = np.dstack((xx, yy, z, w)).reshape(-1, 4)

    return list(points)


def _transform_grid_to_camera_frame(
    grid: List[np.ndarray], camera_to_checkerboard_transform: np.ndarray
) -> List[np.ndarray]:
    """Transform a list of grid points to the camera frame.

    Args:
        grid: List of 4D points (X,Y,Z,W) for each corner in the checkerboard, in the checkerboard frame
        camera_to_checkerboard_transform: 4x4 transformation matrix

    Returns:
        List of 3D grid points in the camera frame

    """
    points_in_camera_frame = []
    for point_in_checkerboard_frame in grid:
        point_in_camera_frame = camera_to_checkerboard_transform @ point_in_checkerboard_frame
        points_in_camera_frame.append(point_in_camera_frame[:3])

    return points_in_camera_frame


def _draw_filled_circles(
    image: np.ndarray, positions: List[List[float]], circle_size_in_pixels: int, circle_color: Tuple[int, ...]
) -> None:
    """Draw a circle for each position in positions in the image.

    Args:
        image: Image to draw circles in
        positions: List of 2D positions (X,Y) to draw a circle in
        circle_size_in_pixels: Radius of circles
        circle_color: Color of circles (RGB, RGBA, BGR, BGRA etc.)

    """
    for position in positions:
        if np.nan not in position:
            point = (round(position[0]), round(position[1]))
            cv2.circle(image, point, circle_size_in_pixels, circle_color, -1)


def _get_2d_capture_settings(camera: zivid.Camera) -> zivid.Settings2D:
    """Get 2D capture settings based on the camera model.

    Args:
        camera: Zivid camera

    Raises:
        ValueError: If the camera model is not supported

    Returns:
        2D capture settings

    """
    settings_2d = zivid.Settings2D(
        acquisitions=[
            zivid.Settings2D.Acquisition(brightness=0.0, exposure_time=timedelta(microseconds=20000), aperture=2.83)
        ]
    )

    model = camera.info.model
    if model in [
        zivid.CameraInfo.Model.zividTwo,
        zivid.CameraInfo.Model.zividTwoL100,
        zivid.CameraInfo.Model.zivid2PlusM130,
        zivid.CameraInfo.Model.zivid2PlusM60,
        zivid.CameraInfo.Model.zivid2PlusL110,
    ]:
        settings_2d.sampling.color = zivid.Settings2D.Sampling.Color.rgb
    elif model in [
        zivid.CameraInfo.Model.zivid2PlusMR130,
        zivid.CameraInfo.Model.zivid2PlusMR60,
        zivid.CameraInfo.Model.zivid2PlusLR110,
    ]:
        settings_2d.sampling.color = zivid.Settings2D.Sampling.Color.grayscale
    else:
        raise ValueError(f"Unsupported camera model '{model}'")

    return settings_2d


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Capturing and estimating pose of the Zivid checkerboard in the camera frame")
    detection_result = zivid.calibration.detect_calibration_board(camera)
    if not detection_result.valid():
        raise RuntimeError(f"Calibration board not detected! {detection_result.status_description()}")

    print("Estimating checkerboard pose")
    camera_to_checkerboard_transform = detection_result.pose().to_matrix()
    print(camera_to_checkerboard_transform)

    print("Creating a grid of 7 x 6 points (3D) with 30 mm spacing to match checkerboard corners")
    grid_points_in_checkerboard_frame = _checkerboard_grid()

    print("Transforming the grid to the camera frame")
    grid_points_in_camera_frame = _transform_grid_to_camera_frame(
        grid_points_in_checkerboard_frame, camera_to_checkerboard_transform
    )

    print("Getting projector pixels (2D) corresponding to points (3D) in the camera frame")
    projector_pixels = zivid.projection.pixels_from_3d_points(camera, grid_points_in_camera_frame)

    print("Retrieving the projector resolution that the camera supports")
    projector_resolution = zivid.projection.projector_resolution(camera)

    print(f"Creating a blank projector image with resolution: {projector_resolution}")
    background_color = (0, 0, 0, 255)
    projector_image = np.full(
        (projector_resolution[0], projector_resolution[1], len(background_color)), background_color, dtype=np.uint8
    )

    print("Drawing circles on the projector image for each grid point")
    circle_color = (0, 255, 0, 255)
    _draw_filled_circles(projector_image, projector_pixels, 2, circle_color)

    projector_image_file = "ProjectorImage.png"
    print(f"Saving the projector image to file: {projector_image_file}")
    cv2.imwrite(projector_image_file, projector_image)

    print("Displaying the projector image")

    with zivid.projection.show_image_bgra(camera, projector_image) as projected_image:
        settings_2d = _get_2d_capture_settings(camera)

        print("Capturing a 2D image with the projected image")
        frame_2d = projected_image.capture_2d(settings_2d)

        captured_image_file = "CapturedImage.png"
        print(f"Saving the captured image: {captured_image_file}")
        frame_2d.image_bgra_srgb().save(captured_image_file)

        input("Press enter to stop projecting ...")

    print("Done")


if __name__ == "__main__":
    _main()
