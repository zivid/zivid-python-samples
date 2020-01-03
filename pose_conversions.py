"""Example to show conversions to/from Transformation Matrix.

Zivid primarily operate with a (4x4) Transformation Matrix (Rotation Matrix + Translation Vector).
This example shows how to use Eigen to convert to and from:
  AxisAngle, Rotation Vector, Roll-Pitch-Yaw, Quaternion

 It provides convenience functions that can be reused in applicable applications.
"""

import enum
from pathlib import Path
import numpy as np
import cv2
from scipy.spatial.transform import Rotation as R


def _main():
    np.set_printoptions(precision=4)
    print(f"This example shows conversions to/from Transformation Matrix")

    transformation_matrix = get_transformation_matrix_from_yaml("robotTransform.yaml")
    print(f"{transformation_matrix}")

    # Extract Rotation Matrix and Translation Vector from Transformation Matrix
    print(f"RotationMatrix:\n{transformation_matrix[:-1,:-1]}")
    print(f"TranslationVector:\n{transformation_matrix[:-1, -1]}")

    # Convert from Zivid to Robot (Transformation Matrix --> any format)
    representations = zivid_to_robot(transformation_matrix)

    # Convert from Robot to Zivid (any format --> Rotation Matrix)
    transformation_matrix2 = robot_to_zivid(
        representations, transformation_matrix[:-1, -1]
    )
    # Combine Rotation Matrix with Translation Vector to form Transformation Matrix
    save_transformation_matrix_to_yaml(transformation_matrix2, "robotTransformOut.yaml")


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
            raise ValueError(f"Angle provided, but vector is not unit vector")

    def as_rotvec(self):
        """Return rotation vector from axis angle.

        Returns:
            rotation vector

        """
        return self.axis * self.angle

    def __str__(self):
        """Return string representation of axis angle.

        Returns:
            string representation

        """
        return f"Axis:\n{self.axis}\nAngle:\n{self.angle:.4}"


def zivid_to_robot(transformation_matrix):
    """Convert from Zivid to Robot (Transformation Matrix --> any format).

    Args:
        transformation_matrix: a numpy array (4x4)

    Returns:
        Various robot representations as defined in the class Representations

    """
    rotation_matrix = transformation_matrix[:3, :3]
    rotation = R.from_matrix(rotation_matrix)
    robot_representations = {
        "axis_angle": AxisAngle(),
        "rotation_vector": np.zeros(3),
        "quaternion": np.zeros(4),
        "rotations": list(),
    }

    print(f"\nConverting Rotation Matrix to Axis-Angle")
    robot_representations["axis_angle"] = AxisAngle(rotation.as_rotvec())
    print(robot_representations["axis_angle"])

    print(f"\nConverting Axis-Angle to Rotation Vector")
    robot_representations["rotation_vector"] = robot_representations[
        "axis_angle"
    ].as_rotvec()
    print(f"{robot_representations['rotation_vector']}")

    print(f"\nConverting Rotation Matrix to Quaternion")
    robot_representations["quaternion"] = rotation.as_quat()
    print(f"{robot_representations['quaternion']}")

    for convention in RotationConvention:
        print(
            f"\nConverting Rotation Matrix to Roll-Pitch-Yaw angles ({convention.name}):"
        )
        robot_representations["rotations"].append(
            {
                "convention": convention,
                "roll_pitch_yaw": rotation.as_euler(convention.value),
            }
        )
        print(f"{robot_representations['rotations'][-1]['roll_pitch_yaw']}")

    return robot_representations


def robot_to_zivid(representations, translation_vector):
    """Convert from Robot to Zivid (any format --> Rotation Matrix).

    Args:
        representations: Various robot representations
        translation_vector: a 3x1 numpy vector

    Returns:
        4x4 Transformation Matrix

    """
    for rotation in representations["rotations"]:
        print(
            f"\nConverting Roll-Pitch-Yaw angles ({rotation['convention'].name})"
            + " to Rotation Matrix:"
        )
        rotation_matrix_from_roll_pitch_yaw = R.from_euler(
            rotation["convention"].value, rotation["roll_pitch_yaw"]
        )
        print(f"{rotation_matrix_from_roll_pitch_yaw.as_matrix()}")

    print(f"\nConverting Rotation Vector to Axis-Angle")
    axis_angle = AxisAngle(representations["rotation_vector"])
    print(axis_angle)

    print(f"\nConverting Axis-Angle to Quaternion:")
    quaternion = R.from_rotvec(axis_angle.as_rotvec()).as_quat()
    print(f"{quaternion}")

    print(f"\nConverting Quaternion to Rotation Matrix:")
    rotation_matrix_from_quaternion = R.from_quat(quaternion).as_matrix()
    print(f"{rotation_matrix_from_quaternion}")

    transformation_matrix = np.identity(4, float)
    transformation_matrix[:-1, :-1] = rotation_matrix_from_quaternion
    transformation_matrix[:-1, -1] = translation_vector

    return transformation_matrix


def save_transformation_matrix_to_yaml(transformation_matrix2, path: Path):
    """Save Transformation Matrix to YAML. Uses OpenCV to maintain yaml format.

    Args:
        transformation_matrix2: 4x4 Transformation Matrix
        path: path to save the YAML output

    """
    file_storage_out = cv2.FileStorage(path, cv2.FILE_STORAGE_WRITE)
    file_storage_out.write("TransformationMatrixFromQuaternion", transformation_matrix2)
    file_storage_out.release()


def get_transformation_matrix_from_yaml(path: Path):
    """Get Transformation Matrix from YAML. Uses OpenCV to maintain yaml format.

    Args:
        path: path to save the YAML output

    Returns:
        4x4 Transformation Matrix

    """
    file_storage_in = cv2.FileStorage(path, cv2.FILE_STORAGE_READ)
    transformation_matrix = file_storage_in.getNode("PoseState").mat()
    file_storage_in.release()
    return transformation_matrix


if __name__ == "__main__":
    _main()
