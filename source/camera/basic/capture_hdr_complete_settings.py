"""
Capture point clouds, with color, from the Zivid camera with fully configured settings.

For scenes with high dynamic range we combine multiple acquisitions to get an HDR point cloud.
This example shows how to fully configure settings for each acquisition.
In general, capturing an HDR point cloud is a lot simpler than this.
The purpose of this example is to demonstrate how to configure all the settings.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

from datetime import timedelta
from typing import Iterable, Tuple

import zivid


def _set_sampling_pixel(settings: zivid.Settings, camera: zivid.Camera) -> None:
    """Get sampling pixel setting based on the camera model.

    Args:
        settings: Zivid settings instance
        camera: Zivid camera instance

    Raises:
        ValueError: If the camera model is not supported

    """
    if (
        camera.info.model is zivid.CameraInfo.Model.zividTwo
        or camera.info.model is zivid.CameraInfo.Model.zividTwoL100
        or camera.info.model is zivid.CameraInfo.Model.zivid2PlusM130
        or camera.info.model is zivid.CameraInfo.Model.zivid2PlusM60
        or camera.info.model is zivid.CameraInfo.Model.zivid2PlusL110
    ):
        settings.sampling.pixel = zivid.Settings.Sampling.Pixel.blueSubsample2x2
    elif (
        camera.info.model is zivid.CameraInfo.Model.zivid2PlusMR130
        or camera.info.model is zivid.CameraInfo.Model.zivid2PlusMR60
        or camera.info.model is zivid.CameraInfo.Model.zivid2PlusLR110
    ):
        settings.sampling.pixel = zivid.Settings.Sampling.Pixel.by2x2
    else:
        raise ValueError(f"Unhandled enum value {camera.info.model}")


def _get_exposure_values(camera: zivid.Camera) -> Iterable[Tuple[float, float, timedelta, float]]:
    """Get exposure values based on the camera model.

    Args:
        camera: Zivid camera instance

    Returns:
        apertures: The f-number of each capture
        gains: The gain of each capture
        exposure_times: The exposure time of each capture
        brightnesses: The projector brightness of each capture

    Raises:
        ValueError: If the camera model is not supported

    """
    if camera.info.model is zivid.CameraInfo.Model.zividTwo or camera.info.model is zivid.CameraInfo.Model.zividTwoL100:
        apertures = (5.66, 2.38, 1.8)
        gains = (1.0, 1.0, 1.0)
        exposure_times = (timedelta(microseconds=1677), timedelta(microseconds=5000), timedelta(microseconds=100000))
        brightnesses = (1.8, 1.8, 1.8)
    elif (
        camera.info.model is zivid.CameraInfo.Model.zivid2PlusM130
        or camera.info.model is zivid.CameraInfo.Model.zivid2PlusM60
        or camera.info.model is zivid.CameraInfo.Model.zivid2PlusL110
    ):
        apertures = (5.66, 2.8, 2.37)
        gains = (1.0, 1.0, 1.0)
        exposure_times = (timedelta(microseconds=1677), timedelta(microseconds=5000), timedelta(microseconds=100000))
        brightnesses = (2.2, 2.2, 2.2)
    elif (
        camera.info.model is zivid.CameraInfo.Model.zivid2PlusMR130
        or camera.info.model is zivid.CameraInfo.Model.zivid2PlusMR60
        or camera.info.model is zivid.CameraInfo.Model.zivid2PlusLR110
    ):
        apertures = (5.66, 2.8, 2.37)
        gains = (1.0, 1.0, 1.0)
        exposure_times = (timedelta(microseconds=900), timedelta(microseconds=1500), timedelta(microseconds=20000))
        brightnesses = (2.5, 2.5, 2.5)
    else:
        raise ValueError(f"Unhandled enum value {camera.info.model}")

    return zip(apertures, gains, exposure_times, brightnesses)  # noqa: B905


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings for capture:")
    settings_2d = zivid.Settings2D()

    settings_2d.sampling.color = zivid.Settings2D.Sampling.Color.rgb
    settings_2d.sampling.pixel = zivid.Settings2D.Sampling.Pixel.all

    settings_2d.processing.color.balance.red = 1.0
    settings_2d.processing.color.balance.blue = 1.0
    settings_2d.processing.color.balance.green = 1.0
    settings_2d.processing.color.gamma = 1.0

    settings_2d.processing.color.experimental.mode = zivid.Settings2D.Processing.Color.Experimental.Mode.automatic

    settings = zivid.Settings()
    settings.engine = zivid.Settings.Engine.phase

    settings.region_of_interest.box.enabled = True
    settings.region_of_interest.box.point_o = [1000, 1000, 1000]
    settings.region_of_interest.box.point_a = [1000, -1000, 1000]
    settings.region_of_interest.box.point_b = [-1000, 1000, 1000]
    settings.region_of_interest.box.extents = [-1000, 1000]

    settings.region_of_interest.depth.enabled = True
    settings.region_of_interest.depth.range = [200, 2000]

    settings.processing.filters.cluster.removal.enabled = True
    settings.processing.filters.cluster.removal.max_neighbor_distance = 10
    settings.processing.filters.cluster.removal.min_area = 100

    settings.processing.filters.hole.repair.enabled = True
    settings.processing.filters.hole.repair.hole_size = 0.2
    settings.processing.filters.hole.repair.strictness = 1

    settings.processing.filters.noise.removal.enabled = True
    settings.processing.filters.noise.removal.threshold = 7.0

    settings.processing.filters.noise.suppression.enabled = True
    settings.processing.filters.noise.repair.enabled = True

    settings.processing.filters.outlier.removal.enabled = True
    settings.processing.filters.outlier.removal.threshold = 5.0

    settings.processing.filters.reflection.removal.enabled = True
    settings.processing.filters.reflection.removal.mode = (
        zivid.Settings.Processing.Filters.Reflection.Removal.Mode.global_
    )

    settings.processing.filters.smoothing.gaussian.enabled = True
    settings.processing.filters.smoothing.gaussian.sigma = 1.5

    settings.processing.filters.experimental.contrast_distortion.correction.enabled = True
    settings.processing.filters.experimental.contrast_distortion.correction.strength = 0.4

    settings.processing.filters.experimental.contrast_distortion.removal.enabled = False
    settings.processing.filters.experimental.contrast_distortion.removal.threshold = 0.5

    settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2

    settings.diagnostics.enabled = False

    settings.color = settings_2d

    _set_sampling_pixel(settings, camera)
    print(settings)

    print("Configuring acquisition settings different for all HDR acquisitions")
    exposure_values = _get_exposure_values(camera)
    for aperture, gain, exposure_time, brightness in exposure_values:
        settings.acquisitions.append(
            zivid.Settings.Acquisition(
                aperture=aperture,
                exposure_time=exposure_time,
                brightness=brightness,
                gain=gain,
            )
        )

    settings_2d.acquisitions.append(
        zivid.Settings2D.Acquisition(
            aperture=2.83,
            exposure_time=timedelta(microseconds=10000),
            brightness=1.8,
            gain=1.0,
        )
    )

    for acquisition in settings.acquisitions:
        print(acquisition)
    print("Capturing frame (HDR)")
    frame = camera.capture_2d_3d(settings)
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
