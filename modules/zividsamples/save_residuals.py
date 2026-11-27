"""
Save per-pose hand-eye calibration residuals to a YAML file.

"""

import math
from pathlib import Path
from typing import Iterable

import yaml


def _rotation_noise_floor_deg(translation_mm: float, point_rmse_mm: float, spatial_extent_mm: float) -> float:
    if math.isnan(point_rmse_mm) or spatial_extent_mm <= 0.0:
        return 0.0
    spread_mm = math.sqrt(max(0.0, point_rmse_mm**2 - translation_mm**2))
    return math.degrees(spread_mm / spatial_extent_mm)


def save_residuals(residuals: Iterable, yaml_path: Path) -> None:
    """Save per-pose hand-eye residuals to a YAML file in the layout Zivid Studio writes.

    Args:
        residuals: Iterable of residual objects with `rotation()`, `translation()`, `spatial_extent()` and
            `point_rmse()` methods.
        yaml_path: Destination YAML file path.

    """
    per_pose_residuals = [
        {
            "rotation_deg": float(r.rotation()),
            "translation_mm": float(r.translation()),
            "feature_extent_mm": float(r.spatial_extent()),
            "rotation_noise_floor_deg": _rotation_noise_floor_deg(
                float(r.translation()), float(r.point_rmse()), float(r.spatial_extent())
            ),
        }
        for r in residuals
    ]

    data = {"per_pose_residuals": per_pose_residuals}

    with open(yaml_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, sort_keys=False)
