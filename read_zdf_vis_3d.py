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
    pts = pc.reshape(-1, 6)

    # Displaying the RGB image
    plt.figure()
    plt.imshow(rgb)
    plt.title("RGB image")
    plt.show()

    # Displaying the Depth Image
    Z = xyz[:, :, 2]
    plt.figure()
    plt.imshow(Z, vmin=np.nanmin(Z), vmax=np.nanmax(Z), cmap="jet")
    plt.colorbar()
    plt.title("Depth map")
    plt.show()

    # Displaying the point cloud
    plotxyzrgb(pts)


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
    input("Press Enter to close...")
