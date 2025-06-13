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
        default=get_sample_data_path() / "FileCameraZivid2PlusMR60.zfc",
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
    settings.processing.filters.reflection.removal.mode = "global"

    settings_2d = zivid.Settings2D()
    settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
    settings_2d.processing.color.balance.blue = 1.0
    settings_2d.processing.color.balance.green = 1.0
    settings_2d.processing.color.balance.red = 1.0

    settings.color = settings_2d

    print("Capturing frame")
    frame = camera.capture_2d_3d(settings)
    data_file = "Frame.zdf"
    print(f"Saving frame to file: {data_file}")
    frame.save(data_file)


if __name__ == "__main__":
    _main()
