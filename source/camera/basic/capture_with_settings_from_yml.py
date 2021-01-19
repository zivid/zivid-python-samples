"""
This example shows how to capture point clouds, with color, from the Zivid camera, with settings from YML file.

The YML files for this sample can be found under the main instructions for Zivid samples.
"""

from pathlib import Path
import zivid

from sample_utils.paths import get_sample_data_path
from sample_utils.settings_from_file import get_settings_from_yaml


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    settings_file = Path() / get_sample_data_path() / "Settings/Zivid One/Settings01.yml"
    print(f"Configuring settings from file: {settings_file}")
    settings = get_settings_from_yaml(settings_file)

    print("Capturing frame")
    with camera.capture(settings) as frame:
        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)


if __name__ == "__main__":
    _main()
