"""
Convert ZDF point cloud to CSV format.
"""

import zivid
import numpy as np


def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"
    filename_csv = "Zivid3D.csv"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Getting the point cloud
    point_cloud = frame.get_point_cloud()
    point_cloud = np.dstack(
        [
            point_cloud["x"],
            point_cloud["y"],
            point_cloud["z"],
            point_cloud["r"],
            point_cloud["g"],
            point_cloud["b"],
            point_cloud["contrast"],
        ]
    )
    # Flattening the point cloud
    flattened_point_cloud = point_cloud.reshape(-1, 7)
    # Just the points without color and contrast
    # point_cloud = np.dstack([point_cloud['x'],point_cloud['y'],point_cloud['z']])
    # flattened_point_cloud = point_cloud.reshape(-1,3)

    # Removing nans
    flattened_point_cloud = flattened_point_cloud[
        ~np.isnan(flattened_point_cloud[:, 0]), :
    ]

    print(f"Saving the frame to {filename_csv}")
    np.savetxt(filename_csv, flattened_point_cloud, delimiter=",", fmt="%.3f")


if __name__ == "__main__":
    _main()
