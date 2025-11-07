"""
Capture images and point clouds, with and without color, from the Zivid camera with settings from YML file.

Choose whether to get the image in the linear RGB or the sRGB color space.

The YML files for this sample can be found under the main Zivid sample instructions.

"""

import argparse
from pathlib import Path

import zivid
from zividsamples.paths import get_sample_data_path


def _preset_path(camera: zivid.Camera) -> Path:
    """Get path to preset settings YML file, depending on camera model.

    Args:
        camera: Zivid camera

    Raises:
        ValueError: If unsupported camera model for this code sample

    Returns:
        Path: Zivid 2D and 3D settings YML path

    """
    presets_path = get_sample_data_path() / "Settings"

    if camera.info.model == zivid.CameraInfo.Model.zivid3XL250:
        return presets_path / "Zivid_Three_XL250_DepalletizationQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusMR60:
        return presets_path / "Zivid_Two_Plus_MR60_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusMR130:
        return presets_path / "Zivid_Two_Plus_MR130_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusLR110:
        return presets_path / "Zivid_Two_Plus_LR110_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusM60:
        return presets_path / "Zivid_Two_Plus_M60_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusM130:
        return presets_path / "Zivid_Two_Plus_M130_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusL110:
        return presets_path / "Zivid_Two_Plus_L110_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zividTwo:
        return presets_path / "Zivid_Two_M70_ManufacturingSpecular.yml"
    if camera.info.model == zivid.CameraInfo.Model.zividTwoL100:
        return presets_path / "Zivid_Two_L100_ManufacturingSpecular.yml"

    raise ValueError("Invalid camera model")


def _options() -> argparse.Namespace:
    """Function to read user arguments.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--settings-path",
        required=False,
        type=Path,
        help="Path to the camera settings YML file",
    )

    parser.add_argument(
        "--linear-rgb",
        action="store_true",
        help="Use linear RGB instead of sRGB",
    )

    return parser.parse_args()


def _main() -> None:
    user_options = _options()
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    if user_options.settings_path is None:
        user_options.settings_path = _preset_path(camera)
    print(f"Loading settings from file: {user_options.settings_path}")

    settings = zivid.Settings.load(user_options.settings_path)

    print("Capturing 2D frame")
    frame_2d = camera.capture_2d(settings)
    pixel_row = 100
    pixel_col = 50

    if user_options.linear_rgb:
        image_rgba = frame_2d.image_rgba()
        image_file = "ImageRGBA_linear.png"
        print(f"Saving 2D color image (sRGB color space) to file: {image_file}")
        image_rgba.save(image_file)

        rgba_data = image_rgba.copy_data()
        pixel_array_rgba = rgba_data[pixel_row, pixel_col]
        print(
            f"Color at pixel ({pixel_row},{pixel_col}): R:{pixel_array_rgba[0]} G:{pixel_array_rgba[1]} B:{pixel_array_rgba[2]} A:{pixel_array_rgba[3]}"
        )
    else:
        image_srgb = frame_2d.image_rgba_srgb()
        image_file = "ImageRGBA_sRGB.png"
        print(f"Saving 2D color image (sRGB color space) to file: {image_file}")
        image_srgb.save(image_file)

        srgb_data = image_srgb.copy_data()
        pixel_array_srgb = srgb_data[pixel_row, pixel_col]
        print(
            f"Color at pixel ({pixel_row},{pixel_col}): R:{pixel_array_srgb[0]} G:{pixel_array_srgb[1]} B:{pixel_array_srgb[2]} A:{pixel_array_srgb[3]}"
        )

    # More information about linear RGB and sRGB color spaces is available at:
    # https://support.zivid.com/en/latest/reference-articles/color-spaces-and-output-formats.html#color-spaces

    print("Capturing 3D frame")
    frame_3d = camera.capture_3d(settings)
    data_file = "Frame3D.zdf"
    print(f"Saving frame to file: {data_file}")
    frame_3d.save(data_file)

    data_file_ply = "PointCloudWithoutColor.ply"
    print(f"Exporting point cloud (default pink colored points) to file: {data_file_ply}")
    frame_3d.save(data_file_ply)

    print("Capturing 2D3D frame")
    frame = camera.capture_2d_3d(settings)
    data_file = "Frame.zdf"
    print(f"Saving frame to file: {data_file}")
    frame.save(data_file)

    data_file_ply = "PointCloudWithColor.ply"
    print(f"Exporting point cloud (default pink colored points) to file: {data_file_ply}")
    frame.save(data_file_ply)


if __name__ == "__main__":
    _main()
