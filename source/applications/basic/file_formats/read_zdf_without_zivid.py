"""
Import ZDF point cloud without Zivid Software.
Note: Zivid Sample Data files must be downloaded, see
https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/450363393/Sample+Data.
"""

from pathlib import Path
from netCDF4 import Dataset
from matplotlib import pyplot as plt
import numpy as np

from utils.paths import get_sample_data_path


def _main():

    filename_zdf = Path() / get_sample_data_path() / "Zivid3D.zdf"

    print(f"Reading {filename_zdf} point cloud")
    with Dataset(filename_zdf) as data:
        # Extracting the point cloud
        xyz = data["data"]["pointcloud"][:, :, :]

        # Extracting the RGB image
        rgb = data["data"]["rgba_image"][:, :, :3]

        # Extracting the SNR image
        snr = data["data"]["snr"][:, :]

    # Displaying the RGB image
    plt.figure()
    plt.imshow(rgb)
    plt.title("RGB image")
    plt.show()

    # Displaying the Depth Image
    plt.imshow(
        xyz[:, :, 2],
        vmin=np.nanmin(xyz[:, :, 2]),
        vmax=np.nanmax(xyz[:, :, 2]),
        cmap="jet",
    )
    plt.colorbar()
    plt.title("Depth map")
    plt.show()


if __name__ == "__main__":
    _main()
