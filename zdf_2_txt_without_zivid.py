"""
Convert ZDF point cloud to TXT format without Zivid Software.
"""

import numpy as np
from netCDF4 import Dataset


def _main():

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"
    filename_txt = "Zivid3D.txt"

    print(f"Reading {filename_zdf} point cloud")
    with Dataset(filename_zdf) as data:
        # Extracting the point cloud
        xyz = data["data"]["pointcloud"][:, :, :]

        # Extracting the RGB image
        rgb = data["data"]["rgba_image"][:, :, :3]

        # Extracting the contrast image
        contrast = data["data"]["contrast"][:, :]

    # Getting the point cloud
    pc = np.dstack([xyz, rgb, contrast])
    # Flattening the point cloud
    pts = pc.reshape(-1, 7)
    # Just the points without color and contrast
    # pc = np.dstack([xyz])
    # pts = pc.reshape(-1,3)

    # Removing nans
    pts = pts[~np.isnan(pts[:, 0]), :]

    print(f"Saving the frame to {filename_txt}")
    np.savetxt(filename_txt, pts, delimiter=" ", fmt="%.3f")


if __name__ == "__main__":
    _main()
