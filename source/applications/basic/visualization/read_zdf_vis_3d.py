"""
Read point cloud data from a ZDF file and visualize it.

The ZDF file for this sample can be found under the main instructions for Zivid samples.
"""

from pathlib import Path

import zivid
from sample_utils.display import display_depthmap, display_pointcloud, display_rgb
from sample_utils.paths import get_sample_data_path


def _main():

    with zivid.Application():

        filename_zdf = Path() / get_sample_data_path() / "Zivid3D.zdf"

        print(f"Reading {filename_zdf} point cloud")
        frame = zivid.Frame(filename_zdf)

        point_cloud = frame.point_cloud()
        xyz = point_cloud.copy_data("xyz")
        rgba = point_cloud.copy_data("rgba")

        display_rgb(rgba[:, :, 0:3], block=False)

        display_depthmap(xyz, block=True)

        display_pointcloud(xyz, rgba[:, :, 0:3])


if __name__ == "__main__":
    _main()
