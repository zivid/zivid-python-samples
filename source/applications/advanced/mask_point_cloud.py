"""
This example shows how to read point cloud data from a ZDF file, apply a binary mask, and visualize it.

The ZDF file for this sample can be found under the main instructions for Zivid samples.
"""

import math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pptk
import zivid

from sample_utils.paths import get_sample_data_path


def _display_rgb(rgb, title):
    """Display RGB image.

    Args:
        rgb: RGB image (HxWx3 darray)
        title: Image title

    Returns None

    """
    plt.figure()
    plt.imshow(rgb)
    plt.title(title)
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
        cmap="viridis",
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
    offset = 5
    xyz_center_cube = xyz[
        int(xyz.shape[0] / 2 - offset) : int(xyz.shape[0] / 2 + offset),
        int(xyz.shape[1] / 2 - offset) : int(xyz.shape[1] / 2 + offset),
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

    data_file = Path() / get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading ZDF frame from file: {data_file}")
    frame = zivid.Frame(data_file)

    point_cloud = frame.point_cloud()
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba")

    pixels_to_display = 300
    print(f"Generating binary mask of central {pixels_to_display} x {pixels_to_display} pixels")
    mask = np.zeros((rgba.shape[0], rgba.shape[1]), np.bool)
    height = frame.point_cloud().height
    width = frame.point_cloud().width
    h_min = int((height - pixels_to_display) / 2)
    h_max = int((height + pixels_to_display) / 2)
    w_min = int((width - pixels_to_display) / 2)
    w_max = int((width + pixels_to_display) / 2)
    mask[h_min:h_max, w_min:w_max] = 1

    _display_rgb(rgba[:, :, 0:3], "RGB image")

    _display_depthmap(xyz)
    _display_pointcloud(rgba[:, :, 0:3], xyz)
    input("Press Enter to continue...")

    print("Masking point cloud")
    xyz_masked = xyz.copy()
    xyz_masked[mask == 0] = np.nan

    _display_depthmap(xyz_masked)
    _display_pointcloud(rgba[:, :, 0:3], xyz_masked)
    input("Press Enter to close...")


if __name__ == "__main__":
    _main()
