"""
Capture Zivid point clouds, compute normals and print a subset.

For scenes with high dynamic range we combine multiple acquisitions to get an HDR point cloud.

"""

import numpy as np
import zivid


def _print_normals(radius: int, normals: np.ndarray) -> None:
    """Print normal XYZ values of the 10 x 10 central pixels.

    Args:
        radius: Half of the width and height of the pixel area, e.g., radius of 5 results in 10 x 10 pixels.
        normals: XYZ values of each normal

    """
    line_separator = "-" * 50
    num_of_rows = normals.shape[0]
    num_of_cols = normals.shape[1]
    print(line_separator)
    for row in range(int(num_of_rows / 2 - radius), int(num_of_rows / 2 + radius)):
        for col in range(int(num_of_cols / 2 - radius), int(num_of_cols / 2 + radius)):
            normal_string = f"Normals ({row}, {col}): ["
            normal_string += f"x: {normals[row, col, 0]:.3} ".ljust(12)
            normal_string += f"y: {normals[row, col, 1]:.3} ".ljust(12)
            normal_string += f"z: {normals[row, col, 2]:.3} ".ljust(12)
            normal_string += "]"
            print(normal_string)
    print(line_separator)


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings")
    settings = zivid.Settings(acquisitions=[zivid.Settings.Acquisition(aperture=fnum) for fnum in (5.66, 4.00, 2.83)])

    print("Capturing frame (HDR)")
    frame = camera.capture_3d(settings)
    point_cloud = frame.point_cloud()

    print("Computing normals and copying them to CPU memory")
    normals = point_cloud.copy_data("normals")

    radius_of_pixels_to_print = 5
    print("Printing normals for the central ")
    print(f"{radius_of_pixels_to_print * 2} x {radius_of_pixels_to_print * 2} pixels")
    _print_normals(radius_of_pixels_to_print, normals)


if __name__ == "__main__":
    _main()
