"""
A basic warm-up method for a Zivid camera with specified time and capture cycle.

The sample uses Capture Assistant unless a path to YAML Camera Settings is passed.
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
        help="Path to the YAML file that contains Camera Settings",
    )

    parser.add_argument(
        "--capture-cycle",
        required=False,
        type=float,
        default=5.0,
        help="Capture cycle in seconds",
    )

    return parser.parse_args()


def _main() -> None:
    user_options = _options()
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    warmup_time = timedelta(minutes=10)
    capture_cycle = timedelta(seconds=user_options.capture_cycle)

    if user_options.settings_path:
        print("Loading settings from file")
        settings = zivid.Settings.load(Path(user_options.settings_path))
    else:
        print("Getting camera settings from capture assistant")
        suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
            max_capture_time=timedelta(milliseconds=1000),
            ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
        )
        settings = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)

    before_warmup = datetime.now()

    print(f"Starting warm up for {warmup_time} minutes")
    while (datetime.now() - before_warmup) < warmup_time:
        before_capture = datetime.now()
        camera.capture(settings)
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

    print("Warm up completed")


if __name__ == "__main__":
    _main()
