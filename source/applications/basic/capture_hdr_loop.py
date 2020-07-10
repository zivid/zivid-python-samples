"""Capture HDR frames in a loop (while actively changing HDR settings).

Three sets of HDR settings are chosen. These settings provide a dynamic range of about 9-10 stops,
with a decent lowlight and highlight frame, which is sufficient to grab good data on most scenes,
including shiny, for a medium camera operating at around 0.7 m to 1.2 m.

"""

from pathlib import Path
import zivid

from utils.paths import get_sample_data_path
from utils.settings_from_file import get_settings_from_yaml


def _main():
    app = zivid.Application()

    print("Connecting to the camera")
    camera = app.connect_camera()

    for hdr_index in range(1, 4):
        print(f"Capturing an HDR image, alternative settings #{hdr_index}")
        settings = get_settings_from_yaml(
            Path() / get_sample_data_path() / f"Settings/Settings{hdr_index:02d}.yml"
        )

        with camera.capture(settings) as hdr_frame:
            out_file_name = f"HDR_Settings_{hdr_index}.zdf"
            print(f"Saving the HDR frame to: {out_file_name}")
            hdr_frame.save(out_file_name)


if __name__ == "__main__":
    _main()
