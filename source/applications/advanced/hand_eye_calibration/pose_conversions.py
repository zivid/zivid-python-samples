"""
This example shows how to convert to/from transformation matrix (rotation matrix + translation vector).

Zivid primarily operate with a (4x4) transformation matrix. This example shows how to use Eigen to convert to and from:
AxisAngle, Rotation Vector, Roll-Pitch-Yaw, Quaternion.

The convenience functions from this example can be reused in applicable applications. The YAML files for this sample
can be found under the main instructions for Zivid samples.
"""

import enum
from pathlib import Path
from dataclasses import dataclass, field
import numpy as np
import cv2
from scipy.spatial.transform import Rotation as R

from sample_utils.paths import get_sample_data_path


def _main():
    np.set_printoptions(precision=4, suppress=True)
    print_header("This example shows conversions to/from Transformation Matrix")

    transformation_matrix = get_transformation_matrix_from_yaml(
        Path() / get_sample_data_path() / "RobotTransform.yaml"
    )
    print(f"Transformation Matrix:\n{transformation_matrix}")

    # Extract Rotation Matrix and Translation Vector from Transformation Matrix
    print(f"Rotation Matrix:\n{transformation_matrix[:3,:3]}")
    print(f"Translation Vector:\n{transformation_matrix[:-1, -1]}")

    ###
    # Convert from Zivid to Robot (Transformation Matrix --> any format)
    ###
    print_header("Convert from Zivid (Rotation Matrix) to Robot")
    axis_angle = rotation_matrix_to_axis_angle(transformation_matrix[:3, :3])
    print(f"AxisAngle:\n{axis_angle.axis}, {axis_angle.angle:.4f}")
    rotation_vector = rotation_matrix_to_rotation_vector(transformation_matrix[:3, :3])
    print(f"Rotation Vector:\n{rotation_vector}")
    quaternion = rotation_matrix_to_quaternion(transformation_matrix[:3, :3])
    print(f"Quaternion:\n{quaternion}")
    rpy_list = rotation_matrix_to_roll_pitch_yaw(transformation_matrix[:3, :3])

    ###
    # Convert from Robot to Zivid (any format --> Rotation Matrix (part of Transformation Matrix))
    ###
    print_header("Convert from Robot to Zivid (Rotation Matrix)")
    rotation_matrix = axis_angle_to_rotation_matrix(axis_angle)
    print(f"Rotation Matrix from Axis Angle:\n{rotation_matrix}")
    rotation_matrix = rotation_vector_to_rotation_matrix(rotation_vector)
    print(f"Rotation Matrix from Rotation Vector:\n{rotation_matrix}")
    rotation_matrix = quaternion_to_rotation_matrix(quaternion)
    print(f"Rotation Matrix from Quaternion:\n{rotation_matrix}")
    roll_pitch_yaw_to_rotation_matrix(rpy_list)

    # Replace rotation matrix in transformation matrix
    transformation_matrix[:3, :3] = rotation_matrix
    # Save transformation matrix which has passed through quaternion representation
    save_transformation_matrix_to_yaml(transformation_matrix, "RobotTransformOut.yaml")


class RotationConvention(enum.Enum):
    """Convenience enum class to list rotation conventions for Roll Pitch Yaw."""

    ZYX_Intrinsic = "ZYX"
    XYZ_Extrinsic = "xyz"
    XYZ_Intrinsic = "XYZ"
    ZYX_Extrinsic = "zyx"


class AxisAngle:
    """Convenience class to access rotation axis and angle."""

    def __init__(self, axis=np.array([0, 0, 1]), angle=None):
        """Initialize class and its variables.

        Can be initialized with a unit vector and an angle, or only a rotation vector.

        Args:
            axis: rotation axis
            angle: rotation angle

        Raises:
            ValueError: if angle vector is provided, but vector is not a unit vector

        """
        self.angle = angle
        self.axis = axis
        if angle is None:
            self.angle = np.linalg.norm(axis)
            self.axis = axis / self.angle
        elif np.linalg.norm(axis) != 0:
            raise ValueError("Angle provided, but vector is not unit vector")

    def as_rotvec(self):
        """Return rotation vector from axis angle.

        Returns:
            rotation vector

        """
        return self.axis * self.angle

    def as_quaternion(self):
        """Return quaternion from axis angle.

        Returns:
            quaternion

        """
        return R.from_rotvec(self.as_rotvec()).as_quat()


@dataclass
class Representations:
    """Class to hold various transformation representations."""

    axis_angle: AxisAngle() = AxisAngle()
    rotation_vector: np.array = np.zeros(3)
    quaternion: np.array = np.zeros(4)
    rotations: list = field(default_factory=list)


def rotation_matrix_to_axis_angle(rotation_matrix):
    """Convert from Rotation Matrix --> Axis Angle.

    Args:
        rotation_matrix: a numpy array (3x3)

    Returns:
        AxisAngle

    """
    rotation = R.from_matrix(rotation_matrix)
    return AxisAngle(rotation.as_rotvec())


def rotation_matrix_to_rotation_vector(rotation_matrix):
    """Convert from Rotation Matrix --> Rotation Vector.

    Args:
        rotation_matrix: a numpy array (3x3)

    Returns:
        Rotation Vector

    """
    rotation = R.from_matrix(rotation_matrix)
    return rotation.as_rotvec()


def rotation_matrix_to_quaternion(rotation_matrix):
    """Convert from Rotation Matrix --> Quaternion.

    Args:
        rotation_matrix: a numpy array (3x3)

    Returns:
        Quaternion

    """
    rotation = R.from_matrix(rotation_matrix)
    return rotation.as_quat()


def rotation_matrix_to_roll_pitch_yaw(rotation_matrix):
    """Convert from Rotation Matrix --> Roll Pitch Yaw.

    Args:
        rotation_matrix: a numpy array (3x3)

    Returns:
        list of Roll Pitch Yaw angles in radians

    """
    rpy_list = list()
    rotation = R.from_matrix(rotation_matrix)
    for convention in RotationConvention:
        roll_pitch_yaw = rotation.as_euler(convention.value)
        print(f"Roll-Pitch-Yaw angles ({convention.name}):")
        print(f"{roll_pitch_yaw}")
        rpy_list.append({"convention": convention, "roll_pitch_yaw": roll_pitch_yaw})
    return rpy_list


def axis_angle_to_rotation_matrix(axis_angle: AxisAngle):
    """Convert from AxisAngle --> Rotation Matrix.

    Args:
        axis_angle: an AxisAngle object with axis and angle

    Returns:
        Rotation Matrix (3x3 numpy array)

    """
    return R.from_quat(axis_angle.as_quaternion()).as_matrix()


def rotation_vector_to_rotation_matrix(rotvec):
    """Convert from Rotation Vector --> Rotation Matrix.

    Args:
        rotvec: a 3x1 numpy array

    Returns:
        Rotation Matrix (3x3 numpy array)

    """
    return R.from_rotvec(rotvec).as_matrix()


def quaternion_to_rotation_matrix(quaternion):
    """Convert from Quaternion --> Rotation Matrix.

    Args:
        quaternion: a 4x1 numpy array

    Returns:
        Rotation Matrix (3x3 numpy array)

    """
    return R.from_quat(quaternion).as_matrix()


def roll_pitch_yaw_to_rotation_matrix(rpy_list):
    """Convert from Roll Pitch Yaw --> Rotation Matrix.

    Args:
        rpy_list: list of Roll Pitch Yaw angles in radians

    Returns None

    """
    for rotation in rpy_list:
        rotation_matrix = R.from_euler(rotation["convention"].value, rotation["roll_pitch_yaw"]).as_matrix()
        print(f"Rotation Matrix from Roll-Pitch-Yaw angles ({rotation['convention'].name}):")
        print(f"{rotation_matrix}")


def save_transformation_matrix_to_yaml(transformation_matrix, path: Path):
    """Save Transformation Matrix to YAML. Uses OpenCV to maintain yaml format.

    Args:
        transformation_matrix: 4x4 Transformation Matrix
        path: path to save the YAML output

    Returns None

    """
    file_storage_out = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    file_storage_out.write("TransformationMatrixFromQuaternion", transformation_matrix)
    file_storage_out.release()


def get_transformation_matrix_from_yaml(path):
    """Get Transformation Matrix from YAML. Uses OpenCV to maintain yaml format.

    Args:
        path: path to the YAML file

    Returns:
        4x4 Transformation Matrix

    """
    file_storage_in = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    transformation_matrix = file_storage_in.getNode("PoseState").mat()
    file_storage_in.release()
    return transformation_matrix


def print_header(txt: str):
    """Print decorated header.

    Args:
        txt: Text to be printed in header

    Returns None

    """
    terminal_width = 70
    print()
    print(f"{'*' * terminal_width}")
    print(f"* {txt} {' ' * (terminal_width - len(txt) - 4)}*")
    print(f"{'*' * terminal_width}")


if __name__ == "__main__":
    _main()
