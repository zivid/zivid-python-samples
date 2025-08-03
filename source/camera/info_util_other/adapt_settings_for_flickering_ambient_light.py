"""
Adapt camera acquisition settings based on known ambient light conditions.

Provided with a directory holding Zivid settings file(s), this
sample will adapt these settings to accommodate either 50 or 60 Hz
flickering frequencies based on user input. The output is new .yml
files with the adapted settings.

"""

import argparse
import math
import os
from datetime import timedelta
from pathlib import Path

import zivid
import zivid.settings


def _options() -> argparse.Namespace:
    """Function for taking in arguments from user.

    Returns:
        Argument from user

    """
    parser = argparse.ArgumentParser(
        description=(
            "Convert settings YMLs to adapt to an ambient light frequency (e.g. 50Hz/60Hz)\n"
            "Example:\n"
            "\t1) $ python adapt_settings_for_flickering_ambient_light.py --directory path/to/directory --frequency 50\n"
            "\t2) $ python adapt_settings_for_flickering_ambient_light.py --directory path/to/directory --frequency 60\n\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
        dest="directory",
        help="Path to directory with settings YMLs to be converted",
    )

    parser.add_argument(
        "-f",
        "--frequency",
        type=int,
        choices=[50, 60],
        required=True,
        dest="frequency",
        help="Frequency of the ambient light to adapt to (e.g. 50Hz/60Hz)",
    )

    parser.add_argument(
        "-m",
        "--model",
        type=str,
        choices=zivid.CameraInfo.Model.valid_values(),
        required=True,
        dest="model",
        help="Camera model of which the settings are to be adjusted for",
    )

    return parser.parse_args()


def _get_acquisition_settings_limits(camera_model: str) -> dict:
    """Finds the correct acquisition settings limits based on camera model.

    Args:
        camera_model: String with camera model name.

    Raises:
        RuntimeError: If unsupported or wrong camera model is given.

    Returns:
        Dictionary holding the limits of the different settings.

    """
    if camera_model in ["zivid2PlusMR60", "zivid2PlusLR110"]:
        limits = {
            "exposure_time": [timedelta(microseconds=900), timedelta(microseconds=100000)],
            "aperture": [2.37, 32],
            "brightness": [1.0, 2.5],  # Lower limit set for 2D color capture
            "gain": [1.0, 16.0],
        }
    elif camera_model == "zivid2PlusMR130":
        limits = {
            "exposure_time": [timedelta(microseconds=900), timedelta(microseconds=100000)],
            "aperture": [2.1, 32],
            "brightness": [1.0, 2.5],  # Lower limit set for 2D color capture
            "gain": [1.0, 16.0],
        }
    elif camera_model in ["zivid2PlusM60", "zivid2PlusL110"]:
        limits = {
            "exposure_time": [timedelta(microseconds=1677), timedelta(microseconds=100000)],
            "aperture": [2.37, 32],
            "brightness": [0, 2.5],
            "gain": [1.0, 16.0],
        }
    elif camera_model == "zivid2PlusM130":
        limits = {
            "exposure_time": [timedelta(microseconds=1677), timedelta(microseconds=100000)],
            "aperture": [2.1, 32],
            "brightness": [0, 2.5],
            "gain": [1.0, 16.0],
        }
    elif camera_model in ["zividTwo", "zividTwoL100"]:
        limits = {
            "exposure_time": [timedelta(microseconds=1677), timedelta(microseconds=100000)],
            "aperture": [1.8, 32],
            "brightness": [0, 1.8],
            "gain": [1.0, 16.0],
        }
    else:
        raise RuntimeError(f"Unsupported camera model: {camera_model}")

    return limits


def _find_max_aperture(settings: zivid.Settings) -> float:
    """Finds the maximum aperture among the acquisitions in the provided settings.

    Args:
        settings: Settings object holding the camera settings.

    Returns:
        Float holding the maximum aperture (f-number).

    """
    max_aperture = float("-inf")

    for acquisition in settings.acquisitions:
        max_aperture = max(max_aperture, acquisition.aperture)

    for acquisition in settings.color.acquisitions:
        max_aperture = max(max_aperture, acquisition.aperture)

    return max_aperture


def _get_snapped_exposure_time_to_closest_multiple(exposure_time: int, semi_period: float) -> int:
    """Finds the exposure time closest to a multiple of the given flickering frequency.

    Args:
        exposure_time: Integer with the exposure time before adapting.
        semi_period: Float with the time of half a cycle for the repeating signal.

    Returns:
        Integer with the new exposure time rounded.

    """
    multiple = max(1.0, round(exposure_time / semi_period))
    return round(semi_period * multiple)


def _frequency_adjusted_exposure_time(exposure_time: int, frequency: int) -> int:
    """Finds the right exposure time based on the flickering frequency of the light.

    Args:
        exposure_time: Integer with the exposure time before adapting.
        frequency: Integer with the flickering frequency of the ambient light (50 or 60).

    Returns:
        Integer with the new exposure time snapped to closest multiple.

    """
    semi_period_us = ((1.0 / frequency) / 2) * 1e6
    return _get_snapped_exposure_time_to_closest_multiple(exposure_time, semi_period_us)


def _clamp(value: float, lower_limit: float, upper_limit: float) -> float:
    """Ensures the inputted value is within a set range.

    Args:
        value: Float with the acquisition value to keep within the limits.
        lower_limit: Float with the lowest value allowed.
        upper_limit: Float with the highest value allowed.

    Returns:
        Float with the the value itself if within the limits, else the lower/upper limit.

    """
    return max(lower_limit, min(value, upper_limit))


def _exposure_mismatch(original_exposure: float, new_exposure: float) -> bool:
    """Finds whether or not the new exposure settings deviate more than 5% from the original settings.

    Args:
        original_exposure: Float with the exposure before adapting.
        new_exposure: Float with the exposure after adapting.

    Returns:
        Bool holding whether or not there was more than 5% change in exposure.

    """
    # If new exposure deviates more than 5% from the original exposure
    return abs(new_exposure / original_exposure - 1.0) > 0.05


def _adjust_acquisition(acquisition: zivid.settings.Settings.Acquisition, frequency: int, limits: dict) -> None:
    """Adjusts the acquisition settings to compensate for given flickering lights frequency.

    Args:
        acquisition: List holding the acquisition settings.
        frequency: Integer with the flickering frequency to compensate for (50 or 60).
        limits: Dictionary holding the limits for the different exposure settings.

    """

    exposure_time = int(acquisition.exposure_time.microseconds)
    aperture = acquisition.aperture
    gain = acquisition.gain
    brightness = acquisition.brightness

    if brightness == 0:
        # May happen for 2D captures, in which case we set it to 1 to effectively ignore it.
        # The brightness setting will only be be updated if it's impossible to get exposure
        # similar to the input exposure by only tuning the other parameters (ET, A, G).
        brightness = 1

    exposure = exposure_time * brightness * gain / aperture**2

    new_exposure_time = _frequency_adjusted_exposure_time(exposure_time, frequency)
    acquisition.exposure_time = timedelta(microseconds=new_exposure_time)

    if new_exposure_time > exposure_time:
        new_gain = 1.0
    else:
        new_gain = gain

    new_aperture = round(math.sqrt(new_exposure_time * brightness * new_gain / exposure), ndigits=2)
    new_aperture = _clamp(new_aperture, min(limits["aperture"]), max(limits["aperture"]))
    acquisition.aperture = new_aperture

    new_gain = round(exposure * new_aperture**2 / (new_exposure_time * brightness), ndigits=0)
    new_gain = _clamp(new_gain, min(limits["gain"]), max(limits["gain"]))
    acquisition.gain = new_gain

    new_exposure = new_exposure_time * brightness * new_gain / new_aperture**2
    if _exposure_mismatch(exposure, new_exposure):
        new_brightness = round(exposure * new_aperture**2 / (new_exposure_time * new_gain), ndigits=2)
        new_brightness = _clamp(new_brightness, min(limits["brightness"]), max(limits["brightness"]))
        acquisition.brightness = new_brightness

        new_exposure = new_exposure_time * new_brightness * new_gain / new_aperture**2
        if _exposure_mismatch(exposure, new_exposure):
            print(f"Unable to maintain same exposure after conversion: {exposure} -> {new_exposure}")
            print(f"  Old acquisition (ET, A, G, B): {exposure_time}, {aperture}, {gain}, {brightness}")
            print(f"  New acquisition (ET, A, G, B): {new_exposure_time}, {new_aperture}, {new_gain}, {new_brightness}")
            print("")
        else:
            print(
                f"Warning: Unable to retain the same exposure settings without adjusting brightness. New brightness: {new_brightness}"
            )


def _adapt_settings_to_ambient_light_frequency(settings_file: Path, frequency: int, limits: dict) -> zivid.Settings:
    """Adjusts the settings to counter the flickering frequency of the ambient light.

    Args:
        settings_file: Path to the settings file to be adjusted.
        frequency: Integer holding the flickering frequency (50 or 60).
        limits: Dictionary holding the upper and lower limits of the exposure settings.

    Returns:
        Zivid settings object holding the new settings.

    """
    settings = zivid.Settings.load(settings_file)

    # Upper aperture limit to ensure the camera will be in focus
    limits["aperture"][-1] = max(_find_max_aperture(settings), 5.66)

    acquisitions_2d = settings.color.acquisitions
    acquisitions_3d = settings.acquisitions

    for acquisition in acquisitions_2d:
        _adjust_acquisition(acquisition, frequency, limits)

    for acquisition in acquisitions_3d:
        # Lower limit for brightness to ensure sufficient signal for 3D
        limits["brightness"][0] = 1.0
        _adjust_acquisition(acquisition, frequency, limits)

    return settings


def _main() -> None:
    zivid.Application()

    args = _options()
    camera_model = args.model

    if not os.path.isdir(args.directory):
        raise argparse.ArgumentTypeError(f"{args.directory} is not a valid directory.")

    input_dir = Path(args.directory).resolve()
    output_dir = input_dir.parent / (input_dir.name + f"_{args.frequency}Hz")
    all_settings_paths = input_dir.rglob("*.yml")

    for settings_path in all_settings_paths:
        rel_path = settings_path.relative_to(input_dir)
        adapted_settings_dir = output_dir / rel_path
        adapted_settings_dir.parent.mkdir(parents=True, exist_ok=True)
        print(f"Converting '{settings_path.name}'")
        settings_file = Path(settings_path)

        acquisition_settings_limits = _get_acquisition_settings_limits(camera_model)
        new_settings = _adapt_settings_to_ambient_light_frequency(
            settings_file, args.frequency, acquisition_settings_limits
        )

        adapted_filename = settings_path.name.replace(".yml", f"_{args.frequency}Hz.yml")
        adapted_settings_path = adapted_settings_dir.with_name(adapted_filename)
        new_settings.save(adapted_settings_path)

    print(f"Converted settings saved to '{output_dir.absolute()}'")


if __name__ == "__main__":  # NOLINT
    _main()
