"""
Save and load Zivid 4x4 transformation matrices from and to YAML files.

"""

from pathlib import Path
from typing import Union

import numpy as np
import zivid


def assert_affine(matrix: Union[np.ndarray, zivid.Matrix4x4]) -> None:
    """Ensures that the matrix is affine.

    Args:
        matrix: Transformation matrix (4x4), np.ndarray or zivid.Matrix4x4

    Raises:
        RuntimeError: If matrix is not affine

    """
    try:
        zivid.calibration.Pose(matrix)
    except RuntimeError as ex:
        raise RuntimeError("matrix is not affine") from ex


def assert_affine_matrix_and_save(matrix: Union[np.ndarray, zivid.Matrix4x4], yaml_path: Path) -> None:
    """Save transformation matrix to YAML.

    Args:
        matrix: Transformation matrix (4x4), np.ndarray or zivid.Matrix4x4
        yaml_path: Path to the YAML file

    """
    assert_affine(matrix)

    zivid.Matrix4x4(matrix).save(yaml_path)


def load_and_assert_affine_matrix(yaml_file_path: Path) -> np.ndarray:
    """Get transformation matrix from YAML.

    Args:
        yaml_file_path: Path to the YAML file

    Returns:
        matrix: Affine 4x4 matrix of np.ndarray type

    Raises:
        RuntimeError: If no transform was read

    """

    if not yaml_file_path.exists():
        raise RuntimeError(f"File {yaml_file_path} not found!")

    try:
        matrix = np.array(zivid.Matrix4x4(yaml_file_path))

    except RuntimeError as ex:
        raise RuntimeError(f"Failed to load matrix from {yaml_file_path}") from ex

    assert_affine(matrix)

    return matrix
