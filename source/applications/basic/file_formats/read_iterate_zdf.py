"""
Read point cloud data from a ZDF file, iterate through it, and extract individual points.

The ZDF file for this sample can be found under the main instructions for Zivid samples.

"""

import zivid
from zividsamples.paths import get_sample_data_path


def _main() -> None:
    with zivid.Application():
        data_file = get_sample_data_path() / "Zivid3D.zdf"
        print(f"Reading point cloud from file: {data_file}")

        frame = zivid.Frame(data_file)

        print("Getting point cloud from frame")
        point_cloud = frame.point_cloud()
        xyz = point_cloud.copy_data("xyz")
        rgba = point_cloud.copy_data("rgba_srgb")
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
        for row in range(int((height - pixels_to_display) / 2), int((height + pixels_to_display) / 2)):
            for col in range(int((width - pixels_to_display) / 2), int((width + pixels_to_display) / 2)):
                print(
                    f"Values at pixel ({row} , {col}): X:{xyz[row,col,0]:.1f} Y:{xyz[row,col,1]:.1f}"
                    f" Z:{xyz[row,col,2]:.1f} R:{rgba[row,col,0]} G:{rgba[row,col,1]} B:{rgba[row,col,2]}"
                    f" SNR:{snr[row,col]:.1f}"
                )


if __name__ == "__main__":
    _main()
