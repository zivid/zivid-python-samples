"""
This example shows how to import, display and iterate over a Zivid point cloud from a .ZDF
file.
"""

import numpy as np
import zivid


def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Extracting point cloud from the frame
    point_cloud = frame.get_point_cloud()
    xyz = np.dstack([point_cloud["x"], point_cloud["y"], point_cloud["z"]])
    rgb = np.dstack([point_cloud["r"], point_cloud["g"], point_cloud["b"]])
    contrast = np.dstack([point_cloud["contrast"]])

    print(f"Point cloud information:")
    print(f"Number of points: {point_cloud.size}")
    print(f"Height: {point_cloud.height}, Width: {point_cloud.width}")

    # Iterating over the point cloud and displaying (X, Y, Z, R, G, B, Contrast)
    for i in range(0, point_cloud.height):
        for j in range(0, point_cloud.width):
            print(
                f"Values at pixel ({i} , {j}): X:{xyz[i,j]} Y:{xyz[i,j]} Z:{xyz[i,j]}\
                    R:{rgb[i,j]} G:{rgb[i,j]} B:{rgb[i,j]} Contrast:{contrast}"
            )


if __name__ == "__main__":
    _main()
