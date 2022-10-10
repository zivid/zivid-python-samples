"""
Capture point clouds, with color, from the Zivid camera with fully configured settings.

For scenes with high dynamic range we combine multiple acquisitions to get an HDR point cloud.
This example shows how to fully configure settings for each acquisition.
In general, capturing an HDR point cloud is a lot simpler than this.
The purpose of this example is to demonstrate how to configure all the settings.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

import datetime
from typing import Iterable, Tuple

import zivid


def _get_exposure_values(camera: zivid.Camera) -> Iterable[Tuple[float, float, float]]:
    """Print normal XYZ values of the 10 x 10 central pixels.

    Args:
        camera: Zivid camera instance

    Returns:
        apertures: The f-number of each capture
        gains: The gain from each capture
        exposure_times: The exposure time from each capture

    Raises:
        Exception: If the model is not Zivid One+ or Zivid Two

    """
    if (
        camera.info.model is zivid.CameraInfo.Model.zividOnePlusLarge
        or camera.info.model is zivid.CameraInfo.Model.zividOnePlusMedium
        or camera.info.model is zivid.CameraInfo.Model.zividOnePlusSmall
    ):
        apertures = (8.0, 4.0, 4.0)
        gains = (1.0, 1.0, 2.0)
        exposure_times = (10000, 10000, 40000)
    elif camera.info.model is zivid.CameraInfo.Model.zividTwo:
        apertures = (5.66, 2.38, 1.8)
        gains = (1.0, 1.0, 1.0)
        exposure_times = (1677, 5000, 100000)
    else:
        raise Exception("Unknown camera model")

    return zip(apertures, gains, exposure_times)


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring processing settings for capture:")
    settings = zivid.Settings()
    settings.experimental.engine = "phase"
    filters = settings.processing.filters
    filters.smoothing.gaussian.enabled = True
    filters.smoothing.gaussian.sigma = 1.5
    filters.noise.removal.enabled = True
    filters.noise.removal.threshold = 7.0
    filters.outlier.removal.enabled = True
    filters.outlier.removal.threshold = 5.0
    filters.reflection.removal.enabled = True
    filters.reflection.removal.experimental.mode = "global"
    filters.experimental.contrast_distortion.correction.enabled = True
    filters.experimental.contrast_distortion.correction.strength = 0.4
    filters.experimental.contrast_distortion.removal.enabled = False
    filters.experimental.contrast_distortion.removal.threshold = 0.5
    color = settings.processing.color
    color.balance.red = 1.0
    color.balance.blue = 1.0
    color.balance.green = 1.0
    color.gamma = 1.0
    settings.processing.color.experimental.mode = "automatic"
    print(settings.processing)

    print("Configuring acquisition settings different for all HDR acquisitions")
    exposure_values = _get_exposure_values(camera)
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
    print("Capturing frame (HDR)")
    with camera.capture(settings) as frame:
        print("Complete settings used:")
        print(frame.settings)
        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)

    settings_file = "Settings.yml"
    print(f"Saving settings to file: {settings_file}")
    settings.save(settings_file)

    print(f"Loading settings from file: {settings_file}")
    settings_from_file = zivid.Settings.load(settings_file)
    print(settings_from_file)


if __name__ == "__main__":
    _main()
