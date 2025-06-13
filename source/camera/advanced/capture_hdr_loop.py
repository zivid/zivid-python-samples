"""
Cover the same dynamic range in a scene with different acquisition settings to optimize for quality, speed, or to find a compromise.

The camera captures multi-acquisition HDR point clouds in a loop, with settings from YML files.
The YML files for this sample can be found under the main Zivid sample instructions.

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

    for i in range(1, 4):
        settings_file = get_sample_data_path() / "Settings" / _settings_folder(camera) / f"Settings0{i :01d}.yml"
        print(f"Loading settings from file: {settings_file}")
        settings = zivid.Settings.load(settings_file)

        print("Capturing frame (HDR)")
        frame = camera.capture_2d_3d(settings)
        data_file = f"Frame0{i}.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)


if __name__ == "__main__":
    _main()
