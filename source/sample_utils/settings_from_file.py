"""
Import settings from a .yml file
"""

import datetime
from pathlib import Path
import yaml

import zivid


def _acquisitions_from_yaml(acquisitions_from_yaml):
    acquisitions = []
    for acquisition in acquisitions_from_yaml:
        acquisitions.append(
            zivid.Settings.Acquisition(
                brightness=acquisition["Acquisition"]["Brightness"],
                aperture=acquisition["Acquisition"]["Aperture"],
                exposure_time=datetime.timedelta(microseconds=acquisition["Acquisition"]["ExposureTime"]),
                gain=acquisition["Acquisition"]["Gain"],
            )
        )
    return acquisitions


def _contrast_distortion_from_yaml(from_yaml):
    contrast_distortion = zivid.Settings.Processing.Filters.Experimental.ContrastDistortion()
    contrast_distortion.correction.enabled = from_yaml["Correction"]["Enabled"]
    contrast_distortion.correction.strength = from_yaml["Correction"]["Strength"]
    contrast_distortion.removal.enabled = from_yaml["Removal"]["Enabled"]
    contrast_distortion.removal.threshold = from_yaml["Removal"]["Threshold"]
    return contrast_distortion


def _filter_from_yaml(from_yaml):
    filters = zivid.Settings.Processing.Filters()
    filters.noise.removal.enabled = from_yaml["Noise"]["Removal"]["Enabled"]
    filters.noise.removal.threshold = from_yaml["Noise"]["Removal"]["Threshold"]
    filters.smoothing.gaussian.enabled = from_yaml["Smoothing"]["Gaussian"]["Enabled"]
    filters.smoothing.gaussian.sigma = from_yaml["Smoothing"]["Gaussian"]["Sigma"]
    filters.outlier.removal.enabled = from_yaml["Outlier"]["Removal"]["Enabled"]
    filters.outlier.removal.threshold = from_yaml["Outlier"]["Removal"]["Threshold"]
    filters.experimental.contrast_distortion = _contrast_distortion_from_yaml(
        from_yaml["Experimental"]["ContrastDistortion"]
    )
    return filters


def _color_from_yaml(from_yaml):
    color = zivid.Settings.Processing.Color()
    color.balance.red = from_yaml["Balance"]["Red"]
    color.balance.blue = from_yaml["Balance"]["Blue"]
    color.balance.green = from_yaml["Balance"]["Green"]
    color.gamma = from_yaml["Gamma"]
    return color


def get_settings_from_yaml(path: Path) -> zivid.Settings:
    """Get settings from .yml file.

    Args:
        path: Path to .yml file which contains settings

    Returns:
        settings: Zivid Settings

    """
    settings_from_yaml = yaml.load(path.read_text(), Loader=yaml.Loader)["Settings"]
    settings = zivid.Settings(
        acquisitions=_acquisitions_from_yaml(settings_from_yaml["Acquisitions"]),
        processing=zivid.Settings.Processing(
            filters=_filter_from_yaml(settings_from_yaml["Processing"]["Filters"]),
            color=_color_from_yaml(settings_from_yaml["Processing"]["Color"]),
        ),
    )
    return settings
