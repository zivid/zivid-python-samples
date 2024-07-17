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


def _transform_grid_to_calibration_board(
    grid: List[np.ndarray], transform_camera_to_checkerboard: np.ndarray
) -> List[np.ndarray]:
    """Transform a list of grid points to the camera frame.

    Args:
        grid: List of 4D points (X,Y,Z,W) for each corner in the checkerboard, in the checkerboard frame
        transform_camera_to_checkerboard: 4x4 transformation matrix

    Returns:
        List of 3D grid points in the camera frame

    """
    points_in_camera_frame = []
    for point in grid:
        transformed_point = transform_camera_to_checkerboard @ point
        points_in_camera_frame.append(transformed_point[:3])

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


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Capturing and estimating pose of the Zivid checkerboard in the camera frame")
    detection_result = zivid.calibration.detect_calibration_board(camera)
    if not detection_result.valid():
        raise RuntimeError("Calibration board not detected!")

    print("Estimating checkerboard pose")
    transform_camera_to_checkerboard = detection_result.pose().to_matrix()
    print(transform_camera_to_checkerboard)

    print("Creating a grid of 7 x 6 points (3D) with 30 mm spacing to match checkerboard corners")
    grid = _checkerboard_grid()

    print("Transforming the grid to the camera frame")
    points_in_camera_frame = _transform_grid_to_calibration_board(grid, transform_camera_to_checkerboard)

    print("Getting projector pixels (2D) corresponding to points (3D) in the camera frame")
    projector_pixels = zivid.projection.pixels_from_3d_points(camera, points_in_camera_frame)

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
        settings_2d = zivid.Settings2D()
        settings_2d.acquisitions.append(
            zivid.Settings2D.Acquisition(brightness=0.0, exposure_time=timedelta(microseconds=20000), aperture=2.83)
        )

        print("Capturing a 2D image with the projected image")
        frame_2d = projected_image.capture(settings_2d)

        captured_image_file = "CapturedImage.png"
        print(f"Saving the captured image: {captured_image_file}")
        frame_2d.image_bgra().save(captured_image_file)

        input("Press enter to stop projecting ...")

    print("Done")


if __name__ == "__main__":
    _main()
