"""
Balance color of a 2D image by using a Zivid calibration board.

Provide your own 2D acquisition settings and balance colors using these settings. Be aware that the settings should
provide enough exposure so that the calibration board can be detected, and make sure the calibration board is in view
of the camera.

If you want to use your own white reference (white wall, piece of paper, etc.) instead of using the calibration board,
you can provide your own mask in _main().

"""

import argparse
from pathlib import Path

import zivid
from zividsamples.calibration_board_utils import find_white_mask_from_checkerboard
from zividsamples.display import display_rgb
from zividsamples.white_balance_calibration import camera_may_need_color_balancing, white_balance_calibration


def _options() -> argparse.Namespace:
    """Configure and take command line arguments from user.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(
        description=(
            "Balance the color of a 2D image\n"
            "Example:\n"
            "\t $ python color_balance.py path/to/settings.yml\n\n"
            "where path/to/settings.yml is the path to the 2D acquisition settings you want to find color balance for."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

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

    if not camera_may_need_color_balancing(camera):
        print(f"{camera.info.model_name} does not need color balancing, skipping ...")
        return

    settings_2d = zivid.Settings2D.load(user_options.path)

    rgba = camera.capture_2d(settings_2d).image_rgba_srgb().copy_data()
    display_rgb(rgba[:, :, 0:3], title="RGB image before color balance", block=False)

    print("Finding the white squares of the checkerboard as white reference ...")
    white_mask = find_white_mask_from_checkerboard(rgba[:, :, 0:3])

    red_balance, green_balance, blue_balance = white_balance_calibration(camera, settings_2d, white_mask)

    print("Applying color balance on 2D image:")
    print(f" Red: {red_balance}")
    print(f" Green: {green_balance}")
    print(f" Blue: {blue_balance}")

    settings_2d.processing.color.balance.red = red_balance
    settings_2d.processing.color.balance.green = green_balance
    settings_2d.processing.color.balance.blue = blue_balance
    rgba_balanced = camera.capture_2d(settings_2d).image_rgba_srgb().copy_data()

    display_rgb(rgba_balanced[:, :, 0:3], title="RGB image after color balance", block=True)

    print("Saving settings after color balance")
    zivid.Settings2D.save(settings_2d, "Settings2DAfterColorBalance.yml")


if __name__ == "__main__":
    _main()
