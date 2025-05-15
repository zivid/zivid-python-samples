from datetime import timedelta

import numpy as np
import zivid
import zivid.presets
from zividsamples.color_to_grayscale import convert_rgba_to_grayscale


def get_matching_2d_preset_settings(
    camera: zivid.Camera,
    sampling_color: zivid.Settings2D.Sampling.Color,
    sampling_pixel: zivid.Settings2D.Sampling.Pixel,
) -> zivid.Settings2D:
    """Get the first 2D preset settings that matches the arguments.

    The function will raise an error if the camera model is not supported.

    Args:
        camera: Zivid camera

    Raises:
        RuntimeError: If no matched preset is found

    Returns:
        First 2D preset settings that matches

    """
    categories = zivid.presets.categories2d(camera.info.model)
    for category in categories:
        for preset in category.presets:
            if preset.settings.sampling.color == sampling_color and preset.settings.sampling.pixel == sampling_pixel:
                return preset.settings  # type: ignore
    raise RuntimeError(
        f"Failed to find a preset with sampling color {sampling_color} and sampling pixel {sampling_pixel} for {camera.info.model_name}."
    )


def update_exposure_based_on_relative_brightness(
    camera: zivid.Camera, settings_2d: zivid.Settings2D
) -> zivid.Settings2D:
    if settings_2d.acquisitions[0].brightness == 0.0:
        return settings_2d
    rgba_with_projector = camera.capture_2d(settings_2d).image_srgb().copy_data()
    grayscale_with_projector = convert_rgba_to_grayscale(rgba_with_projector)
    for acquisition in settings_2d.acquisitions:
        acquisition.brightness = 0.0
    rgba_without_projector = camera.capture_2d(settings_2d).image_srgb().copy_data()
    grayscale_without_projector = convert_rgba_to_grayscale(rgba_without_projector)
    grayscale_without_projector[grayscale_without_projector == 0] = np.nan
    # We assume that more pixels are not in projector shadow than in shadow. We can
    # then use median to get a good estimate of the brightness difference.
    relative_brightness = np.nanmedian(grayscale_with_projector / grayscale_without_projector)
    for acquisition in settings_2d.acquisitions:
        max_exposure_time = timedelta(microseconds=20000)
        current_exposure_time = acquisition.exposure_time
        exposure_increase = min(max_exposure_time - current_exposure_time, current_exposure_time * relative_brightness)
        acquisition.exposure_time += exposure_increase
        remaining_relative_brightness = relative_brightness / (exposure_increase / current_exposure_time)
        acquisition.gain *= remaining_relative_brightness
        acquisition.brightness = 0.0
    return settings_2d
