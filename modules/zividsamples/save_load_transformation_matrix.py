from pathlib import Path

from zividsamples.save_load_matrix import assert_affine_matrix_and_save, load_and_assert_affine_matrix
from zividsamples.transformation_matrix import TransformationMatrix


def save_transformation_matrix(transformation_matrix: TransformationMatrix, yaml_path: Path) -> None:
    """Save transformation matrix to YAML.

    Args:
        transformation_matrix: TransformationMatrix to be saved.
        yaml_path: Path to the YAML file where the matrix will be saved.

    Raises:
        RuntimeError: If the matrix is not affine.
    """
    assert_affine_matrix_and_save(transformation_matrix.as_matrix(), yaml_path)


def load_transformation_matrix(yaml_path: Path) -> TransformationMatrix:
    """Load transformation matrix from YAML.

    Args:
        yaml_path: Path to the YAML file from which the matrix will be loaded.

    Returns:
        Loaded TransformationMatrix if found, otherwise identity.
    """
    try:
        return TransformationMatrix.from_matrix(load_and_assert_affine_matrix(yaml_path))
    except RuntimeError as ex:
        print(f"Warning: {ex}")
        return TransformationMatrix()
