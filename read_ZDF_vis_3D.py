"""
This example shows how to import a Zivid point cloud from a .ZDF file and
visualize it using vtk_visualizer (point cloud) and matplotlib (RGB image and
Depth map).
"""

import zivid
import numpy as np
import matplotlib.pyplot as plt
from vtk_visualizer import *


def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    FilenameZDF = "Zivid3D.zdf"

    print("Reading ", FilenameZDF, " point cloud")
    frame = zivid.Frame(FilenameZDF)

    pc = frame.get_point_cloud()
    xyz = np.dstack([pc["x"], pc["y"], pc["z"]])
    image = np.dstack([pc["r"], pc["g"], pc["b"]])

    pc = np.dstack([xyz, image])
    pts = pc.reshape(-1, 6)

    # Plot them
    plotxyzrgb(pts)

    print("Displaying the RGB image and the Depth map")

    plt.figure()
    plt.imshow(image)
    plt.title("RGB image")

    plt.figure()
    plt.imshow(
        xyz[:, :, 2],
        vmin=np.nanmin(xyz[:, :, 2]),
        vmax=np.nanmax(xyz[:, :, 2]),
        cmap="jet",
    )
    plt.colorbar()
    plt.title("Depth map")


if __name__ == "__main__":
    _main()
