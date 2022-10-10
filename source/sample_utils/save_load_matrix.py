from pathlib import Path

import numpy as np
import yaml
import zivid


def assert_affine_matrix_and_save(matrix: np.ndarray, yaml_path: Path):
    """Save transformation to directory.

    Args:
        matrix: 4x4 transformation matrix
        yaml_path: Path to the YAML file

    """
    # Checks if matrix is affine
    zivid.calibration.Pose(matrix)

    dict_for_yaml = {}
    dict_for_yaml["__version__"] = {"serializer": 1, "data": 1}
    dict_for_yaml["FloatMatrix"] = {"Data": matrix.tolist()}

    with open(yaml_path, "w", encoding="utf-8") as outfile:
        yaml.safe_dump(dict_for_yaml, outfile, default_flow_style=None, sort_keys=False)


def load_and_assert_affine_matrix(yaml_file_path: Path):
    """Get Transformation Matrix from YAML.

    Args:
        yaml_file_path: Path to the YAML file

    Returns:
        matrix: 4x4 Transformation Matrix

    Raises:
        Exception: If no transform was read

    """
    with open(yaml_file_path, encoding="utf-8") as yaml_file:
        matrix = np.array(yaml.safe_load(yaml_file)["FloatMatrix"]["Data"])

    if matrix is None:
        raise Exception("No transform found on the provided path!")

    # Checks if matrix is affine
    zivid.calibration.Pose(matrix)

    return matrix
