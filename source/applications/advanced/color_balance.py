"""
This example shows how to balance color of 2D image.
"""

import datetime
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
import zivid


@dataclass
class MeanColor:
    """
    RGB  channel mean colors

    Attributes:
        red (np.array): Red channel mean value
        green (np.array): Green channel mean value
        blue (np.array): Blue channel mean value

    """

    red: np.float64
    green: np.float64
    blue: np.float64


def _display_rgb(rgb, title):
    """Display RGB image.

    Args:
        rgb: RGB image (HxWx3 darray)
        title: Image title

    Returns None

    """
    plt.figure()
    plt.imshow(rgb)
    plt.title(title)
    plt.show(block=False)


def _compute_mean_rgb(rgb, pixels):
    """Compute mean RGB values.

    Args:
        rgb: RGB image (HxWx3 darray)
        pixels: Number of central pixels (^2) for computation

    Returns:
        mean_color: RGB channel mean values

    """
    height = np.shape(rgb)[0]
    width = np.shape(rgb)[1]
    pixel_hight_start_index = int((height - pixels) / 2)
    pixel_hight_end_index = int((height + pixels) / 2)
    pixel_width_start_index = int((width - pixels) / 2)
    pixel_width_end_index = int((width + pixels) / 2)
    red = rgb[
        pixel_hight_start_index:pixel_hight_end_index,
        pixel_width_start_index:pixel_width_end_index,
        0,
    ]
    green = rgb[
        pixel_hight_start_index:pixel_hight_end_index,
        pixel_width_start_index:pixel_width_end_index,
        1,
    ]
    blue = rgb[
        pixel_hight_start_index:pixel_hight_end_index,
        pixel_width_start_index:pixel_width_end_index,
        2,
    ]
    mean_red = np.mean(np.reshape(red, -1), dtype=np.float64)
    mean_green = np.mean(np.reshape(green, -1), dtype=np.float64)
    mean_blue = np.mean(np.reshape(blue, -1), dtype=np.float64)

    return MeanColor(red=mean_red, green=mean_green, blue=mean_blue)


def _color_balance_calibration(camera, settings_2d):
    """Balance color for RGB image by taking images of white surface (piece of paper, wall, etc.) in a loop.

    Args:
        camera: Zivid camera
        settings_2d: 2D capture settings

    Returns:
        corrected_red_balance: Corrected red balance
        corrected_blue_balance: Corrected blue balance

    """
    print("Starting color balance calibration")
    corrected_red_balance = 1.0
    corrected_blue_balance = 1.0
    first_iteration = True
    while True:
        settings_2d.processing.color.balance.red = corrected_red_balance
        settings_2d.processing.color.balance.blue = corrected_blue_balance
        rgba = camera.capture(settings_2d).image_rgba().copy_data()
        if first_iteration:
            _display_rgb(rgba[:, :, 0:3], "RGB image before color balance")
            first_iteration = False
        mean_color = _compute_mean_rgb(rgba[:, :, 0:3], 100)
        print(
            (
                "Mean color values: R = "
                f"{int(mean_color.red)} "
                "G = "
                f"{int(mean_color.green)} "
                "B = "
                f"{int(mean_color.blue)} "
            )
        )
        if int(mean_color.green) == int(mean_color.red) and int(mean_color.green) == int(mean_color.blue):
            break
        corrected_red_balance = settings_2d.processing.color.balance.red * mean_color.green / mean_color.red
        corrected_blue_balance = settings_2d.processing.color.balance.blue * mean_color.green / mean_color.blue
    _display_rgb(rgba[:, :, 0:3], "RGB image after color balance")

    return (corrected_red_balance, corrected_blue_balance)


def _main():

    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings")
    settings_2d = zivid.Settings2D(
        acquisitions=[
            zivid.Settings2D.Acquisition(
                aperture=5.66,
                exposure_time=datetime.timedelta(microseconds=80000),
                brightness=0.0,
                gain=2.0,
            )
        ],
    )

    rgba = camera.capture(settings_2d).image_rgba().copy_data()
    _display_rgb(rgba[:, :, 0:3], "RGB image before color balance")

    [red_balance, blue_balance] = _color_balance_calibration(camera, settings_2d)

    print("Applying color balance on 2D image")
    settings_2d.processing.color.balance.red = red_balance
    settings_2d.processing.color.balance.blue = blue_balance
    rgba_balanced = camera.capture(settings_2d).image_rgba().copy_data()

    _display_rgb(rgba_balanced[:, :, 0:3], "RGB image after color balance")
    input("Press Enter to close...")


if __name__ == "__main__":
    _main()
