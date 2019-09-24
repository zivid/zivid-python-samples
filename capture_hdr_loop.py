"""Capture HDR frames in a loop (while actively changing HDR settings).

Three sets of HDR settings are chosen. These settings provide a dynamic range of about 9-10 stops,
with a decent lowlight and highlight frame, which is sufficient to grab good data on most scenes,
including shiny, for a medium camera operating at around 0.7 m to 1.2 m.

"""

import datetime
from pathlib import Path
import yaml
import zivid


def _read_settings_from_file(path: Path) -> zivid.Settings:
    settings_from_yaml = yaml.load(open(path, "rb").read(), Loader=yaml.Loader)[
        "Settings"
    ]
    settings = zivid.Settings(
        brightness=settings_from_yaml["Brightness"],
        exposure_time=datetime.timedelta(
            microseconds=settings_from_yaml["ExposureTime"]
        ),
        gain=settings_from_yaml["Gain"],
        iris=settings_from_yaml["Iris"],
    )
    filters = settings_from_yaml["Filters"]
    settings.filters.contrast.enabled = filters["Contrast"]["Enabled"]
    settings.filters.contrast.threshold = filters["Contrast"]["Threshold"]
    settings.filters.gaussian.enabled = filters["Gaussian"]["Enabled"]
    settings.filters.gaussian.sigma = filters["Gaussian"]["Sigma"]
    settings.filters.outlier.enabled = filters["Outlier"]["Enabled"]
    settings.filters.outlier.threshold = filters["Outlier"]["Threshold"]
    settings.filters.reflection.enabled = filters["Reflection"]["Enabled"]
    settings.filters.saturated.enabled = filters["Saturated"]["Enabled"]
    return settings


def _main():
    app = zivid.Application()

    print("Connecting to the camera")
    camera = app.connect_camera()

    # Get current settings, to be modified before use
    settings = [camera.settings for _ in range(3)]

    for hdr_index in range(3):
        print(f"Capturing an HDR image, alternative settings #{hdr_index+1}")
        for frame_index in range(len(settings)):
            settings[frame_index] = _read_settings_from_file(
                Path(f"settings/set{hdr_index+1}/frame_0{frame_index+1}.yml")
            )
            print(
                f"\tFrame {frame_index + 1}:"
                f" Iris: {settings[frame_index].iris}"
                f" Exposure: {settings[frame_index].exposure_time.microseconds / 1000}ms"
                f" Gain: {settings[frame_index].gain}"
            )

        with camera.capture(settings) as hdr_frame:
            out_file_name = f"HDR_Settings_{hdr_index+1}.zdf"
            print(f"Saving the HDR frame to: {out_file_name}")
            hdr_frame.save(out_file_name)


if __name__ == "__main__":
    _main()
