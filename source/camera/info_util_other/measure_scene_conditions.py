"""
Measure ambient light conditions in the scene and output the measured flickering frequency of the ambient light if flickering is detected.
"""

import zivid
import zivid.presets
from zividsamples.paths import get_sample_data_path


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()
    print(f"Connected to {camera.info.serial_number}, {camera.info.model_name}.")

    print("Measuring scene conditions")
    scene_conditions = camera.measure_scene_conditions()
    flicker_classification = scene_conditions.ambient_light.flicker_classification

    if flicker_classification == "noFlicker":
        print("No flickering lights were detected in the scene.")
        settings_path = (
            get_sample_data_path()
            / "Settings"
            / f"{camera.info.model_name.replace('2+', 'Two_Plus').replace('2', 'Two').replace(' ', '_')}_ConsumerGoodsFast.yml"
        )
        print(settings_path)
        return

    if flicker_classification == "unknownFlicker":
        unknown_flicker_frequency = scene_conditions.ambient_light.flicker_frequency
        print("Flickering not found to match any known grid frequency.")
        print(f"Measured flickering frequency in the scene is: {unknown_flicker_frequency} Hz.")
        print(
            "This is a non-standard flickering frequency. Consider adjusting the exposure time to be a multiple of this frequency to avoid artifacts."
        )
        return
    if flicker_classification == "grid50hz":
        print("Found flickering corresponding to 50 Hz frequency in the scene, applying compensated preset:")
        settings_50_hz_path = (
            get_sample_data_path()
            / "Settings"
            / f"{camera.info.model_name.replace('2+', 'Two_Plus').replace('2', 'Two').replace(' ', '_')}_ConsumerGoodsFast_50Hz.yml"
        )
        print(settings_50_hz_path)
    elif flicker_classification == "grid60hz":
        print("Found flickering corresponding to 60 Hz frequency in the scene, applying compensated preset:")
        settings_60_hz_path = (
            get_sample_data_path()
            / "Settings"
            / f"{camera.info.model_name.replace('2+', 'Two_Plus').replace('2', 'Two').replace(' ', '_')}_ConsumerGoodsFast_60Hz.yml"
        )
        print(settings_60_hz_path)

    flicker_frequency = scene_conditions.ambient_light.flicker_frequency
    print(f"The measured flickering frequency in the scene: {flicker_frequency} Hz.")


if __name__ == "__main__":
    _main()
