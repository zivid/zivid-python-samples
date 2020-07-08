"""
This example shows how to import, display and iterate over a Zivid point cloud from a .ZDF
file.
Note: Zivid Sample Data files must be downloaded, see
https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/450363393/Sample+Data.
"""

from pathlib import Path
import numpy as np
import zivid

from utils.paths import get_sample_data_path


def _main():

    app = zivid.Application()

    filename_zdf = Path() / get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Extracting point cloud from the frame
    xyzrgba = frame.point_cloud().copy_data("xyzrgba")
    xyz = np.dstack([xyzrgba["x"], xyzrgba["y"], xyzrgba["z"]])
    rgb = np.dstack([xyzrgba["r"], xyzrgba["g"], xyzrgba["b"]])
    snr = frame.point_cloud().copy_data("snr")

    height = frame.point_cloud().height
    width = frame.point_cloud().width

    print("Point cloud information:")
    print(f"Number of points: {height * width}")
    print(f"Height: {height}, Width: {width}")

    # Iterating over the point cloud and displaying X, Y, Z, R, G, B, and SNR
    # for central 10 x 10 pixels
    pixels_to_display = 10
    for i in range(int((height - pixels_to_display) / 2), int((height + pixels_to_display) / 2)):
        for j in range(int((width - pixels_to_display) / 2), int((width + pixels_to_display) / 2)):
            print(
                f"Values at pixel ({i} , {j}): X:{xyz[i,j,0]:.1f} Y:{xyz[i,j,1]:.1f}"
                f"Z:{xyz[i,j,2]:.1f} R:{rgb[i,j,0]} G:{rgb[i,j,1]} B:{rgb[i,j,2]}"
                f"SNR:{snr[i,j,0]:.1f}"
            )


if __name__ == "__main__":
    _main()
