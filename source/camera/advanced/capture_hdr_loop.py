"""
This example shows how to cover the same dynamic range in a scene with different acquisition settings.

This possibility allows to optimize settings for quality, speed, or to find a compromise. The camera captures multi
acquisition HDR point clouds in a loop, with settings from YML files. The YML files for this sample can be found under
the main instructions for Zivid samples.
"""

from pathlib import Path
import zivid

from sample_utils.paths import get_sample_data_path
from sample_utils.settings_from_file import get_settings_from_yaml


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    for i in range(1, 4):
        settings_file = Path() / get_sample_data_path() / f"Settings/Zivid One/Settings0{i :01d}.yml"
        print(f"Configuring settings from file: {settings_file}")
        settings = get_settings_from_yaml(settings_file)

        print("Capturing frame (HDR)")
        with camera.capture(settings) as frame:
            data_file = f"Frame0{i}.zdf"
            print(f"Saving frame to file: {data_file}")
            frame.save(data_file)


if __name__ == "__main__":
    _main()
