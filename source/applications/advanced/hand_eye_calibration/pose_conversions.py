"""
Convert to/from Transformation Matrix (Rotation Matrix + Translation Vector).

Zivid primarily operate with a (4x4) transformation matrix. This example shows how to use Eigen to convert to and from:
AxisAngle, Rotation Vector, Roll-Pitch-Yaw, Quaternion.

The convenience functions from this example can be reused in applicable applications. The YAML files for this sample
can be found under the main instructions for Zivid samples.

"""

import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import zivid
from scipy.spatial.transform import Rotation as R
from zividsamples.paths import get_sample_data_path
from zividsamples.save_load_matrix import assert_affine_matrix_and_save, load_and_assert_affine_matrix


class RotationConvention(enum.Enum):
    """Convenience enum class to list rotation conventions for Roll Pitch Yaw."""

    ZYX_INTRINSIC = "ZYX"
    XYZ_EXTRINSIC = "xyz"
    XYZ_INTRINSIC = "XYZ"
    ZYX_EXTRINSIC = "zyx"


class AxisAngle:
    """Convenience class to access rotation axis and angle."""

    axis: np.ndarray
    angle: np.floating

    def __init__(self, axis: np.ndarray = np.array([0, 0, 1]), angle: Optional[float] = None):
        """Initialize class and its variables.

        Can be initialized with a unit vector and an angle, or only a rotation vector.

        Args:
            axis: Rotation axis
            angle: Rotation angle

        Raises:
            ValueError: If angle vector is provided, but vector is not a unit vector

        """
        self.axis = axis
        if angle is None:
            self.angle = np.linalg.norm(axis)
            self.axis = axis / self.angle
        elif np.linalg.norm(axis) != 0:
            raise ValueError("Angle provided, but vector is not unit vector")
        else:
            self.angle: np.floating = np.floating(angle)

    def as_rotvec(self) -> np.ndarray:
        """Return rotation vector from axis angle.

        Returns:
            Rotation vector

        """
        return self.axis * self.angle

    def as_quaternion(self) -> np.ndarray:
        """Return quaternion from axis angle.

        Returns:
            Quaternion

        """
        return R.from_rotvec(self.as_rotvec()).as_quat()


@dataclass
class Representations:
    """Class to hold various transformation representations."""

    axis_angle: AxisAngle = AxisAngle()
    rotation_vector: np.ndarray = field(default_factory=lambda: np.zeros(3))
    quaternion: np.ndarray = field(default_factory=lambda: np.zeros(4))
    rotations: list = field(default_factory=list)


def rotation_matrix_to_axis_angle(rotation_matrix: np.ndarray) -> AxisAngle:
    """Convert from Rotation Matrix --> Axis Angle.

    Args:
        rotation_matrix: A numpy array (3x3)

    Returns:
        AxisAngle

    """
    rotation = R.from_matrix(rotation_matrix)
    return AxisAngle(rotation.as_rotvec())


def rotation_matrix_to_rotation_vector(rotation_matrix: np.ndarray) -> np.ndarray:
    """Convert from Rotation Matrix --> Rotation Vector.

    Args:
        rotation_matrix: A numpy array (3x3)

    Returns:
        Rotation Vector

    """
    rotation = R.from_matrix(rotation_matrix)
    return rotation.as_rotvec()


def rotation_matrix_to_quaternion(rotation_matrix: np.ndarray) -> np.ndarray:
    """Convert from Rotation Matrix --> Quaternion.

    Args:
        rotation_matrix: A numpy array (3x3)

    Returns:
        Quaternion

    """
    rotation = R.from_matrix(rotation_matrix)
    return rotation.as_quat()


def rotation_matrix_to_roll_pitch_yaw(rotation_matrix: np.ndarray) -> List[Dict]:
    """Convert from Rotation Matrix --> Roll Pitch Yaw.

    Args:
        rotation_matrix: A numpy array (3x3)

    Returns:
        rpy_list: List of Roll Pitch Yaw angles in radians

    """
    rpy_list = []
    rotation = R.from_matrix(rotation_matrix)
    for convention in RotationConvention:
        roll_pitch_yaw = rotation.as_euler(convention.value)
        print(f"Roll-Pitch-Yaw angles ({convention.name}):")
        print(f"{roll_pitch_yaw}")
        rpy_list.append({"convention": convention, "roll_pitch_yaw": roll_pitch_yaw})
    return rpy_list


def axis_angle_to_rotation_matrix(axis_angle: AxisAngle) -> np.ndarray:
    """Convert from AxisAngle --> Rotation Matrix.

    Args:
        axis_angle: An AxisAngle object with axis and angle

    Returns:
        Rotation Matrix (3x3 numpy array)

    """
    return R.from_quat(axis_angle.as_quaternion()).as_matrix()


def rotation_vector_to_rotation_matrix(rotvec: np.ndarray) -> np.ndarray:
    """Convert from Rotation Vector --> Rotation Matrix.

    Args:
        rotvec: A 3x1 numpy array

    Returns:
        Rotation Matrix (3x3 numpy array)

    """
    return R.from_rotvec(rotvec).as_matrix()


def quaternion_to_rotation_matrix(quaternion: np.ndarray) -> np.ndarray:
    """Convert from Quaternion --> Rotation Matrix.

    Args:
        quaternion: A 4x1 numpy array

    Returns:
        Rotation Matrix (3x3 numpy array)

    """
    return R.from_quat(quaternion).as_matrix()


def roll_pitch_yaw_to_rotation_matrix(rpy_list: List[Dict]) -> None:
    """Convert from Roll Pitch Yaw --> Rotation Matrix.

    Args:
        rpy_list: List of Roll Pitch Yaw angles in radians

    """
    for rotation in rpy_list:
        rotation_matrix = R.from_euler(rotation["convention"].value, rotation["roll_pitch_yaw"]).as_matrix()
        print(f"Rotation Matrix from Roll-Pitch-Yaw angles ({rotation['convention'].name}):")
        print(f"{rotation_matrix}")


def print_header(txt: str) -> None:
    """Print decorated header.

    Args:
        txt: Text to be printed in header

    """
    terminal_width = 70
    print()
    print(f"{'*' * terminal_width}")
    print(f"* {txt} {' ' * (terminal_width - len(txt) - 4)}*")
    print(f"{'*' * terminal_width}")


def _main() -> None:
    # Application class must be initialized before using other Zivid classes.
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    np.set_printoptions(precision=4, suppress=True)
    print_header("This example shows conversions to/from Transformation Matrix")

    transformation_matrix = load_and_assert_affine_matrix(get_sample_data_path() / "RobotTransform.yaml")
    print(f"Transformation Matrix:\n{transformation_matrix}")

    # Extract Rotation Matrix and Translation Vector from Transformation Matrix
    rotation_matrix = transformation_matrix[:3, :3]
    translation_vector = transformation_matrix[:-1, -1]
    print(f"Rotation Matrix:\n{rotation_matrix}")
    print(f"Translation Vector:\n{translation_vector}")

    ###
    # Convert from Zivid to Robot (Transformation Matrix --> any format)
    ###
    print_header("Convert from Zivid (Rotation Matrix) to Robot")
    axis_angle = rotation_matrix_to_axis_angle(rotation_matrix)
    print(f"AxisAngle:\n{axis_angle.axis}, {axis_angle.angle:.4f}")
    rotation_vector = rotation_matrix_to_rotation_vector(rotation_matrix)
    print(f"Rotation Vector:\n{rotation_vector}")
    quaternion = rotation_matrix_to_quaternion(rotation_matrix)
    print(f"Quaternion:\n{quaternion}")
    rpy_list = rotation_matrix_to_roll_pitch_yaw(rotation_matrix)

    ###
    # Convert from Robot to Zivid (any format --> Rotation Matrix (part of Transformation Matrix))
    ###
    print_header("Convert from Robot to Zivid (Rotation Matrix)")
    rotation_matrix_from_axis_angle = axis_angle_to_rotation_matrix(axis_angle)
    print(f"Rotation Matrix from Axis Angle:\n{rotation_matrix_from_axis_angle}")
    rotation_matrix_from_rotation_vector = rotation_vector_to_rotation_matrix(rotation_vector)
    print(f"Rotation Matrix from Rotation Vector:\n{rotation_matrix_from_rotation_vector}")
    rotation_matrix_from_quaternion = quaternion_to_rotation_matrix(quaternion)
    print(f"Rotation Matrix from Quaternion:\n{rotation_matrix_from_quaternion}")
    roll_pitch_yaw_to_rotation_matrix(rpy_list)

    # Replace rotation matrix in transformation matrix
    transformation_matrix_from_quaternion = np.eye(4)
    transformation_matrix_from_quaternion[:3, :3] = rotation_matrix_from_quaternion
    transformation_matrix_from_quaternion[:-1, -1] = translation_vector
    # Save transformation matrix which has passed through quaternion representation
    assert_affine_matrix_and_save(
        transformation_matrix_from_quaternion, Path(__file__).parent / "RobotTransformOut.yaml"
    )


if __name__ == "__main__":
    _main()
