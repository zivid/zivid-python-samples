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


def _auto_settings_configuration(camera):
    """Automatically configure 2D capture settings by taking images in a loop while tunning gain, exposure time, and
    aperture. The goal is that the maximum of mean RGB values reaches the value within defined limits.

    Args:
        camera: Camera

    Returns:
        settings_2d: 2D capture settings

    """
    print("Starting auto settings configuration")
    desired_color_range = [200, 225]
    settings_2d = zivid.Settings2D(
        acquisitions=[
            zivid.Settings2D.Acquisition(
                aperture=8,
                exposure_time=datetime.timedelta(microseconds=20000),
                brightness=0.0,
                gain=2.0,
            )
        ],
    )
    fnums = [11.31, 8, 5.6, 4, 2.8, 2]
    setting_tunning_index = 1
    cnt = 0
    timeout_cnt = 25
    timeout_break = False

    while True:
        rgba = camera.capture(settings_2d).image_rgba().copy_data()
        mean_color = _compute_mean_rgb(rgba[:, :, 0:3], 100)
        max_mean_color = max(mean_color.red, mean_color.green, mean_color.blue)
        print(f"Iteration: {cnt+1}")
        print(f" Max mean color: {max_mean_color} ")
        print(f" Desired color range: [{desired_color_range[0]},{desired_color_range[1]}]")

        # Breaking on timeout the first time 2D image is not saturated
        if timeout_break is True and max_mean_color < 255:
            break

        if max_mean_color <= desired_color_range[0] or max_mean_color >= desired_color_range[1]:
            color_ratio = np.mean(desired_color_range) / max_mean_color
            if setting_tunning_index == 1:
                settings_2d.acquisitions[0].gain = np.clip(settings_2d.acquisitions[0].gain * color_ratio, 1, 16)
                print(f" New gain: {settings_2d.acquisitions[0].gain}")
                setting_tunning_index = 2
            elif setting_tunning_index == 2:
                new_exp = settings_2d.acquisitions[0].exposure_time.microseconds * color_ratio
                settings_2d.acquisitions[0].exposure_time = datetime.timedelta(
                    microseconds=np.clip(new_exp, 6500, 100000)
                )
                print(f" New exposure time: {settings_2d.acquisitions[0].exposure_time.microseconds}")
                setting_tunning_index = 3
            elif setting_tunning_index == 3:
                fnum_index = fnums.index(settings_2d.acquisitions[0].aperture)
                if color_ratio > 1:
                    settings_2d.acquisitions[0].aperture = np.clip(fnums[fnum_index + 1], fnums[-1], fnums[0])
                if color_ratio < 1:
                    settings_2d.acquisitions[0].aperture = np.clip(fnums[fnum_index - 1], fnums[-1], fnums[0])
                setting_tunning_index = 1
                print(f" New aperture: {settings_2d.acquisitions[0].aperture}")
            cnt = cnt + 1
        else:
            print("Auto settings configuration sucessful")
            break
        if cnt >= timeout_cnt:
            timeout_break = True
    print("Settings:")
    print(settings_2d.acquisitions[0])
    return settings_2d


def _color_balance_calibration(camera, settings_2d):
    """Balance color for RGB image by taking images of white surface (piece of paper, wall, etc.) in a loop.

    Args:
        camera: Zivid camera
        settings_2d: 2D capture settings

    Returns:
        corrected_red_balance: Corrected red balance
        corrected_green_balance: Corrected green balance
        corrected_blue_balance: Corrected blue balance

    """
    print("Starting color balance calibration")

    corrected_red_balance = 1.0
    corrected_green_balance = 1.0
    corrected_blue_balance = 1.0

    saturated = False

    while True:
        settings_2d.processing.color.balance.red = corrected_red_balance
        settings_2d.processing.color.balance.green = corrected_green_balance
        settings_2d.processing.color.balance.blue = corrected_blue_balance
        rgba = camera.capture(settings_2d).image_rgba().copy_data()
        mean_color = _compute_mean_rgb(rgba[:, :, 0:3], 100)
        print(" Mean color values:")
        print(f"  R: {int(mean_color.red)}")
        print(f"  G: {int(mean_color.green)}")
        print(f"  B: {int(mean_color.blue)}")
        if int(mean_color.green) == int(mean_color.red) and int(mean_color.green) == int(mean_color.blue):
            print("Color balance successful")
            break
        if saturated is True:
            print("Color balance incomplete - the range limits of color balance parameters have been reached")
            break
        max_color = max(mean_color.red, mean_color.green, mean_color.blue)
        corrected_red_balance = np.clip(settings_2d.processing.color.balance.red * max_color / mean_color.red, 1, 2)
        corrected_green_balance = np.clip(
            settings_2d.processing.color.balance.green * max_color / mean_color.green, 1, 2
        )
        corrected_blue_balance = np.clip(settings_2d.processing.color.balance.blue * max_color / mean_color.blue, 1, 2)

        if (
            corrected_red_balance == 1.0
            or corrected_red_balance == 2.0
            or corrected_green_balance == 1.0
            or corrected_green_balance == 2.0
            or corrected_blue_balance == 1.0
            or corrected_blue_balance == 2.0
        ):
            saturated = True
    print("Color balance:")
    print(f" Red: {corrected_red_balance}")
    print(f" Green: {corrected_green_balance}")
    print(f" Blue: {corrected_blue_balance}")

    return (corrected_red_balance, corrected_green_balance, corrected_blue_balance)


def _main():

    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    settings_2d = _auto_settings_configuration(camera)

    rgba = camera.capture(settings_2d).image_rgba().copy_data()
    _display_rgb(rgba[:, :, 0:3], "RGB image before color balance")

    [red_balance, green_balance, blue_balance] = _color_balance_calibration(camera, settings_2d)

    print("Applying color balance on 2D image")
    settings_2d.processing.color.balance.red = red_balance
    settings_2d.processing.color.balance.green = green_balance
    settings_2d.processing.color.balance.blue = blue_balance
    rgba_balanced = camera.capture(settings_2d).image_rgba().copy_data()

    _display_rgb(rgba_balanced[:, :, 0:3], "RGB image after color balance")
    input("Press Enter to close...")


if __name__ == "__main__":
    _main()
