"""
Capture images and point clouds, with or without color, from the Zivid camera with settings from YML file.

The YML files for this sample can be found under the main Zivid sample instructions.

"""

import argparse
from pathlib import Path

import zivid
from zividsamples.paths import get_sample_data_path


def _settings_folder(camera: zivid.Camera) -> str:
    """Get folder name for settings files in Zivid Sample Data.

    Args:
        camera: Zivid camera

    Raises:
        RuntimeError: If camera is not supported

    Returns:
        Folder name

    """

    model = camera.info.model

    if model == zivid.CameraInfo.Model.zividTwo:
        return "zivid2"
    if model == zivid.CameraInfo.Model.zividTwoL100:
        return "zivid2"
    if model == zivid.CameraInfo.Model.zivid2PlusM130:
        return "zivid2Plus"
    if model == zivid.CameraInfo.Model.zivid2PlusM60:
        return "zivid2Plus"
    if model == zivid.CameraInfo.Model.zivid2PlusL110:
        return "zivid2Plus"
    if model == zivid.CameraInfo.Model.zivid2PlusMR130:
        return "zivid2Plus/R"
    if model == zivid.CameraInfo.Model.zivid2PlusMR60:
        return "zivid2Plus/R"
    if model == zivid.CameraInfo.Model.zivid2PlusLR110:
        return "zivid2Plus/R"
    raise RuntimeError(f"Unhandled enum value {camera.info.model}")


def _options(camera: zivid.Camera) -> argparse.Namespace:
    """Function to read user arguments.

    Args:
        camera: Zivid camera

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--settings-path",
        required=False,
        type=Path,
        default=get_sample_data_path() / "Settings" / _settings_folder(camera) / "Settings01.yml",
        help="Path to the camera settings YML file",
    )

    return parser.parse_args()


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    user_options = _options(camera)

    print("Loading settings from file")
    settings_file = Path(user_options.settings_path)
    settings = zivid.Settings.load(settings_file)

    print("Capturing 2D frame")
    with camera.capture_2d(settings) as frame_2d:
        image_srgb = frame_2d.image_srgb()
        image_file = "ImageSRGB.png"
        print(f"Saving 2D color image (sRGB color space) to file: {image_file}")
        image_srgb.save(image_file)

        # More information about linear RGB and sRGB color spaces is available at:
        # https://support.zivid.com/en/latest/reference-articles/color-spaces-and-output-formats.html#color-spaces

        pixel_row = 100
        pixel_col = 50

        srgb = image_srgb.copy_data()
        pixel = srgb[pixel_row, pixel_col]
        print(f"Color at pixel ({pixel_row},{pixel_col}): R:{pixel[0]} G:{pixel[1]} B:{pixel[2]} A:{pixel[3]}")

    print("Capturing 3D frame")
    with camera.capture_3d(settings) as frame_3d:
        data_file = "Frame3D.zdf"
        print(f"Saving frame to file: {data_file}")
        frame_3d.save(data_file)

        data_file_ply = "PointCloudWithoutColor.ply"
        print(f"Exporting point cloud (default pink colored points) to file: {data_file_ply}")
        frame_3d.save(data_file_ply)

    print("Capturing 2D3D frame")
    with camera.capture_2d_3d(settings) as frame:
        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)

        data_file_ply = "PointCloudWithColor.ply"
        print(f"Exporting point cloud (default pink colored points) to file: {data_file_ply}")
        frame.save(data_file_ply)


if __name__ == "__main__":
    _main()
