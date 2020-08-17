"""
Capture an HDR frame with fully configured settings for each frame.

In general, taking an HDR image is a lot simpler than this as the default
settings work for most scenes. The purpose of this example is to demonstrate
how to configure all the settings.
"""

import datetime
import zivid


def _main():
    app = zivid.Application()

    print("Connecting to the camera")
    camera = app.connect_camera()

    print("Configuring the camera settings")
    iris_setting = [17, 27, 27]
    exposure_setting = [10000, 10000, 40000]
    gain_setting = [1.0, 1.0, 2.0]
    settings_collection = [camera.settings for _ in range(3)]
    for i in range(len(settings_collection)):
        settings_collection[i].iris = iris_setting[i]
        settings_collection[i].exposure_time = datetime.timedelta(
            microseconds=exposure_setting[i]
        )
        settings_collection[i].brightness = 1
        settings_collection[i].gain = gain_setting[i]
        settings_collection[i].bidirectional = 0
        settings_collection[i].filters.contrast.enabled = True
        settings_collection[i].filters.Contrast.threshold = 0.5
        settings_collection[i].filters.gaussian.enabled = True
        settings_collection[i].filters.gaussian.sigma = 1.5
        settings_collection[i].filters.outlier.enabled = True
        settings_collection[i].filters.outlier.threshold = 5
        settings_collection[i].filters.reflection.enabled = True
        settings_collection[i].filters.saturated.enabled = True
        settings_collection[i].blue_balance = 1
        settings_collection[i].red_balance = 1

    print("Capturing an HDR frame")
    with camera.capture(settings_collection) as hdr_frame:
        print("Saving the HDR frame")
        hdr_frame.save("HDR.zdf")


if __name__ == "__main__":
    _main()
