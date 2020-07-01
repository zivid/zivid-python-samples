"""File camera capture sample."""
from pathlib import Path

import zivid

from utils.paths import get_sample_data_path


def _main():
    app = zivid.Application()
    camera = app.create_file_camera(
        Path() / get_sample_data_path() / "FileCameraZividOne.zfc"
    )

    with camera.capture() as frame:
        frame.save("Result.zdf")


if __name__ == "__main__":
    _main()
