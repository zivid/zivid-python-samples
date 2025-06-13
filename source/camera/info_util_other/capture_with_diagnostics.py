"""
Capture point clouds, with color, from the Zivid camera, with settings from YML file and diagnostics enabled.

Enabling diagnostics allows collecting additional data to be saved in the ZDF file.
Send ZDF files with diagnostics enabled to the Zivid support team to allow more thorough troubleshooting.
Have in mind that enabling diagnostics increases the capture time and the RAM usage.

The YML file for this sample can be found under the main instructions for Zivid samples.

"""

import zivid
from zividsamples.paths import get_sample_data_path


def _settings_folder(camera: zivid.Camera) -> str:
    """Get folder name for settings files in Zivid Sample Data.

    Args:
        camera: Zivid camera

    Raises:
        RuntimeError: If camera is not supported

    Returns:
        Folder name

    """

    model = camera.info.model

    if model == zivid.CameraInfo.Model.zividTwo:
        return "zivid2"
    if model == zivid.CameraInfo.Model.zividTwoL100:
        return "zivid2"
    if model == zivid.CameraInfo.Model.zivid2PlusM130:
        return "zivid2Plus"
    if model == zivid.CameraInfo.Model.zivid2PlusM60:
        return "zivid2Plus"
    if model == zivid.CameraInfo.Model.zivid2PlusL110:
        return "zivid2Plus"
    if model == zivid.CameraInfo.Model.zivid2PlusMR130:
        return "zivid2Plus/R"
    if model == zivid.CameraInfo.Model.zivid2PlusMR60:
        return "zivid2Plus/R"
    if model == zivid.CameraInfo.Model.zivid2PlusLR110:
        return "zivid2Plus/R"
    raise RuntimeError(f"Unhandled enum value {camera.info.model}")


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings from file")
    settings_file = get_sample_data_path() / "Settings" / _settings_folder(camera) / "Settings01.yml"
    settings = zivid.Settings.load(settings_file)

    print("Enabling diagnostics")
    settings.diagnostics.enabled = True

    print("Capturing frame")
    frame = camera.capture_2d_3d(settings)
    data_file = "FrameWithDiagnostics.zdf"
    print(f"Saving frame with diagnostic data to file: {data_file}")
    frame.save(data_file)


if __name__ == "__main__":
    _main()
