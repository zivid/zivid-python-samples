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
from sample_utils.paths import get_sample_data_path


def _visualize_point_cloud(point_cloud):
    """Visualize point cloud, rgb image, and depth map.

    Args:
        point_cloud: Zivid point cloud
    """

    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba")

    # Getting the point cloud
    xyzrgba = np.dstack([xyz, rgba])

    # Flattening the point cloud
    flattened_xyzrgba = xyzrgba.reshape(-1, 6)

    # Displaying the point cloud
    plotxyzrgb(flattened_xyzrgba)

    # Displaying the RGB image
    plt.figure()
    plt.imshow(rgba[:, :, 0:3])
    plt.title("RGB image")
    plt.show()

    # Displaying the Depth map
    plt.figure()
    plt.imshow(
        xyz[:, :, 2], vmin=np.nanmin(xyz[:, :, 2]), vmax=np.nanmax(xyz[:, :, 2]), cmap="jet",
    )
    plt.colorbar()
    plt.title("Depth map")
    plt.show()


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
