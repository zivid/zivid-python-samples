"""
Import ZDF point cloud and downsample it.
Note: Zivid Sample Data files must be downloaded, see
https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/450363393/Sample+Data.
"""

import math
from pathlib import Path
import numpy as np
import pptk
import zivid
from sample_utils.paths import get_sample_data_path


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


def _visualize_point_cloud(point_cloud):
    """Visualize point cloud.

    Visualize the provided point cloud `xyz`, and color it with `rgb`.

    We take the centermost co-ordinate as 'lookat' point. We assume that camera location is at azimuth -pi/2 and
    elevation -pi/2 relative to the 'lookat' point.

    Args:
        point_cloud: Zivid point cloud
    """
    xyz = point_cloud.copy_data("xyz")
    rgb = point_cloud.copy_data("rgba")[:, :, 0:3]

    mid_point = _get_mid_point(xyz)

    # Setting nans to zeros
    xyz[np.isnan(xyz[:, :, 2])] = 0

    viewer = pptk.viewer(xyz)
    viewer.attributes(rgb.reshape(-1, 3) / 255.0)
    viewer.set(lookat=mid_point)
    viewer.set(phi=-math.pi / 2, theta=-math.pi / 2, r=mid_point[2])


def _main():

    app = zivid.Application()

    filename_zdf = Path() / get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Getting the point cloud
    point_cloud = frame.point_cloud()

    print(f"Before downsampling: {point_cloud.width * point_cloud.height} point cloud")

    _visualize_point_cloud(point_cloud)

    # Downsampling the point cloud
    point_cloud.downsample(zivid.PointCloud.Downsampling.by2x2)    
    
    print(f"After downsampling: {point_cloud.width * point_cloud.height} point cloud")

    _visualize_point_cloud(point_cloud)

    input("Press Enter to close...")


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
