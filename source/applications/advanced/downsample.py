"""
This example shows how to downsample point cloud from a ZDF file.

The ZDF files for this sample can be found under the main instructions for Zivid samples.
"""

from pathlib import Path
import zivid

from sample_utils.paths import get_sample_data_path
from sample_utils.display import display_pointcloud


def _main():

    app = zivid.Application()

    data_file = Path() / get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading ZDF frame from file: {data_file}")
    frame = zivid.Frame(data_file)

    point_cloud = frame.point_cloud()
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba")

    print(f"Before downsampling: {point_cloud.width * point_cloud.height} point cloud")

    display_pointcloud(xyz, rgba[:, :, 0:3])

    print("Downsampling point cloud")
    point_cloud.downsample(zivid.PointCloud.Downsampling.by2x2)
    xyz_donwsampled = point_cloud.copy_data("xyz")
    rgba_downsampled = point_cloud.copy_data("rgba")

    print(f"After downsampling: {point_cloud.width * point_cloud.height} point cloud")

    display_pointcloud(xyz_donwsampled, rgba_downsampled[:, :, 0:3])

    input("Press Enter to close...")


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
