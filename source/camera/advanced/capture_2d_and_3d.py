"""
Capture 2D and 3D separately with the Zivid camera.

Capture separate 2D image with subsampling2x2. Then capture 3D with subsampling4x4
and upsampling2x2 to match resolution of 2D.
Then use color from 2D when visualizing the 3D point cloud.

"""

import zivid
from sample_utils.display import display_pointcloud


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring 2D settings")
    settings_2d = zivid.Settings2D()
    settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
    settings_2d.sampling.pixel = zivid.Settings2D.Sampling.Pixel.blueSubsample2x2

    print("Configuring 3D settings")
    settings = zivid.Settings()
    settings.engine = zivid.Settings.Engine.phase
    settings.acquisitions.append(zivid.Settings.Acquisition())
    settings.sampling.pixel = zivid.Settings.Sampling.Pixel.blueSubsample4x4
    settings.sampling.color = zivid.Settings.Sampling.Color.disabled
    settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2

    if camera.info.model in [zivid.CameraInfo.Model.zividTwo, zivid.CameraInfo.Model.zividTwoL100]:
        print(
            f"{camera.info.model_name} does not support 4x4 subsampling. This sample is written to show how combinations of Sampling::Pixel and Processing::Resampling::Mode."
        )
        settings.sampling.pixel = zivid.Settings.Sampling.Pixel.blueSubsample2x2
        settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.disabled

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
