"""
Capture 2D and 3D separately with the Zivid camera.

Capture separate 2D image and use this to color the 3D point cloud.
If resolution is different, then apply manual subsampling of the
2D image to match the resolution of the 3D point cloud.

"""

import argparse

import numpy as np
import zivid
from sample_utils.display import display_pointcloud, display_rgbs


def _options() -> argparse.Namespace:
    """Function to read user arguments

    Returns:
        Argument from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--pixels-to-sample",
        "-p",
        required=False,
        type=str,
        choices=zivid.Settings.Sampling.Pixel.valid_values(),
        default=zivid.Settings.Sampling.Pixel.blueSubsample2x2,
        help="Select which pixels to sample",
    )

    return parser.parse_args()


def _map_rgb(pixels_to_sample: zivid.Settings.Sampling.Pixel, rgba: np.ndarray) -> np.ndarray:
    """Function to map the full RGB image to a subsampled one.

    Args:
        pixels_to_sample: zivid.Settings.Sampling.Pixel option to use for subsampling
        rgba: RGBA image (HxWx4)

    Raises:
        RuntimeError: If chosen zivid.Settings.Sampling.Pixel is unsupported

    Returns:
        Subsampled RGB image

    """
    if pixels_to_sample == zivid.Settings.Sampling.Pixel.blueSubsample2x2:
        return rgba[::2, ::2, 0:3]
    if pixels_to_sample == zivid.Settings.Sampling.Pixel.redSubsample2x2:
        return rgba[1::2, 1::2, 0:3]
    if pixels_to_sample == zivid.Settings.Sampling.Pixel.all:
        return rgba[:, :, 0:3]
    raise RuntimeError(f"Invalid pixels to sample: {pixels_to_sample}")


def _main() -> None:
    app = zivid.Application()

    user_input = _options()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring 2D settings")
    settings_2d = zivid.Settings2D()
    settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())

    print("Configuring 3D settings")
    settings = zivid.Settings()
    settings.experimental.engine = "phase"
    settings.acquisitions.append(zivid.Settings.Acquisition())
    settings.sampling.pixel = user_input.pixels_to_sample
    settings.sampling.color = zivid.Settings.Sampling.Color.disabled

    model = camera.info.model
    if settings.sampling.pixel == zivid.Settings.Sampling.Pixel.all and model in (
        zivid.CameraInfo.Model.zivid2PlusM130,
        zivid.CameraInfo.Model.zivid2PlusM60,
        zivid.CameraInfo.Model.zivid2PlusL110,
    ):
        # For 2+, we must lower Brightness from the default 2.5 to 2.2, when using `all` mode.
        # This code can be removed by changing the Config.yml option 'Camera/Power/Limit'.
        for acquisition in settings.acquisitions:
            acquisition.brightness = 2.2

    print("Capturing 2D frame")
    with camera.capture(settings_2d) as frame_2d:
        print("Getting RGBA image")
        image = frame_2d.image_rgba()
        rgba = image.copy_data()

        rgb_mapped = _map_rgb(user_input.pixels_to_sample, rgba)
        display_rgbs(
            rgbs=[rgba[:, :, :3], rgb_mapped],
            titles=["Full resolution RGB from 2D capture", f"{user_input.pixels_to_sample} RGB from 2D capture"],
            layout=(1, 2),
            block=True,
        )

        print("Capturing frame")
        with camera.capture(settings) as frame:
            point_cloud = frame.point_cloud()
            xyz = point_cloud.copy_data("xyz")

            print("Visualizing point cloud")
            display_pointcloud(xyz, rgb_mapped)


if __name__ == "__main__":
    _main()
