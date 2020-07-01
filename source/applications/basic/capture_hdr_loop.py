"""Capture HDR frames in a loop (while actively changing HDR settings).

Three sets of HDR settings are chosen. These settings provide a dynamic range of about 9-10 stops,
with a decent lowlight and highlight frame, which is sufficient to grab good data on most scenes,
including shiny, for a medium camera operating at around 0.7 m to 1.2 m.

"""

import datetime
from pathlib import Path
import yaml
import zivid

from utils.paths import get_sample_data_path


def _read_settings_from_file(path: Path) -> zivid.Settings:
    settings_from_yaml = yaml.load(path.read_text(), Loader=yaml.Loader)["Settings"]
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

    # Initialize settings list
    number_of_frames_per_hdr = 3

    for hdr_index in range(3):
        print(f"Capturing an HDR image, alternative settings #{hdr_index+1}")
        settingslist = []
        for frame_index in range(number_of_frames_per_hdr):
            settings = _read_settings_from_file(
                Path()
                / Path()
                / get_sample_data_path()
                / "Settings/Set{hdr_index+1}/Frame0{frame_index+1}.yml"
            )
            print(
                f"\tFrame {frame_index + 1}:"
                f" Iris: {settings.iris}"
                f" Exposure: {settings.exposure_time.microseconds / 1000}ms"
                f" Gain: {settings.gain}"
            )
            settingslist.append(settings)

        with zivid.hdr.capture(camera, settingslist) as hdr_frame:
            out_file_name = f"HDR_Settings_{hdr_index+1}.zdf"
            print(f"Saving the HDR frame to: {out_file_name}")
            hdr_frame.save(out_file_name)


if __name__ == "__main__":
    _main()
