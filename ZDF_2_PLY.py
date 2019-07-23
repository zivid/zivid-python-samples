"""
This example shows how to convert a Zivid point cloud from a .ZDF file format
to a .PLY file format.
"""

import zivid


def _main():
    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    FilenameZDF = "Zivid3D.zdf"
    FilenamePLY = "Zivid3D.ply"

    print("Reading ", FilenameZDF, " point cloud")
    frame = zivid.Frame(FilenameZDF)

    print("Saving the frame to ", FilenamePLY)
    frame.save(FilenamePLY)


if __name__ == "__main__":
    _main()
