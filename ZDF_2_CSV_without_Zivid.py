"""
This example shows how to convert a Zivid point cloud from a .ZDF file format
to a .CSV file format without Zivid Software.
"""

import numpy as np
from netCDF4 import Dataset
from math import ceil

def _main():
    
    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    FilenameZDF = "Zivid3D.zdf"
    FilenameCSV = "Zivid3D.csv"
    
    print("Reading ", FilenameZDF, " point cloud" )
    data = Dataset(FilenameZDF)
    
    # Extracting the point cloud
    xyz = data["data"]["pointcloud"][:, :, :]
    
    # Extracting the RGB image
    image = data["data"]["rgba_image"][:, :, :3]
    
    # Extracting the contrast image
    contrast = data["data"]["contrast"][:, :]
    
    # Closing the ZDF file
    data.close()
    
    # Disorganizing the point cloud
    pc = np.dstack([xyz, image, contrast])
    pts = pc.reshape(-1, 7)
    # Just the points without color and contrast
    # pc = np.dstack([xyz])
    # pts = pc.reshape(-1,3)
    
    # Removing nans
    pts = pts[~np.isnan(pts[:, 0]), :]
    
    # Saving to a .CSV file format
    parts = ceil(len(pts) / 1000000)
    np.savetxt(FilenameCSV, pts, delimiter=",", fmt="%.3f")
    if parts > 1:
        for x in range(0, parts):
            index = FilenameCSV.find(".")
            Filename = FilenameCSV[:index] + "_part_" + str(x + 1) + FilenameCSV[index:]
            np.savetxt(
                Filename, pts[x * 1000000 : (x + 1) * 1000000, :], delimiter=",", fmt="%.3f"
            )

if __name__ == "__main__":
    _main()