"""
This example shows how to capture point clouds, with color, from the Zivid camera.

For scenes with high dynamic range we combine multiple acquisitions to get an HDR point cloud. This example shows how
to fully configure settings for each acquisition. In general, capturing an HDR point cloud is a lot simpler than this.
The purpose of this example is to demonstrate how to configure all the settings.
"""

import datetime
import zivid


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring acquisition settings different for all HDR acquisitions")
    settings = zivid.Settings(
        acquisitions=[
            zivid.Settings.Acquisition(
                aperture=8.0,
                exposure_time=datetime.timedelta(microseconds=10000),
                brightness=1.8,
                gain=1.0,
            ),
            zivid.Settings.Acquisition(
                aperture=4.0,
                exposure_time=datetime.timedelta(microseconds=10000),
                brightness=1.8,
                gain=1.0,
            ),
            zivid.Settings.Acquisition(
                aperture=4.0,
                exposure_time=datetime.timedelta(microseconds=40000),
                brightness=1.8,
                gain=2.0,
            ),
        ],
    )
    for acquisition in settings.acquisitions:
        print(acquisition)

    print("Configuring global processing settings")
    filters = settings.processing.filters
    filters.smoothing.gaussian.enabled = True
    filters.smoothing.gaussian.sigma = 1.5
    filters.noise.removal.enabled = True
    filters.noise.removal.threshold = 7.0
    filters.outlier.removal.enabled = True
    filters.outlier.removal.threshold = 5.0
    filters.reflection.removal.enabled = True
    filters.experimental.contrast_distortion.correction.enabled = True
    filters.experimental.contrast_distortion.correction.strength = 0.4
    filters.experimental.contrast_distortion.removal.enabled = False
    filters.experimental.contrast_distortion.removal.threshold = 0.5
    color = settings.processing.color
    color.balance.red = 1.0
    color.balance.blue = 1.0
    color.balance.green = 1.0
    color.gamma = 1.0
    print(settings.processing)

    print("Capturing frame (HDR)")
    with camera.capture(settings) as frame:
        print("Complete settings used:")
        print(frame.settings)
        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)


if __name__ == "__main__":
    _main()
