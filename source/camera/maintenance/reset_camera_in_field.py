"""
Reset infield correction on a camera.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

For more information about in-field correction, check out this tutorial:
https://support.zivid.com/en/latest/camera/academy/camera/infield-correction.html

"""

import zivid


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Reset infield correction on the camera")
    zivid.calibration.reset_camera_correction(camera)


if __name__ == "__main__":
    _main()
