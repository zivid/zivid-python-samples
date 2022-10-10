"""
Capture point clouds, with color, from the Zivid camera, with settings from YML file.

The YML files for this sample can be found under the main Zivid sample instructions.

"""

from pathlib import Path

import zivid
from sample_utils.paths import get_sample_data_path


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Loading settings from file")
    camera_model = camera.info.model
    settings_file = Path() / get_sample_data_path() / Path("Settings/" + camera_model[0:8] + "/Settings01.yml")
    settings = zivid.Settings.load(settings_file)

    print("Capturing frame")
    with camera.capture(settings) as frame:
        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)


if __name__ == "__main__":
    _main()
