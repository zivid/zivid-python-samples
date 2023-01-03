"""
Capture point clouds, with color, from the Zivid camera, with settings from YML file.

The YML files for this sample can be found under the main Zivid sample instructions.

"""

import argparse
from pathlib import Path

import zivid
from sample_utils.paths import get_sample_data_path


def _options(camera_model) -> argparse.Namespace:
    """Function to read user arguments.

    Args:
        camera_model: Zivid camera model

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--settings-path",
        required=False,
        type=Path,
        default=get_sample_data_path() / "Settings" / camera_model[0:8] / "Settings01.yml",
        help="Path to the camera settings YML file",
    )

    return parser.parse_args()


def _main() -> None:

    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    user_options = _options(camera.info.model)

    print("Loading settings from file")
    settings_file = Path(user_options.settings_path)
    settings = zivid.Settings.load(settings_file)

    print("Capturing frame")
    with camera.capture(settings) as frame:
        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)


if __name__ == "__main__":
    _main()
