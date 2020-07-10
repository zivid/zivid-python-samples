"""File camera capture sample."""
import datetime
from pathlib import Path
import zivid

from utils.paths import get_sample_data_path


def _main():
    app = zivid.Application()
    camera = app.create_file_camera(
        Path() / get_sample_data_path() / "FileCameraZividOne.zfc"
    )

    settings = zivid.Settings(
        acquisitions=[
            zivid.Settings.Acquisition(
                aperture=5.66, exposure_time=datetime.timedelta(microseconds=8333),
            ),
        ],
    )

    with camera.capture(settings) as frame:
        frame.save("Result.zdf")


if __name__ == "__main__":
    _main()
