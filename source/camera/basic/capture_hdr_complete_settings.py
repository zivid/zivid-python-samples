"""
This example shows how to capture point clouds, with color, from the Zivid camera.

For scenes with high dynamic range we combine multiple acquisitions to get an HDR point cloud. This example shows how
to fully configure settings for each acquisition. In general, capturing an HDR point cloud is a lot simpler than this.
The purpose of this example is to demonstrate how to configure all the settings.
"""

import datetime
import zivid


def _get_exposure_values(camera):
    if (
        camera.info.model is zivid.CameraInfo.Model.zividOnePlusLarge
        or camera.info.model is zivid.CameraInfo.Model.zividOnePlusMedium
        or camera.info.model is zivid.CameraInfo.Model.zividOnePlusSmall
    ):
        aperture = (8.0, 4.0, 4.0)
        gain = (1.0, 1.0, 2.0)
        exposure_time = (10000, 10000, 20000)
    elif camera.info.model is zivid.CameraInfo.Model.zividTwo:
        aperture = (5.66, 2.38, 1.8)
        gain = (1.0, 1.0, 1.0)
        exposure_time = (1677, 5000, 100000)
    else:
        raise Exception("Unknown camera model")

    return zip(aperture, gain, exposure_time)


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring acquisition settings different for all HDR acquisitions")
    exposure_values = _get_exposure_values(camera)
    settings = zivid.Settings()
    for (aperture, gain, exposure_time) in exposure_values:
        settings.acquisitions.append(
            zivid.Settings.Acquisition(
                aperture=aperture,
                exposure_time=datetime.timedelta(microseconds=exposure_time),
                brightness=1.8,
                gain=gain,
            )
        )

    for acquisition in settings.acquisitions:
        print(acquisition)

    print("Configuring global processing settings")
    settings.experimental.engine = "phase"
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
    settings.processing.color.experimental.tone_mapping.enabled = "hdrOnly"
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
