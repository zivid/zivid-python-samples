"""
Balance color for RGB image.
"""

import datetime
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
import zivid


@dataclass
class MeanColor:
    """
    RGB channel mean colors

    Attributes:
        red (np.array): Red channel mean value
        green (np.array): Green channel mean value
        blue (np.array): Blue channel mean value

    """

    red: np.array
    green: np.array
    blue: np.array


def _display_rgb(rgb, title):
    """Display RGB image.

    Args:
        rgb: RGB image
        title: Image title

    Returns None

    """
    plt.figure()
    plt.imshow(rgb)
    plt.title(title)
    plt.show(block=False)


def _set_settings(dimension, iris, exposure_time, brightness, gain):
    """Set settings for capture (3D or 2D).

    Args:
        dimension: '3d' or '2d'
        iris: Iris
        exposure_time: Exposure time
        brightness: Projector brightness
        gain: Gain

    Returns:
        settings: Capture settings (3D or 2D)

    Raises:
        ValueError: If dimension is not '3d' or '2d'

    """
    if dimension == "3d":
        settings = zivid.Settings()
        settings.iris = iris
        settings.exposure_time = datetime.timedelta(microseconds=exposure_time)
        settings.brightness = brightness
        settings.gain = gain
    elif dimension == "2d":
        settings = zivid.Settings2D()
        settings.iris = iris
        settings.exposure_time = datetime.timedelta(microseconds=exposure_time)
        settings.brightness = brightness
        settings.gain = gain
    else:
        raise ValueError(
            f"The dimension value should be '3d' or '2d', got: '{dimension}'"
        )

    return settings


def _capture_rgb(camera, settings_2d):
    """Capture 2D RGB image.

    Args:
        camera: Zivid camera
        settings_2d: 2D capture settings

    Returns:
        rgb: RGB image

    """
    frame_2d = camera.capture_2d(settings_2d)
    image = frame_2d.image().to_array()
    rgb = np.dstack([image["r"], image["g"], image["b"], image["a"]])

    return rgb


def _compute_mean_rgb(rgb, pixels):
    """Compute mean RGB values.

    Args:
        rgb: RGB image
        pixels: Number of central pixels for computation

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
    mean_color = MeanColor(red=mean_red, green=mean_green, blue=mean_blue)

    return mean_color


def _apply_color_balance(rgb, red_balance, blue_balance):
    """Apply color balance to RGB image.

    Args:
        rgb: Input RGB image
        red_balance: Red balance
        blue_balance: Blue balance

    Returns:
        corrected_image: RGB image after color balance

    """
    default_red_balance = zivid.Settings().red_balance
    default_blue_balance = zivid.Settings().blue_balance
    corrected_rgb = np.copy(rgb)
    corrected_rgb[:, :, 0] = rgb[:, :, 0] * red_balance / default_red_balance
    corrected_rgb[:, :, 2] = rgb[:, :, 2] * blue_balance / default_blue_balance

    return corrected_rgb


def _color_balance_calibration(camera, settings_3d):
    """Balance color for RGB image by taking images of white surface (piece of paper, wall, etc.) in a loop.

    Args:
        camera: Zivid camera
        settings_3d: 3D capture settings

    Returns:
        corrected_red_balance: Corrected red balance
        corrected_blue_balance: Corrected blue balance

    """
    print(f"Starting color balance calibration")
    corrected_red_balance = 1.0
    corrected_blue_balance = 1.0
    settings_list = [settings_3d]
    first_iteration = True
    while True:
        settings_3d.red_balance = corrected_red_balance
        settings_3d.blue_balance = corrected_blue_balance
        frame = zivid.hdr.capture(camera, settings_list)
        point_cloud = frame.get_point_cloud().to_array()
        rgb = np.dstack([point_cloud["r"], point_cloud["g"], point_cloud["b"]])
        if first_iteration:
            _display_rgb(rgb, "RGB image before color balance (3D capture)")
            first_iteration = False
        mean_color = _compute_mean_rgb(rgb, 100)
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
        if int(mean_color.green) == int(mean_color.red) and int(
            mean_color.green
        ) == int(mean_color.blue):
            break
        corrected_red_balance = (
            camera.settings.red_balance * mean_color.green / mean_color.red
        )
        corrected_blue_balance = (
            camera.settings.blue_balance * mean_color.green / mean_color.blue
        )
    _display_rgb(rgb, "RGB image after color balance (3D capture)")

    return (corrected_red_balance, corrected_blue_balance)


def _main():

    app = zivid.Application()

    camera = app.connect_camera()

    iris = 21
    exposure_time = 10000
    brightness = 0.0
    gain = 16.0

    settings_3d = _set_settings("3d", iris, exposure_time, brightness, gain)
    settings_2d = _set_settings("2d", iris, exposure_time, brightness, gain)

    [red_balance, blue_balance] = _color_balance_calibration(camera, settings_3d)

    print(f"Applying color balance on 2D image")
    rgb = _capture_rgb(camera, settings_2d)
    rgb_balanced = _apply_color_balance(rgb, red_balance, blue_balance)

    _display_rgb(rgb, "RGB image before color balance (2D capture)")
    _display_rgb(rgb_balanced, "RGB image after color balance (2D capture)")


if __name__ == "__main__":
    _main()
