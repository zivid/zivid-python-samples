"""
This example shows how to convert a Zivid point cloud from a .ZDF file format
to a .PLY file format without Zivid Software.
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
    FilenameZDF = "Zivid3D.zdf"
    FilenamePLY = "Zivid3D.ply"

    print("Reading ", FilenameZDF, " point cloud")
    data = Dataset(FilenameZDF)

    # Extracting the point cloud
    xyz = data["data"]["pointcloud"][:, :, :]

    # Extracting the RGB image
    image = data["data"]["rgba_image"][:, :, :3]

    # Closing the ZDF file
    data.close()

    # Disorganizing the point cloud
    pc = np.dstack([xyz, image])

    # Replacing nans with zeros
    pc[np.isnan(pc[:, :, 2])] = 0
    pts = pc.reshape(-1, 6)

    # Saving to a .PLY file format
    write_ply_binary(FilenamePLY, pts)


if __name__ == "__main__":
    _main()
