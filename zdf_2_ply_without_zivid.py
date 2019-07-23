"""
Convert ZDF point cloud to PLY file format without Zivid Software.
"""

import numpy as np
import struct
from netCDF4 import Dataset


def write_ply_binary(fname, pts):

    with open(fname, "wb") as f:
        line = "ply\n"
        f.write(line.encode("utf-8"))
        line = "format binary_little_endian 1.0\n"
        f.write(line.encode("utf-8"))
        line = "element vertex %d\n"
        f.write(line.encode("utf-8") % pts.shape[0])
        line = "property float x\n"
        f.write(line.encode("utf-8"))
        line = "property float y\n"
        f.write(line.encode("utf-8"))
        line = "property float z\n"
        f.write(line.encode("utf-8"))
        line = "property uchar red\n"
        f.write(line.encode("utf-8"))
        line = "property uchar green\n"
        f.write(line.encode("utf-8"))
        line = "property uchar blue\n"
        f.write(line.encode("utf-8"))
        line = "end_header\n"
        f.write(line.encode("utf-8"))

        for i in range(len(pts)):

            s = struct.pack(
                "<fffBBB",
                pts[i, 0],
                pts[i, 1],
                pts[i, 2],
                np.uint8(pts[i, 3]),
                np.uint8(pts[i, 4]),
                np.uint8(pts[i, 5]),
            )

            f.write(s)


def _main():

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"
    filename_ply = "Zivid3D.ply"

    print(f"Reading {filename_zdf} point cloud")
    with Dataset(filename_zdf) as data:
        # Extracting the point cloud
        xyz = data["data"]["pointcloud"][:, :, :]

        # Extracting the RGB image
        rgb = data["data"]["rgba_image"][:, :, :3]

    # Getting the point cloud
    pc = np.dstack([xyz, rgb])

    # Replacing nans with zeros
    pc[np.isnan(pc[:, :, 2])] = 0

    # Flattening the point cloud
    pts = pc.reshape(-1, 6)

    print(f"Saving the frame to {filename_ply}")
    write_ply_binary(filename_ply, pts)


if __name__ == "__main__":
    _main()
