"""
Import ZDF point cloud and visualize it.
"""

import numpy as np
import matplotlib.pyplot as plt
import zivid
from vtk_visualizer import plotxyzrgb


def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Getting the point cloud
    point_cloud = frame.get_point_cloud()
    xyz = np.dstack([point_cloud["x"], point_cloud["y"], point_cloud["z"]])
    rgb = np.dstack([point_cloud["r"], point_cloud["g"], point_cloud["b"]])

    # Flattening the point cloud
    flattened_point_cloud = point_cloud.reshape(-1, 6)

    # Displaying the RGB image
    plt.figure()
    plt.imshow(rgb)
    plt.title("RGB image")
    plt.show()

    # Displaying the Depth map
    plt.figure()
    plt.imshow(
        xyz[:, :, 2],
        vmin=np.nanmin(xyz[:, :, 2]),
        vmax=np.nanmax(xyz[:, :, 2]),
        cmap="jet",
    )
    plt.colorbar()
    plt.title("Depth map")
    plt.show()

    # Displaying the point cloud
    plotxyzrgb(flattened_point_cloud)

    input("Press Enter to close...")


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
