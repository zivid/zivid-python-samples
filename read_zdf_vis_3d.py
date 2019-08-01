"""
Import ZDF point cloud and visualize it.
"""

import zivid
import numpy as np
import matplotlib.pyplot as plt
from vtk_visualizer import plotxyzrgb


def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Getting the point cloud
    pc = frame.get_point_cloud()
    xyz = np.dstack([pc["x"], pc["y"], pc["z"]])
    rgb = np.dstack([pc["r"], pc["g"], pc["b"]])
    pc = np.dstack([xyz, rgb])

    # Flattening the point cloud
    flattened_point_cloud = pc.reshape(-1, 6)

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


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
    input("Press Enter to close...")
