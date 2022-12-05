"""
Capture point clouds, with color, from the Zivid camera, with settings from YML file and diagnostics enabled.

Enabling diagnostics allows collecting additional data to be saved in the ZDF file.
Send ZDF files with diagnostics enabled to the Zivid support team to allow more thorough troubleshooting.
Have in mind that enabling diagnostics increases the capture time and the RAM usage.

The YML file for this sample can be found under the main instructions for Zivid samples.

"""


from pathlib import Path

import zivid
from sample_utils.paths import get_sample_data_path


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings from file")
    camera_model = camera.info.model
    settings_file = Path() / get_sample_data_path() / Path("Settings/" + camera_model[0:8] + "/Settings01.yml")
    settings = zivid.Settings.load(settings_file)

    print("Enabling diagnostics")
    settings.diagnostics.enabled = True

    print("Capturing frame")
    with camera.capture(settings) as frame:
        data_file = "FrameWithDiagnostics.zdf"
        print(f"Saving frame with diagnostic data to file: {data_file}")
        frame.save(data_file)


if __name__ == "__main__":
    _main()
