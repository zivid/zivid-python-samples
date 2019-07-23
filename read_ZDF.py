"""
Import ZDF point cloud.
"""

import zivid
import numpy as np


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


if __name__ == "__main__":
    _main()
