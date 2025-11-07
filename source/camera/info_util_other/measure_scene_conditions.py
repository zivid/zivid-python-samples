"""
Measure ambient light conditions in the scene and output the measured flickering frequency of the ambient light if flickering is detected.
"""

import zivid
from zividsamples.paths import get_sample_data_path


def _find_settings_2d_3d(camera: zivid.Camera) -> str:
    """Find settings from preset for 2D and 3D capture depending on camera model.

    Args:
        camera: Zivid camera

    Raises:
        RuntimeError: If unsupported camera model for this code sample

    Returns:
        Zivid 2D and 3D settings path as a string

    """
    presets_path = get_sample_data_path() / "Settings"

    if camera.info.model == zivid.CameraInfo.Model.zivid3XL250:
        return presets_path / "Zivid_Three_XL250_DepalletizationQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusMR60:
        return presets_path / "Zivid_Two_Plus_MR60_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusMR130:
        return presets_path / "Zivid_Two_Plus_MR130_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusLR110:
        return presets_path / "Zivid_Two_Plus_LR110_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusM60:
        return presets_path / "Zivid_Two_Plus_M60_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusM130:
        return presets_path / "Zivid_Two_Plus_M130_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zivid2PlusL110:
        return presets_path / "Zivid_Two_Plus_L110_ConsumerGoodsQuality.yml"
    if camera.info.model == zivid.CameraInfo.Model.zividTwo:
        return presets_path / "Zivid_Two_M70_ManufacturingSpecular.yml"
    if camera.info.model == zivid.CameraInfo.Model.zividTwoL100:
        return presets_path / "Zivid_Two_L100_ManufacturingSpecular.yml"

    raise RuntimeError("Invalid camera model")


def add_suffix_before_extension(path: str, suffix: str) -> str:
    """Add a suffix before the file extension.

    Args:
        path: String representing a file path
        suffix: Suffix to add before the file extension (_50Hz or _60Hz)

    Returns:
        Modified file path with the added suffix

    """
    dot_pos = path.rfind(".")

    return path[:dot_pos] + suffix + path[dot_pos:]


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()
    print(f"Connected to {camera.info.serial_number}, {camera.info.model_name}.")

    print("Measuring scene conditions")
    scene_conditions = camera.measure_scene_conditions()
    flicker_classification = scene_conditions.ambient_light.flicker_classification
    print(f"Flicker classification: {flicker_classification}")

    if flicker_classification != "noFlicker":
        flicker_frequency = scene_conditions.ambient_light.flicker_frequency
        print(f"The measured flickering frequency in the scene: {flicker_frequency} Hz.")

    settings_path = ""
    if flicker_classification != "unknownFlicker":
        settings_path = _find_settings_2d_3d(camera)

    if flicker_classification == "noFlicker":
        print("No flickering lights were detected in the scene.")
    elif flicker_classification == "unknownFlicker":
        print("Flickering not found to match any known grid frequency.")
        print(
            "This is a non-standard flickering frequency. Consider adjusting the exposure time to be a multiple of this frequency to avoid artifacts."
        )
        return
    elif flicker_classification == "grid50hz":
        print("Found flickering corresponding to 50 Hz frequency in the scene, applying compensated preset:")
        settings_path = add_suffix_before_extension(settings_path, "_50Hz")
    elif flicker_classification == "grid60hz":
        print("Found flickering corresponding to 60 Hz frequency in the scene, applying compensated preset:")
        settings_path = add_suffix_before_extension(settings_path, "_60Hz")
    else:
        raise RuntimeError("Invalid flicker classification")

    print(settings_path)


if __name__ == "__main__":
    _main()
