from pathlib import Path
from typing import Iterable

import yaml


def save_residuals(residuals: Iterable, yaml_path: Path) -> None:
    """Save per-pose hand-eye residuals to a YAML file.

    Args:
        residuals: Iterable of residual objects with `rotation()` and `translation()` methods.
        yaml_path: Destination YAML file path.

    """
    per_pose_residuals = [
        {
            "rotation_deg": float(r.rotation()),
            "translation_mm": float(r.translation()),
        }
        for r in residuals
    ]

    data = {"per_pose_residuals": per_pose_residuals}

    with open(yaml_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, sort_keys=False)
