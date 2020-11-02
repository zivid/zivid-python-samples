"""
This example shows how to read point cloud data from a ZDF file, iterate through it, and extract individual points.

The ZDF file for this sample can be found under the main instructions for Zivid samples.
"""

from pathlib import Path
import zivid

from sample_utils.paths import get_sample_data_path


def _main():

    app = zivid.Application()

    data_file = Path() / get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading point cloud from file: {data_file}")
    frame = zivid.Frame(data_file)

    print("Getting point cloud from frame")
    point_cloud = frame.point_cloud()
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba")
    snr = frame.point_cloud().copy_data("snr")

    height = frame.point_cloud().height
    width = frame.point_cloud().width

    print("Point cloud information:")
    print(f"Number of points: {height * width}")
    print(f"Height: {height}, Width: {width}")

    pixels_to_display = 10
    print(
        "Iterating over point cloud and extracting X, Y, Z, R, G, B, and SNR "
        f"for central {pixels_to_display} x {pixels_to_display} pixels"
    )
    for i in range(int((height - pixels_to_display) / 2), int((height + pixels_to_display) / 2)):
        for j in range(int((width - pixels_to_display) / 2), int((width + pixels_to_display) / 2)):
            print(
                f"Values at pixel ({i} , {j}): X:{xyz[i,j,0]:.1f} Y:{xyz[i,j,1]:.1f}"
                f" Z:{xyz[i,j,2]:.1f} R:{rgba[i,j,0]} G:{rgba[i,j,1]} B:{rgba[i,j,2]}"
                f" SNR:{snr[i,j]:.1f}"
            )


if __name__ == "__main__":
    _main()
