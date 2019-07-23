"""
This example shows how to acquire an HDR image from the Zivid camera with fully
configured settings for each frame. In general, taking an HDR image is a lot
simpler than this as the default settings work for most scenes. The purpose of
this example is to demonstrate how to configure all the settings.
"""

import zivid
import datetime


def _main():
    app = zivid.Application()

    print("Connecting to the camera")
    camera = app.connect_camera()

    print("Configuring the camera settings")
    settings_collection = [camera.settings for _ in range(3)]

    settings_collection[0].iris = 10
    settings_collection[0].exposure_time = datetime.timedelta(microseconds=10000)
    settings_collection[0].brightness = 1
    settings_collection[0].gain = 1
    settings_collection[0].bidirectional = 0
    settings_collection[0].filters.contrast.enabled = True
    settings_collection[0].filters.Contrast.threshold = 5
    settings_collection[0].filters.gaussian.enabled = True
    settings_collection[0].filters.gaussian.sigma = 1.5
    settings_collection[0].filters.outlier.enabled = True
    settings_collection[0].filters.outlier.threshold = 5
    settings_collection[0].filters.reflection.enabled = True
    settings_collection[0].filters.saturated.enabled = True
    settings_collection[0].blue_balance = 1.081
    settings_collection[0].red_balance = 1.709

    settings_collection[1].iris = 20
    settings_collection[1].exposure_time = datetime.timedelta(microseconds=20000)
    settings_collection[1].brightness = 0.5
    settings_collection[1].gain = 2
    settings_collection[1].bidirectional = 0
    settings_collection[1].filters.contrast.enabled = True
    settings_collection[1].filters.contrast.threshold = 5
    settings_collection[1].filters.gaussian.enabled = True
    settings_collection[1].filters.gaussian.sigma = 1.5
    settings_collection[1].filters.outlier.enabled = True
    settings_collection[1].filters.outlier.threshold = 5
    settings_collection[1].filters.reflection.enabled = True
    settings_collection[1].filters.saturated.enabled = True
    settings_collection[1].blue_balance = 1.081
    settings_collection[1].red_balance = 1.709

    settings_collection[2].iris = 30
    settings_collection[2].exposure_time = datetime.timedelta(microseconds=33000)
    settings_collection[2].brightness = 1
    settings_collection[2].gain = 1
    settings_collection[2].bidirectional = 1
    settings_collection[2].filters.contrast.enabled = True
    settings_collection[2].filters.contrast.threshold = 5
    settings_collection[2].filters.gaussian.enabled = True
    settings_collection[2].filters.gaussian.sigma = 1.5
    settings_collection[2].filters.outlier.enabled = True
    settings_collection[2].filters.outlier.threshold = 5
    settings_collection[2].filters.reflection.enabled = True
    settings_collection[2].filters.saturated.enabled = True
    settings_collection[2].blue_balance = 1.081
    settings_collection[2].red_balance = 1.709

    print("Capturing an HDR frame")
    with camera.capture(settings_collection) as hdr_frame:
        print("Saving the HDR frame")
        hdr_frame.save("HDR.zdf")


if __name__ == "__main__":
    _main()
