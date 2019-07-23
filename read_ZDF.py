"""
This example shows how to import a Zivid point cloud from a .ZDF file.
"""

import zivid
import numpy as np


def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    FilenameZDF = "Zivid3D.zdf"

    print("Reading ", FilenameZDF, " point cloud")
    frame = zivid.Frame(FilenameZDF)

    # Getting the point cloud
    pc = frame.get_point_cloud()
    xyz = np.dstack([pc["x"], pc["y"], pc["z"]])
    image = np.dstack([pc["r"], pc["g"], pc["b"]])


if __name__ == "__main__":
    _main()
