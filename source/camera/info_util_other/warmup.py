"""
Short example of a basic way to warm up the camera with specified time and capture cycle.

"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

import zivid


def _options() -> argparse.Namespace:
    """Function to read user arguments.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--settings-path",
        required=False,
        help="Path to the YML file that contains camera settings",
    )

    parser.add_argument(
        "--capture-cycle",
        required=False,
        type=float,
        default=5.0,
        help="Capture cycle in seconds",
    )

    return parser.parse_args()


def _load_or_default_settings(settings_path: str) -> zivid.Settings:
    """Load settings from YML file or use default settings.

    Args:
        settings_path: Path to the YML file that contains camera settings

    Returns:
        Camera Settings

    """

    if settings_path:
        print("Loading settings from file")
        return zivid.Settings.load(Path(settings_path))

    print("Using default 3D settings")
    settings = zivid.Settings(acquisitions=[zivid.Settings.Acquisition()])

    return settings


def _main() -> None:
    user_options = _options()
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    warmup_time = timedelta(minutes=10)
    capture_cycle = timedelta(seconds=user_options.capture_cycle)
    settings = _load_or_default_settings(user_options.settings_path)

    before_warmup = datetime.now()

    print(f"Starting warmup for {warmup_time} minutes")
    while (datetime.now() - before_warmup) < warmup_time:
        before_capture = datetime.now()

        # Use the same capture method as you would use in production
        # to get the most accurate results from warmup
        camera.capture_3d(settings)

        after_capture = datetime.now()

        duration = after_capture - before_capture

        if duration.seconds <= capture_cycle.seconds:
            sleep(capture_cycle.seconds - duration.seconds)
        else:
            print(
                "Your capture time is longer than your desired capture cycle. \
                 Please increase the desired capture cycle."
            )

        remaining_time = warmup_time - (datetime.now() - before_warmup)
        remaining_time_minutes = remaining_time.seconds // 60
        remaining_time_seconds = remaining_time.seconds % 60
        print(f"Remaining time: {remaining_time_minutes} minutes, {remaining_time_seconds} seconds.")

    print("Warmup completed")


if __name__ == "__main__":
    _main()
