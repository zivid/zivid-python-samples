"""
Import ZDF point cloud without Zivid Software.
"""

from netCDF4 import Dataset
from matplotlib import pyplot as plt
import numpy as np


def _main():

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"

    print(f"Reading {filename_zdf} point cloud")
    with Dataset(filename_zdf) as data:
        # Extracting the point cloud
        xyz = data["data"]["pointcloud"][:, :, :]

        # Extracting the RGB image
        rgb = data["data"]["rgba_image"][:, :, :3]

        # Extracting the contrast image
        contrast = data["data"]["contrast"][:, :]

    # Displaying the RGB image
    plt.imshow(rgb)
    plt.show()

    # Displaying the Depth Image
    plt.imshow(xyz[:, :, 2], vmin=np.nanmin(xyz[:, :, 2]), vmax=np.nanmax(xyz[:, :, 2]), cmap="jet")
    plt.colorbar()
    plt.show()


if __name__ == "__main__":
    _main()
