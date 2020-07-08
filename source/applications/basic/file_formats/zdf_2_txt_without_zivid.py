"""
Convert ZDF point cloud to TXT format without Zivid Software.
Note: Zivid Sample Data files must be downloaded, see
https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/450363393/Sample+Data.
"""

from pathlib import Path
import numpy as np
from netCDF4 import Dataset

from utils.paths import get_sample_data_path


def _main():

    filename_zdf = Path() / get_sample_data_path() / "Zivid3D.zdf"
    filename_txt = "Zivid3D.txt"

    print(f"Reading {filename_zdf} point cloud")
    with Dataset(filename_zdf) as data:
        # Extracting the point cloud
        xyz = data["data"]["pointcloud"][:, :, :]

        # Extracting the RGB image
        rgb = data["data"]["rgba_image"][:, :, :3]

        # Extracting the SNR image
        snr = data["data"]["snr"][:, :]

    # Getting the point cloud
    point_cloud = np.dstack([xyz, rgb, snr])
    # Flattening the point cloud
    flattened_point_cloud = point_cloud.reshape(-1, 7)
    # Just the points without color and SNR
    # pc = np.dstack([xyz])
    # flattened_point_cloud = pc.reshape(-1,3)

    # Removing nans
    flattened_point_cloud = flattened_point_cloud[
        ~np.isnan(flattened_point_cloud[:, 0]), :
    ]

    print(f"Saving the frame to {filename_txt}")
    np.savetxt(filename_txt, flattened_point_cloud, delimiter=" ", fmt="%.3f")


if __name__ == "__main__":
    _main()
