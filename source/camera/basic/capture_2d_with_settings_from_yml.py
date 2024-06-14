"""
Capture 2D images from the Zivid camera, with settings from YML file.

"""

import argparse
from pathlib import Path

import zivid
from sample_utils.display import display_rgb


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
        print("Getting RGBA image")
        image = frame_2d.image_rgba()
        rgba = image.copy_data()

        display_rgb(rgba[:, :, 0:3], title="RGB image", block=True)

        image_file = "Image.png"
        print(f"Saving 2D color image to file: {image_file}")
        image.save(image_file)


if __name__ == "__main__":
    _main()
