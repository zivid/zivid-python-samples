"""
This example shows how to capture point clouds, with color, from the Zivid file camera.

This example can be used without access to a physical camera. The ZFC files for this sample can be found under the main
instructions for Zivid samples.
"""

from pathlib import Path
import zivid

from sample_utils.paths import get_sample_data_path


def _main():
    app = zivid.Application()

    # The file_camera file is in Zivid Sample Data. See instructions in README.md
    file_camera = Path() / get_sample_data_path() / "FileCameraZividOne.zfc"

    print(f"Creating virtual camera using file: {file_camera}")
    camera = app.create_file_camera(file_camera)

    print("Configuring settings")
    settings = zivid.Settings()
    settings.acquisitions.append(zivid.Settings.Acquisition())
    settings.processing.filters.smoothing.gaussian.enabled = True
    settings.processing.filters.smoothing.gaussian.sigma = 1.5
    settings.processing.filters.reflection.removal.enabled = True
    settings.processing.color.balance.red = 1.0
    settings.processing.color.balance.green = 1.0
    settings.processing.color.balance.blue = 1.0

    print("Capturing frame")
    with camera.capture(settings) as frame:
        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)


if __name__ == "__main__":
    _main()
