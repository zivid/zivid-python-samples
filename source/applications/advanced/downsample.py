"""
This example shows how to downsample point cloud from a ZDF file.

The ZDF files for this sample can be found under the main instructions for Zivid samples.
"""

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

    Returns None

    """

    # Getting point cloud data
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba")
    xyzrgba = np.dstack([xyz, rgba])

    # Flattening point cloud data
    flattened_xyzrgba = xyzrgba.reshape(-1, 6)

    print("Visualizing point cloud")
    plotxyzrgb(flattened_xyzrgba)

    print("Visualizing RGB image")
    plt.figure()
    plt.imshow(rgba[:, :, 0:3])
    plt.title("RGB image")
    plt.show()

    print("Visualizing Depth map")
    plt.figure()
    plt.imshow(
        xyz[:, :, 2],
        vmin=np.nanmin(xyz[:, :, 2]),
        vmax=np.nanmax(xyz[:, :, 2]),
        cmap="jet",
    )
    plt.colorbar()
    plt.title("Depth map")
    plt.show()


def _main():

    app = zivid.Application()

    data_file = Path() / get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading ZDF frame from file: {data_file}")
    frame = zivid.Frame(data_file)

    point_cloud = frame.point_cloud()

    print(f"Before downsampling: {point_cloud.width * point_cloud.height} point cloud")

    _visualize_point_cloud(point_cloud)

    print("Downsampling point cloud")
    point_cloud.downsample(zivid.PointCloud.Downsampling.by2x2)

    print(f"After downsampling: {point_cloud.width * point_cloud.height} point cloud")

    _visualize_point_cloud(point_cloud)

    input("Press Enter to close...")


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
