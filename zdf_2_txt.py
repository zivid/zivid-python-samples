"""
Convert ZDF point cloud to TXT format.
"""

import numpy as np
import zivid


def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"
    filename_txt = "Zivid3D.txt"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Getting the point cloud
    pc = frame.get_point_cloud()
    pc = np.dstack(
        [pc["x"], pc["y"], pc["z"], pc["r"], pc["g"], pc["b"], pc["contrast"]]
    )
    # Flattening the point cloud
    pts = pc.reshape(-1, 7)
    # Just the points without color and contrast
    # pc = np.dstack([pc['x'],pc['y'],pc['z']])
    # pts = pc.reshape(-1,3)

    # Removing nans
    pts = pts[~np.isnan(pts[:, 0]), :]

    print(f"Saving the frame to {filename_txt}")
    np.savetxt(filename_txt, pts, delimiter=",", fmt="%.3f")


if __name__ == "__main__":
    _main()
