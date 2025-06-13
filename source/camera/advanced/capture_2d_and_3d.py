"""
Capture 2D and 3D with the Zivid camera.

Capture separate 2D and 3D with different sampling modes based on camera model.
Then use color from 2D when visualizing the 3D point cloud.

"""

import zivid
from zividsamples.display import display_pointcloud


def _get_2d_and_3d_settings(camera: zivid.Camera) -> zivid.Settings:
    """Get 2D and 3D settings with sampling mode based on camera model.

    Args:
        camera: Zivid camera

    Raises:
        ValueError: If camera model is not supported

    Returns:
        Settings with sampling mode based on camera model

    """
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    model = camera.info.model
    if model in [zivid.CameraInfo.Model.zividTwo, zivid.CameraInfo.Model.zividTwoL100]:
        settings.sampling.pixel = zivid.Settings.Sampling.Pixel.blueSubsample2x2
        settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2
        settings.color.sampling.pixel = zivid.Settings2D.Sampling.Pixel.all
    elif model in [
        zivid.CameraInfo.Model.zivid2PlusM130,
        zivid.CameraInfo.Model.zivid2PlusM60,
        zivid.CameraInfo.Model.zivid2PlusL110,
    ]:
        settings.sampling.pixel = zivid.Settings.Sampling.Pixel.blueSubsample4x4
        settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2
        settings.color.sampling.pixel = zivid.Settings2D.Sampling.Pixel.blueSubsample2x2
    elif model in [
        zivid.CameraInfo.Model.zivid2PlusMR130,
        zivid.CameraInfo.Model.zivid2PlusMR60,
        zivid.CameraInfo.Model.zivid2PlusLR110,
    ]:
        settings.sampling.pixel = zivid.Settings.Sampling.Pixel.by4x4
        settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2
        settings.color.sampling.pixel = zivid.Settings2D.Sampling.Pixel.by2x2
    else:
        raise ValueError(f"Unsupported camera model '{model}'")

    return settings


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring 2D and 3D settings")
    settings = _get_2d_and_3d_settings(camera)

    print("Capturing 2D+3D")
    frame = camera.capture_2d_3d(settings)
    print("Getting RGBA image")
    image = frame.frame_2d().image_rgba_srgb()
    rgba = image.copy_data()

    print("Getting point cloud")
    point_cloud = frame.point_cloud()
    xyz = point_cloud.copy_data("xyz")

    print("Visualizing point cloud")
    display_pointcloud(xyz, rgba[:, :, :3])


if __name__ == "__main__":
    _main()
