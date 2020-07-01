"""
Convert ZDF point cloud to PLY file format without Zivid Software.
Note: Zivid Sample Data files must be downloaded, see
https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/450363393/Sample+Data.
"""

import struct
from pathlib import Path
import numpy as np
from netCDF4 import Dataset

from utils.paths import get_sample_data_path


def write_ply_binary(fname, pts):
    """
    Function for writing PLY point cloud.

    Args:
        fname: file name of target.
        pts: point cloud points.

    """

    with open(fname, "wb") as file_pointer:
        line = "ply\n"
        file_pointer.write(line.encode("utf-8"))
        line = "format binary_little_endian 1.0\n"
        file_pointer.write(line.encode("utf-8"))
        line = "element vertex %d\n"
        file_pointer.write(line.encode("utf-8") % pts.shape[0])
        line = "property float x\n"
        file_pointer.write(line.encode("utf-8"))
        line = "property float y\n"
        file_pointer.write(line.encode("utf-8"))
        line = "property float z\n"
        file_pointer.write(line.encode("utf-8"))
        line = "property uchar red\n"
        file_pointer.write(line.encode("utf-8"))
        line = "property uchar green\n"
        file_pointer.write(line.encode("utf-8"))
        line = "property uchar blue\n"
        file_pointer.write(line.encode("utf-8"))
        line = "end_header\n"
        file_pointer.write(line.encode("utf-8"))

        for i in range(len(pts)):

            data = struct.pack(
                "<fffBBB",
                pts[i, 0],
                pts[i, 1],
                pts[i, 2],
                np.uint8(pts[i, 3]),
                np.uint8(pts[i, 4]),
                np.uint8(pts[i, 5]),
            )

            file_pointer.write(data)


def _main():

    filename_zdf = Path() / get_sample_data_path() / "Zivid3D.zdf"
    filename_ply = "Zivid3D.ply"

    print(f"Reading {filename_zdf} point cloud")
    with Dataset(filename_zdf) as data:
        # Extracting the point cloud
        xyz = data["data"]["pointcloud"][:, :, :]

        # Extracting the RGB image
        rgb = data["data"]["rgba_image"][:, :, :3]

    # Getting the point cloud
    point_cloud = np.dstack([xyz, rgb])

    # Replacing nans with zeros
    point_cloud[np.isnan(point_cloud[:, :, 2])] = 0

    # Flattening the point cloud
    flattened_point_cloud = point_cloud.reshape(-1, 6)

    print(f"Saving the frame to {filename_ply}")
    write_ply_binary(filename_ply, flattened_point_cloud)


if __name__ == "__main__":
    _main()
