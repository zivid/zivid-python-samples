"""
This example shows how to import a Zivid point cloud from a .ZDF file without
Zivid Software.
"""

from netCDF4 import Dataset
from matplotlib import pyplot as plt
import numpy as np


def _main():

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    FilenameZDF = "Zivid3D.zdf"

    print("Reading ", FilenameZDF, " point cloud")
    data = Dataset(FilenameZDF, "r")

    # Extracting the point cloud
    pc = data["data"]["pointcloud"][:, :, :]

    # Extracting the RGB image
    image = data["data"]["rgba_image"][:, :, :]

    # Extracting the contrast image
    contrast = data["data"]["contrast"][:, :]

    # Closing the ZDF file
    data.close()

    # Displaying the RGB image
    plt.imshow(image)
    plt.show()

    # Displaying the Depth Image
    Z = pc[:, :, 2]
    plt.imshow(Z, vmin=np.nanmin(Z), vmax=np.nanmax(Z), cmap="jet")
    plt.colorbar()
    plt.show()


if __name__ == "__main__":
    _main()
