"""File camera capture sample."""
import datetime
from pathlib import Path
import zivid

from sample_utils.paths import get_sample_data_path


def _main():
    app = zivid.Application()
    camera = app.create_file_camera(Path() / get_sample_data_path() / "FileCameraZividOne.zfc")

    settings = zivid.Settings()
    settings.acquisitions.append(zivid.Settings.Acquisition())
    settings.acquisitions[0].aperture = 5.66
    settings.acquisitions[0].exposure_time = datetime.timedelta(microseconds=8333)

    with camera.capture(settings) as frame:
        frame.save("Result.zdf")


if __name__ == "__main__":
    _main()
