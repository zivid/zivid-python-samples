"""
Capture a ZDF point cloud and save it to PLY file format.
"""

import datetime
import zivid


def _main():
    app = zivid.Application()

    filename_ply = "Zivid3D.ply"

    print("Connecting to the camera")
    camera = app.connect_camera()

    print("Configuring the camera settings")
    with camera.update_settings() as updater:
        updater.settings.exposure_time = datetime.timedelta(microseconds=10000)
        updater.settings.iris = 21
        updater.settings.filters.reflection.enabled = True

    print("Capturing a frame")
    with camera.capture() as frame:
        print(f"Saving the frame to {filename_ply}")
        frame.save(filename_ply)


if __name__ == "__main__":
    _main()
