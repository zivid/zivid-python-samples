"""
Capture point clouds, with color, with the Zivid file camera.
This sample can be used without access to a physical camera.

The file camera is created from a ZDF with diagnostics.
ZDF files with diagnostics are found in Zivid Sample Data.
See the instructions in README.md to download the Zivid Sample Data.
There are nine available file cameras to choose from, one for each camera model.
The default ZDF used in this sample is from Zivid 2 M70.

For more information about file cameras, check out this tutorial:
https://support.zivid.com/en/latest/camera/academy/camera/file-camera.html

"""

import argparse
from pathlib import Path

import zivid
from zividsamples.display import display_pointcloud
from zividsamples.paths import get_sample_data_path


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
        default=get_sample_data_path() / "FileCameraZivid2M70.zdf",
        help="Path to a ZDF with diagnostics enabled",
    )

    return parser.parse_args()


def _main() -> None:
    user_input = _options()

    app = zivid.Application()

    file_camera = user_input.file_camera
    loaded_frame_with_diagnostics = zivid.Frame(file_camera)

    print(f"Creating virtual camera using file: {file_camera}")
    camera = app.create_file_camera(loaded_frame_with_diagnostics)

    print("Capturing frame")
    settings = loaded_frame_with_diagnostics.settings
    settings.processing.filters.smoothing.gaussian.enabled = True
    settings.processing.filters.smoothing.gaussian.sigma = 1.5
    settings.processing.filters.reflection.removal.enabled = True
    settings.processing.filters.reflection.removal.mode = (
        zivid.Settings.Processing.Filters.Reflection.Removal.Mode.global_
    )
    settings.region_of_interest.box = zivid.Settings.RegionOfInterest.Box(
        enabled=True,
        point_o=(-331, 201, 661),
        point_a=(299, 203, 667),
        point_b=(-331, -203, 844),
        extents=(0, 178),
    )
    frame = camera.capture_2d_3d(settings)

    print("Visualizing point cloud")
    display_pointcloud(frame)


if __name__ == "__main__":
    _main()
