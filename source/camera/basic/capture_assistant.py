"""Capture Assistant sample."""
import datetime
import zivid


def _main():
    app = zivid.Application()
    camera = app.connect_camera()

    suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
        max_capture_time=datetime.timedelta(milliseconds=1200),
        ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
    )

    settings = zivid.capture_assistant.suggest_settings(
        camera, suggest_settings_parameters
    )

    with camera.capture(settings) as hdr_frame:
        hdr_frame.save("Result.zdf")


if __name__ == "__main__":
    _main()
