"""
Balance color for 2D capture using white surface as reference.

"""

from typing import Tuple

import numpy as np
import zivid


def get_central_pixels_mask(image_shape: Tuple, num_pixels: int = 100) -> np.ndarray:
    """Get mask for central NxN pixels in an image.

    Args:
        image_shape: (H, W) of image to mask
        num_pixels: Number of central pixels to mask

    Returns:
        mask: Mask of (num_pixels)x(num_pixels) central pixels

    """
    height = image_shape[0]
    width = image_shape[1]

    height_start = int((height - num_pixels) / 2)
    height_end = int((height + num_pixels) / 2)
    width_start = int((width - num_pixels) / 2)
    width_end = int((width + num_pixels) / 2)

    mask = np.zeros((height, width))
    mask[height_start:height_end, width_start:width_end] = 1

    return mask


def compute_mean_rgb_from_mask(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Find the mean RGB channels in the masked area of an RGB image.

    Args:
        rgb: (H, W, 3) RGB image
        mask: (H, W) of bools masking the image

    Returns:
        Mean RGB channels (1, 3) from the masked area

    """
    repeated_mask = ~np.repeat(mask[:, :, np.newaxis], rgb.shape[2], axis=2).astype(bool)
    mean_rgb = np.ma.masked_array(rgb, repeated_mask).mean(axis=(0, 1))

    return mean_rgb


def camera_may_need_color_balancing(camera: zivid.Camera) -> bool:
    """Check if camera may need color balancing.

    Args:
        camera: Zivid camera

    Returns:
        True if camera may need color balance, False otherwise

    """
    if camera.info.model in (
        zivid.CameraInfo.Model.zivid2PlusMR130,
        zivid.CameraInfo.Model.zivid2PlusMR60,
        zivid.CameraInfo.Model.zivid2PlusLR110,
    ):
        return False
    return True


def white_balance_calibration(
    camera: zivid.Camera, settings_2d: zivid.Settings2D, mask: np.ndarray
) -> Tuple[float, float, float]:
    """Balance color for RGB image by taking images of white surface (checkers, piece of paper, wall, etc.) in a loop.

    Args:
        camera: Zivid camera
        settings_2d: 2D capture settings
        mask: (H, W) of bools masking the white surface

    Raises:
        RuntimeError: If camera does not need color balancing

    Returns:
        corrected_red_balance: Corrected red balance
        corrected_green_balance: Corrected green balance
        corrected_blue_balance: Corrected blue balance

    """
    if not camera_may_need_color_balancing(camera):
        raise RuntimeError(f"{camera.info.model} does not need color balancing.")

    corrected_red_balance = 1.0
    corrected_green_balance = 1.0
    corrected_blue_balance = 1.0

    saturated = False

    while True:
        settings_2d.processing.color.balance.red = corrected_red_balance
        settings_2d.processing.color.balance.green = corrected_green_balance
        settings_2d.processing.color.balance.blue = corrected_blue_balance

        rgba = camera.capture_2d(settings_2d).image_rgba_srgb().copy_data()
        mean_color = compute_mean_rgb_from_mask(rgba[:, :, 0:3], mask)

        mean_red, mean_green, mean_blue = mean_color[0], mean_color[1], mean_color[2]

        if int(mean_green) == int(mean_red) and int(mean_green) == int(mean_blue):
            break
        if saturated is True:
            break
        max_color = max(float(mean_red), float(mean_green), float(mean_blue))
        corrected_red_balance = float(np.clip(settings_2d.processing.color.balance.red * max_color / mean_red, 1, 8))
        corrected_green_balance = float(
            np.clip(settings_2d.processing.color.balance.green * max_color / mean_green, 1, 8)
        )
        corrected_blue_balance = float(np.clip(settings_2d.processing.color.balance.blue * max_color / mean_blue, 1, 8))

        corrected_values = [corrected_red_balance, corrected_green_balance, corrected_blue_balance]

        if 1.0 in corrected_values or 8.0 in corrected_values:
            saturated = True

    return (corrected_red_balance, corrected_green_balance, corrected_blue_balance)
