"""
Cover the same dynamic range in a scene with different acquisition settings to optimize for quality, speed, or to find a compromise.

The camera captures multi-acquisition HDR point clouds in a loop, with settings from YML files.
The YML files for this sample can be found under the main Zivid sample instructions.

"""

from pathlib import Path

import zivid
from sample_utils.paths import get_sample_data_path


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    for i in range(1, 4):
        camera_model = camera.info.model
        settings_file = (
            Path() / get_sample_data_path() / Path("Settings/" + camera_model[0:8] + f"/Settings0{i :01d}.yml")
        )
        print(f"Loading settings from file: {settings_file}")
        settings = zivid.Settings.load(settings_file)

        print("Capturing frame (HDR)")
        with camera.capture(settings) as frame:
            data_file = f"Frame0{i}.zdf"
            print(f"Saving frame to file: {data_file}")
            frame.save(data_file)


if __name__ == "__main__":
    _main()
