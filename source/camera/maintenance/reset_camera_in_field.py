"""
Reset in-field correction on a camera.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

import zivid
from zivid.experimental import calibration


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Reset in-field correction on the camera")
    calibration.reset_camera_correction(camera)


if __name__ == "__main__":
    _main()
