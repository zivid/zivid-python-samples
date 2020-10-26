"""
This example shows how to use Capture Assistant to capture point clouds, with color, from the Zivid camera.
"""

import datetime
import zivid


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
        max_capture_time=datetime.timedelta(milliseconds=1200),
        ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
    )

    print(f"Running Capture Assistant with parameters: {suggest_settings_parameters}")
    settings = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)

    print("Settings suggested by Capture Assistant:")
    for acquisition in settings.acquisitions:
        print(acquisition)

    print("Manually configuring processing settings (Capture Assistant only suggests acquisition settings)")
    settings.processing.filters.reflection.removal.enabled = True
    settings.processing.filters.smoothing.gaussian.enabled = True
    settings.processing.filters.smoothing.gaussian.sigma = 1.5

    print("Capturing frame")
    with camera.capture(settings) as frame:
        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)


if __name__ == "__main__":
    _main()
