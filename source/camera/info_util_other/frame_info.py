"""
Read frame info from the Zivid camera.

The frame info consists of the version information for installed software at the time of capture,
information about the system that captured the frame, and the time stamp of the capture.

"""

import datetime

import zivid


def _assisted_capture(camera: zivid.Camera) -> zivid.Frame:
    """Acquire frame with capture assistant.

    Args:
        camera: Zivid camera

    Returns:
        frame: Zivid frame

    """
    suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
        max_capture_time=datetime.timedelta(milliseconds=800),
        ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
    )
    settings = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)
    return camera.capture(settings)


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    frame = _assisted_capture(camera)

    frame_info = frame.info

    print("The version information for installed software at the time of image capture:")
    print(frame_info.software_version)

    print("Information about the system that captured this frame:")
    print(frame_info.system_info)

    print("The time of frame capture:")
    print(frame_info.time_stamp)

    print("Acquisition time:")
    print(f"{frame_info.metrics.acquisition_time.total_seconds() * 1000:.0f} ms")

    print("Capture time:")
    print(f"{frame_info.metrics.capture_time.total_seconds() * 1000:.0f} ms")


if __name__ == "__main__":
    _main()
