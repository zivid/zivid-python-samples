"""
Capture point clouds, with color, with the Zivid file camera.
This sample can be used without access to a physical camera.

The file camera files are found in Zivid Sample Data with ZFC file extension.
See the instructions in README.md to download the Zivid Sample Data.
There are five available file cameras to choose from, one for each camera model.
The default file camera used in this sample is the Zivid 2 M70 file camera.

"""

import argparse
from pathlib import Path

import zivid
from sample_utils.display import display_pointcloud
from sample_utils.paths import get_sample_data_path


def _options() -> argparse.Namespace:
    """Function to read user arguments


    Returns:
        Argument from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--file-camera",
        required=False,
        type=Path,
        default=get_sample_data_path() / "FileCameraZivid2M70.zfc",
        help="Path to the file camera .zfc file",
    )

    return parser.parse_args()


def _main() -> None:
    user_input = _options()

    app = zivid.Application()

    file_camera = user_input.file_camera

    print(f"Creating virtual camera using file: {file_camera}")
    camera = app.create_file_camera(file_camera)

    print("Configuring settings")
    settings = zivid.Settings()
    settings.acquisitions.append(zivid.Settings.Acquisition())
    settings.processing.filters.smoothing.gaussian.enabled = True
    settings.processing.filters.smoothing.gaussian.sigma = 1
    settings.processing.filters.reflection.removal.enabled = True
    settings.processing.filters.reflection.removal.experimental.mode = "global"
    settings.processing.color.balance.red = 1.0
    settings.processing.color.balance.green = 1.0
    settings.processing.color.balance.blue = 1.0

    print("Capturing frame")
    with camera.capture(settings) as frame:
        point_cloud = frame.point_cloud()
        xyz = point_cloud.copy_data("xyz")
        rgba = point_cloud.copy_data("rgba")

        print("Visualizing point cloud")
        display_pointcloud(xyz, rgba[:, :, 0:3])


if __name__ == "__main__":
    _main()
