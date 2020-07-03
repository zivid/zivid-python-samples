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
    point_cloud = frame.point_cloud().to_array()
    xyz = np.dstack([point_cloud["x"], point_cloud["y"], point_cloud["z"]])
    rgb = np.dstack([point_cloud["r"], point_cloud["g"], point_cloud["b"]])
    contrast = np.dstack([point_cloud["contrast"]])

    height = frame.point_cloud().height
    width = frame.point_cloud().width

    print("Point cloud information:")
    print(f"Number of points: {point_cloud.size}")
    print(f"Height: {height}, Width: {width}")

    # Iterating over the point cloud and displaying X, Y, Z, R, G, B, and Contrast
    # for central 10 x 10 pixels
    pixels_to_display = 10
    for i in range(
        int((height - pixels_to_display) / 2), int((height + pixels_to_display) / 2)
    ):
        for j in range(
            int((width - pixels_to_display) / 2), int((width + pixels_to_display) / 2)
        ):
            print(
                f"Values at pixel ({i} , {j}): X:{xyz[i,j,0]:.1f} Y:{xyz[i,j,1]:.1f}"
                f"Z:{xyz[i,j,2]:.1f} R:{rgb[i,j,0]} G:{rgb[i,j,1]} B:{rgb[i,j,2]}"
                f"Contrast:{contrast[i,j,0]:.1f}"
            )


if __name__ == "__main__":
    _main()
