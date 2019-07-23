"""
Convert ZDF point cloud to PLY file format.
"""

import zivid


def _main():
    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"
    filename_ply = "Zivid3D.ply"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    print(f"Saving the frame to {filename_ply}")
    frame.save(filename_ply)


if __name__ == "__main__":
    _main()
