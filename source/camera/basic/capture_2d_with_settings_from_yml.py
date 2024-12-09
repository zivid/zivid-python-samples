"""
Capture 2D images from the Zivid camera, with settings from YML file.

The color information is provided in linear RGB and sRGB color spaces.
Color represented in linear RGB space is suitable as input to traditional computer vision algorithms.
Color represented in sRGB color space is suitable for showing an image on a display.
More information about linear RGB and sRGB color spaces is available at:
https://support.zivid.com/en/latest/reference-articles/color-spaces-and-output-formats.html#color-spaces

"""

import argparse
from pathlib import Path

import zivid
from zividsamples.display import display_rgb


def _options() -> argparse.Namespace:
    """Configure and take command line arguments from user.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        dest="path",
        type=Path,
        help="Path to YML containing 2D capture settings",
    )

    return parser.parse_args()


def _main() -> None:
    app = zivid.Application()

    user_options = _options()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring 2D settings")
    # Note: The Zivid SDK supports 2D captures with a single acquisition only
    settings_2d = zivid.Settings2D.load(user_options.path)

    print("Capturing 2D frame")
    with camera.capture(settings_2d) as frame_2d:
        print("Getting color image (linear RGB color space)")
        image_rgba = frame_2d.image_rgba()
        rgba = image_rgba.copy_data()

        display_rgb(rgba[:, :, 0:3], title="Color image (Linear RGB color space)", block=True)

        image_rgb_file = "ImageRGB.png"
        print(f"Saving 2D color image (linear RGB color space) to file: {image_rgb_file}")
        image_rgba.save(image_rgb_file)

        print("Getting color image (sRGB color space)")
        image_srgb = frame_2d.image_srgb()
        srgb = image_srgb.copy_data()

        display_rgb(srgb[:, :, 0:3], title="Color image (sRGB color space)", block=True)

        image_srgb_file = "ImageSRGB.png"
        print(f"Saving 2D color image  (sRGB color space) to file: {image_srgb_file}")
        image_srgb.save(image_srgb_file)


if __name__ == "__main__":
    _main()
