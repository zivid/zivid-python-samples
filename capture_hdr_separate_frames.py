"""
Capture several individual frames and merge them into one HDR frame.

This is not the recommended way to capture an HDR frame. The goal is to
demonstrate the possibility to have access to both individual frames and the
resulting HDR frame.
"""

import zivid
import datetime


def capture(camera, settings):
    camera.settings = settings
    return camera.capture()


def _main():
    app = zivid.Application()

    print("Connecting to the camera")
    camera = app.connect_camera()

    print("Configuring the camera settings")
    settings_collection = [camera.settings for _ in range(3)]
    settings_collection[0].exposure_time = datetime.timedelta(microseconds=10000)
    settings_collection[0].iris = 17
    settings_collection[1].exposure_time = datetime.timedelta(microseconds=20000)
    settings_collection[1].iris = 27
    settings_collection[2].exposure_time = datetime.timedelta(microseconds=30000)
    settings_collection[2].iris = 35

    print("Capturing separate frames")
    frame1 = capture(camera, settings_collection[0])
    print(camera.settings.iris)
    print(camera.settings.exposure_time)
    frame2 = capture(camera, settings_collection[1])
    print(camera.settings.iris)
    print(camera.settings.exposure_time)
    frame3 = capture(camera, settings_collection[2])
    print(camera.settings.iris)
    print(camera.settings.exposure_time)

    print("Combining separate frames into a HDR frame")
    hdr = zivid.hdr.combine_frames([frame1, frame2, frame3])

    print("Saving the frames")
    frame1.save("frame1.zdf")
    frame2.save("frame2.zdf")
    frame3.save("frame3.zdf")

    print("Saving the HDR frame")
    hdr.save("HDR.zdf")


if __name__ == "__main__":
    _main()
