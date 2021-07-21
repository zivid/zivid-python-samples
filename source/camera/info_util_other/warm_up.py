"""
This example shows how to warm up the camera.
"""

from time import sleep
from datetime import datetime, timedelta

import zivid


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    warmup_time = timedelta(minutes=10)
    capture_cycle = timedelta(seconds=5)
    max_capture_time = timedelta(milliseconds=1000)

    print("Getting camera settings")
    suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
        max_capture_time=max_capture_time,
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
        print(f"Remaining time is {remaining_time_minutes} minutes and {remaining_time_seconds} seconds.")

    print("Warm up completed")


if __name__ == "__main__":
    _main()