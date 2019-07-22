"""
This example shows how to convert a Zivid point cloud from a .ZDF file format
to a .TXT file format.
"""

import zivid
import numpy as np
from math import ceil

def _main():

    app = zivid.Application()
    
    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    FilenameZDF = "Zivid3D.zdf"
    FilenameTXT = "Zivid3D.txt"
    
    print("Reading ", FilenameZDF, " point cloud")
    frame = zivid.Frame(FilenameZDF)
    
    pc = frame.get_point_cloud()

    # Disorganizing the point cloud
    pc = np.dstack([pc['x'],pc['y'],pc['z'],pc['r'],pc['g'],pc['b'],pc['contrast']])
    pts = pc.reshape(-1, 7)
    # Just the points without color and contrast
    # pc = np.dstack([pc['x'],pc['y'],pc['z']])
    # pts = pc.reshape(-1,3)

    # Removing nans
    pts = pts[~np.isnan(pts[:, 0]), :]

    print("Saving to a .TXT file format")
    parts = ceil(len(pts) / 1000000)
    np.savetxt(FilenameTXT, pts, delimiter=",", fmt="%.3f")
    if parts > 1:
        for x in range(0, parts):
            index = FilenameTXT.find(".")
            Filename = FilenameTXT[:index] + "_part_" + str(x + 1) + FilenameTXT[index:]
            np.savetxt(
                Filename, pts[x * 1000000 : (x + 1) * 1000000, :], delimiter=",", fmt="%.3f"
            )
    
if __name__ == "__main__":
    _main()
