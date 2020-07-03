"""
Import ZDF point cloud and downsample it.
Note: Zivid Sample Data files must be downloaded, see
https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/450363393/Sample+Data.
"""

from math import fmod
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from vtk_visualizer import plotxyzrgb
import zivid

from utils.paths import get_sample_data_path


def _gridsum(matrix, downsampling_factor):
    """Reshape and sum in second direction.

    Args:
        matrix: Matrix to be reshaped and summed in second direction.
        downsampling_factor: the denominator of a fraction that represents the
            size of the downsampled point cloud relative to the original point
            cloud, e.g. 2 - one-half, 3 - one-third, 4 one-quarter, etc.

    Returns:
        Matrix reshaped and summed in second direction.
    """
    return _sumline(
        np.transpose(_sumline(matrix, downsampling_factor)), downsampling_factor
    )


def _sumline(matrix, downsampling_factor):
    """Reshape and sum in first direction.

    Args:
        matrix: Matrix to be reshaped and summed in first direction.
        downsampling_factor: the denominator of a fraction that represents the
            size of the downsampled point cloud relative to the original point
            cloud, e.g. 2 - one-half, 3 - one-third, 4 one-quarter, etc.

    Returns:
        Matrix reshaped and summed in first direction.
    """
    return np.transpose(
        np.nansum(
            np.transpose(np.transpose(matrix).reshape(-1, downsampling_factor)), 0
        ).reshape(
            int(np.shape(np.transpose(matrix))[0]),
            int(np.shape(np.transpose(matrix))[1] / downsampling_factor),
        )
    )


def _downsample(xyz, rgb, contrast, downsampling_factor):
    """Function for downsampling a Zivid point cloud.

    Args:
        xyz: Point cloud.
        rgb: Color image.
        contrast: Contrast image.
        downsampling_factor: The denominator of a fraction that represents the
            size of the downsampled point cloud relative to the original point
            cloud, e.g. 2 - one-half, 3 - one-third, 4 one-quarter, etc.

    Raises:
        ValueError: If downsampling factor is not correct.

    Returns:
        Tuple of downsampled point cloud and color image.
    """

    # Checking if downsampling_factor is ok
    if fmod(rgb.shape[0], downsampling_factor) or fmod(
        rgb.shape[1], downsampling_factor
    ):
        raise ValueError(
            "Downsampling factor has to be a factor of point cloud width (1920) and height (1200)."
        )

    rgb_new = np.zeros(
        (
            int(rgb.shape[0] / downsampling_factor),
            int(rgb.shape[1] / downsampling_factor),
            3,
        ),
        dtype=np.uint8,
    )
    for i in range(3):
        rgb_new[:, :, i] = (
            (np.transpose(_gridsum(rgb[:, :, i], downsampling_factor)))
            / (downsampling_factor * downsampling_factor)
        ).astype(np.uint8)

    contrast[np.isnan(xyz[:, :, 2])] = 0
    contrast_weight = _gridsum(contrast[:, :, 0], downsampling_factor)

    x_initial = np.zeros((int(xyz.shape[0]), int(xyz.shape[1]), 1), dtype=np.float32)
    y_initial = np.zeros((int(xyz.shape[0]), int(xyz.shape[1]), 1), dtype=np.float32)
    z_initial = np.zeros((int(xyz.shape[0]), int(xyz.shape[1]), 1), dtype=np.float32)

    x_initial[:, :, 0] = xyz[:, :, 0]
    y_initial[:, :, 0] = xyz[:, :, 1]
    z_initial[:, :, 0] = xyz[:, :, 2]

    x_new = np.transpose(
        np.divide(
            _gridsum((np.multiply(x_initial, contrast))[:, :, 0], downsampling_factor),
            contrast_weight,
        )
    )
    y_new = np.transpose(
        np.divide(
            _gridsum((np.multiply(y_initial, contrast))[:, :, 0], downsampling_factor),
            contrast_weight,
        )
    )
    z_new = np.transpose(
        np.divide(
            _gridsum((np.multiply(z_initial, contrast))[:, :, 0], downsampling_factor),
            contrast_weight,
        )
    )

    xyz_new = np.dstack([x_new, y_new, z_new])

    return xyz_new, rgb_new


def _main():

    app = zivid.Application()

    filename_zdf = Path() / get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Getting the point cloud
    point_cloud = frame.point_cloud().to_array()
    xyz = np.dstack([point_cloud["x"], point_cloud["y"], point_cloud["z"]])
    rgb = np.dstack([point_cloud["r"], point_cloud["g"], point_cloud["b"]])
    contrast = np.dstack([point_cloud["contrast"]])

    # Downsampling the point cloud
    downsampling_factor = 4
    [xyz_new, rgb_new] = _downsample(xyz, rgb, contrast, downsampling_factor)

    # Getting the point cloud
    point_cloud = np.dstack([xyz_new, rgb_new])

    # Flattening the point cloud
    flattened_point_cloud = point_cloud.reshape(-1, 6)

    # Displaying the RGB image
    plt.figure()
    plt.imshow(rgb_new)
    plt.title("RGB image")
    plt.show()

    # Displaying the Depth map
    plt.figure()
    plt.imshow(
        xyz_new[:, :, 2],
        vmin=np.nanmin(xyz_new[:, :, 2]),
        vmax=np.nanmax(xyz_new[:, :, 2]),
        cmap="jet",
    )
    plt.colorbar()
    plt.title("Depth map")
    plt.show()

    # Displaying the point cloud
    plotxyzrgb(flattened_point_cloud)

    input("Press Enter to close...")


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
