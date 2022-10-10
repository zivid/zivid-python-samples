"""
Downsample point cloud from a ZDF file.

The ZDF files for this sample can be found under the main instructions for Zivid samples.

"""

from pathlib import Path

import zivid
from sample_utils.display import display_pointcloud
from sample_utils.paths import get_sample_data_path


def _main():

    with zivid.Application():

        data_file = Path() / get_sample_data_path() / "Zivid3D.zdf"
        print(f"Reading ZDF frame from file: {data_file}")
        frame = zivid.Frame(data_file)

        point_cloud = frame.point_cloud()
        xyz = point_cloud.copy_data("xyz")
        rgba = point_cloud.copy_data("rgba")

        print(f"Before downsampling: {point_cloud.width * point_cloud.height} point cloud")

        display_pointcloud(xyz, rgba[:, :, 0:3])

        print("Downsampling point cloud")
        print("This does not modify the current point cloud but returns")
        print("the downsampled point cloud as a new point cloud instance.")
        downsampled_point_cloud = point_cloud.downsampled(zivid.PointCloud.Downsampling.by2x2)

        print(f"After downsampling: {downsampled_point_cloud.width * downsampled_point_cloud.height} point cloud")

        print("Downsampling point cloud (in-place)")
        print("This modifies the current point cloud.")
        point_cloud.downsample(zivid.PointCloud.Downsampling.by2x2)

        xyz_donwsampled = point_cloud.copy_data("xyz")
        rgba_downsampled = point_cloud.copy_data("rgba")

        print(f"After downsampling: {point_cloud.width * point_cloud.height} point cloud")

        display_pointcloud(xyz_donwsampled, rgba_downsampled[:, :, 0:3])


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
