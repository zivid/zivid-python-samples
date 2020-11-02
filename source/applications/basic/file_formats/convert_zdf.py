"""
This exampe shows how to convert point cloud data from a ZDF file to your preferred format.

Example: $ python convert_zdf.py --ply Zivid3D.zdf

Available formats:
    .ply - Polygon File Format
    .csv,.txt - [X, Y, Z, r, g, b, SNR]
    .png,.jpg,.bmp,.tiff - 2D RGB image
"""

import argparse
from pathlib import Path
import numpy as np
import cv2
import zivid


def _options():
    parser = argparse.ArgumentParser(
        description="Convert from ZDF to your preferred format\
            \nExample:\n\t $ python convert_zdf.py --ply Zivid3D.zdf",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("filename", help="File to convert", default="Zivid3D.zdf")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ply", action="store_true", help="Convert to PLY")
    group.add_argument("--csv", action="store_true", help="Convert to CSV")
    group.add_argument("--txt", action="store_true", help="Convert to text")
    group.add_argument("--jpg", action="store_true", help="Convert to JPEG (3D->2D)")
    group.add_argument("--tiff", action="store_true", help="Convert to TIFF (3D->2D)")
    group.add_argument(
        "--png",
        action="store_true",
        help="Convert to Portable Network Graphics (3D->2D)",
    )
    group.add_argument("--bmp", action="store_true", help="Convert to Windows bitmap (3D->2D)")

    return parser.parse_args()


def _flatten_point_cloud(point_cloud):
    """Convert from point cloud to flattened point cloud (with numpy).

    Args:
        point_cloud: a handle to point cloud in the GPU memory

    Returns:
        2D numpy array, with 8 columns and npixels rows

    """
    # Convert to numpy 3D array
    point_cloud = np.dstack(
        [point_cloud.copy_data("xyz"), point_cloud.copy_data("rgba"), point_cloud.copy_data("snr")]
    )
    # Flattening the point cloud
    flattened_point_cloud = point_cloud.reshape(-1, 8)

    # Removing nans
    return flattened_point_cloud[~np.isnan(flattened_point_cloud[:, 0]), :]


def _convert_2_ply(frame, file_name: str):
    """Convert from frame to ply.

    Args:
        frame: A frame captured by a Zivid camera.
        file_name: File name without extension

    Returns None

    """
    print(f"Saving the frame to {file_name}.ply")
    frame.save(f"{file_name}.ply")


def _convert_2_csv(point_cloud, file_name: str):
    """Convert from point cloud to csv or txt.

    Args:
        point_cloud: a handle to point cloud in the GPU memory
        file_name: File name with extension

    Returns None

    """
    print(f"Saving the frame to {file_name}")
    np.savetxt(file_name, _flatten_point_cloud(point_cloud), delimiter=",", fmt="%.3f")


def _convert_2_2d(point_cloud, file_name: str):
    """Convert from point cloud to 2D image.

    Args:
        point_cloud: a handle to point cloud in the GPU memory
        file_name: File name without extension

    Returns None

    """
    print(f"Saving the frame to {file_name}")
    rgba = point_cloud.copy_data("rgba")
    bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
    cv2.imwrite(file_name, bgr)


def _main():
    user_options = _options()

    file_path = Path(user_options.filename)
    if not file_path.exists():
        raise FileNotFoundError(f"{user_options.filename} does not exist")

    app = zivid.Application()

    print(f"Reading point cloud from file: {user_options.filename}")
    frame = zivid.Frame(user_options.filename)

    point_cloud = frame.point_cloud()

    if user_options.ply:
        _convert_2_ply(frame, file_path.stem)

    elif user_options.csv:
        _convert_2_csv(point_cloud, file_path.stem + ".csv")

    elif user_options.txt:
        _convert_2_csv(point_cloud, file_path.stem + ".txt")

    elif user_options.png:
        _convert_2_2d(point_cloud, file_path.stem + ".png")

    elif user_options.jpg:
        _convert_2_2d(point_cloud, file_path.stem + ".jpg")

    elif user_options.bmp:
        _convert_2_2d(point_cloud, file_path.stem + ".bmp")

    elif user_options.tiff:
        _convert_2_2d(point_cloud, file_path.stem + ".tiff")


if __name__ == "__main__":
    _main()
