"""
Import ZDF point cloud and visualize it.
Note: Zivid Sample Data files must be downloaded, see
https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/450363393/Sample+Data.
"""

import math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pptk
import zivid

from utils.paths import get_sample_data_path


def _display_rgb(rgb):
    """Display RGB image.

    Args:
        rgb: RGB image

    Returns None

    """
    plt.figure()
    plt.imshow(rgb)
    plt.title("RGB image")
    plt.show(block=False)


def _display_depthmap(xyz):
    """Create and display depthmap.

    Args:
        xyz: X, Y and Z images (point cloud co-ordinates)

    Returns None

    """
    plt.figure()
    plt.imshow(
        xyz[:, :, 2],
        vmin=np.nanmin(xyz[:, :, 2]),
        vmax=np.nanmax(xyz[:, :, 2]),
        cmap="jet",
    )
    plt.colorbar()
    plt.title("Depth map")
    plt.show(block=False)


def _get_mid_point(xyz):
    """Calculate mid point from average of the 100 centermost points.

    Args:
        xyz: X, Y and Z images (point cloud co-ordinates)

    Returns:
        mid_point: Calculated mid point

    """
    xyz_center_cube = xyz[
        int(xyz.shape[0] / 2 - 5) : int(xyz.shape[0] / 2 + 5),
        int(xyz.shape[1] / 2 - 5) : int(xyz.shape[1] / 2 + 5),
        :,
    ]
    return (
        np.nanmedian(xyz_center_cube[:, :, 0]),
        np.nanmedian(xyz_center_cube[:, :, 1]),
        np.nanmedian(xyz_center_cube[:, :, 2]),
    )


def _display_pointcloud(rgb, xyz):
    """Display point cloud.

    Display the provided point cloud `xyz`, and color it with `rgb`.

    We take the centermost co-ordinate as 'lookat' point. We assume that
    camera location is at azimuth -pi/2 and elevation -pi/2 relative to
    the 'lookat' point.

    Args:
        rgb: RGB image
        xyz: X, Y and Z images (point cloud co-ordinates)

    Returns None

    """
    mid_point = _get_mid_point(xyz)
    point_cloud_to_view = xyz
    point_cloud_to_view[np.isnan(xyz[:, :, 2])] = 0
    viewer = pptk.viewer(point_cloud_to_view)
    viewer.attributes(rgb.reshape(-1, 3) / 255.0)
    viewer.set(lookat=mid_point)
    viewer.set(phi=-math.pi / 2, theta=-math.pi / 2, r=mid_point[2])


def _main():

    app = zivid.Application()

    filename_zdf = Path() / get_sample_data_path() / "Zivid3D.zdf"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    point_cloud = frame.point_cloud().to_array()
    xyz = np.dstack([point_cloud["x"], point_cloud["y"], point_cloud["z"]])
    rgb = np.dstack([point_cloud["r"], point_cloud["g"], point_cloud["b"]])

    _display_rgb(rgb)

    _display_depthmap(xyz)

    _display_pointcloud(rgb, xyz)

    input("Press Enter to close...")


if __name__ == "__main__":
    _main()
