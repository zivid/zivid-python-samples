"""
Capture 2D and 3D separately with the Zivid camera.

Capture separate 2D image with subsampling2x2. Then capture 3D with subsampling4x4
and upsampling2x2 to match resolution of 2D.
Then use color from 2D when visualizing the 3D point cloud.

"""

from typing import Tuple

import zivid
from zividsamples.display import display_pointcloud


def _get_2d_and_3d_settings(camera: zivid.Camera) -> Tuple[zivid.Settings2D, zivid.Settings]:
    """Get 2D and 3D settings with sampling mode based on camera model.

    Args:
        camera: Zivid camera

    Raises:
        ValueError: If camera model is not supported

    Returns:
        3D settings with sampling mode based on camera model

    """
    settings_2d = zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()])
    settings = zivid.Settings(acquisitions=[zivid.Settings.Acquisition()])

    model = camera.info.model
    if model in [zivid.CameraInfo.Model.zividTwo, zivid.CameraInfo.Model.zividTwoL100]:
        settings_2d.sampling.pixel = zivid.Settings2D.Sampling.Pixel.all
        settings.sampling.pixel = zivid.Settings.Sampling.Pixel.blueSubsample2x2
        settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2
    elif model in [
        zivid.CameraInfo.Model.zivid2PlusM130,
        zivid.CameraInfo.Model.zivid2PlusM60,
        zivid.CameraInfo.Model.zivid2PlusL110,
    ]:
        settings_2d.sampling.pixel = zivid.Settings2D.Sampling.Pixel.blueSubsample2x2
        settings.sampling.pixel = zivid.Settings.Sampling.Pixel.blueSubsample4x4
        settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2
    elif model in [
        zivid.CameraInfo.Model.zivid2PlusMR130,
        zivid.CameraInfo.Model.zivid2PlusMR60,
        zivid.CameraInfo.Model.zivid2PlusLR110,
    ]:
        settings_2d.sampling.pixel = zivid.Settings2D.Sampling.Pixel.by2x2
        settings.sampling.pixel = zivid.Settings.Sampling.Pixel.by4x4
        settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2
    else:
        raise ValueError(f"Unsupported camera model '{model}'")

    return settings_2d, settings


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring 2D and 3D settings")
    settings_2d, settings = _get_2d_and_3d_settings(camera)

    print("Capturing 2D frame")
    with camera.capture(settings_2d) as frame_2d:
        print("Getting RGBA image")
        image = frame_2d.image_rgba()
        rgba = image.copy_data()

        print("Capturing frame")
        with camera.capture(settings) as frame:
            point_cloud = frame.point_cloud()
            xyz = point_cloud.copy_data("xyz")

            print("Visualizing point cloud")
            display_pointcloud(xyz, rgba)


if __name__ == "__main__":
    _main()
