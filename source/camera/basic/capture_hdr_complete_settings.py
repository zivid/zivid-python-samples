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

    print("Configuring acquisition settings different for all HDR acquisitions")
    settings = zivid.Settings(
        acquisitions=[
            zivid.Settings.Acquisition(
                aperture=8.0, exposure_time=datetime.timedelta(microseconds=10000), brightness=1.8, gain=1.0,
            ),
            zivid.Settings.Acquisition(
                aperture=4.0, exposure_time=datetime.timedelta(microseconds=10000), brightness=1.8, gain=1.0,
            ),
            zivid.Settings.Acquisition(
                aperture=4.0, exposure_time=datetime.timedelta(microseconds=40000), brightness=1.8, gain=2.0,
            ),
        ],
    )
    for acquisition in settings.acquisitions:
        print(acquisition)

    print("Configuring global processing settings")
    filters = settings.processing.filters
    filters.noise.removal.enabled = True
    filters.noise.removal.threshold = 10
    filters.smoothing.gaussian.enabled = True
    filters.smoothing.gaussian.sigma = 1.5
    filters.outlier.removal.enabled = True
    filters.outlier.removal.threshold = 5
    filters.reflection.removal.enabled = True
    filters.experimental.contrast_distortion.correction.enabled = True
    filters.experimental.contrast_distortion.correction.strength = 0.4
    filters.experimental.contrast_distortion.removal.enabled = False
    filters.experimental.contrast_distortion.removal.threshold = 0.5
    balance = settings.processing.color.balance
    balance.red = 1.0
    balance.blue = 1.0
    balance.green = 1.0
    print(settings.processing)

    print("Capturing an HDR frame")
    with camera.capture(settings) as hdr_frame:
        print("Saving the HDR frame")
        hdr_frame.save("HDR.zdf")


if __name__ == "__main__":
    _main()
