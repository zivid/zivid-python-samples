from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation


@dataclass
class TransformationMatrix:
    """Class for simplifying the creation and manipulation of 4x4 homogenous transformation matrices."""

    translation: np.ndarray = np.array((0, 0, 0))
    rotation: Rotation = Rotation.from_matrix(np.identity(3))

    @staticmethod
    def from_matrix(matrix: np.ndarray) -> "TransformationMatrix":
        """Creates a TransformationMatrix object from a 4x4 matrix array.

        Args:
            matrix: A 4x4 matrix array that represents a 4x4 homogenous transformation matrix

        Returns:
            A TransformationMatrix object that represents a 4x4 homogenous transformation matrix

        """
        return TransformationMatrix(
            translation=matrix[:3, 3],
            rotation=Rotation.from_matrix(matrix[:3, :3]),
        )

    def as_matrix(self) -> np.ndarray:
        """Creates a matrix object as 4x4 matrix array from a TransformationMatrix object.

        Returns:
            matrix: A 4x4 matrix array that represents a 4x4 homogenous transformation matrix

        """
        matrix = np.identity(n=4)
        matrix[:3, :3] = self.rotation.as_matrix()
        matrix[:3, 3] = self.translation
        return matrix

    def inverse(self) -> "TransformationMatrix":
        """Inverts a 4x4 matrix of TransformationMatrix instance.

        Returns:
            An inverted 4x4 matrix that is instance of TransformationMatrix

        """
        return TransformationMatrix.from_matrix(
            matrix=np.linalg.inv(self.as_matrix()),
        )

    def __mul__(self, multiplicator: "TransformationMatrix") -> "TransformationMatrix":
        """Multiplies two 4x4 matrices of TransformationMatrix instance.

        Args:
            multiplicator: A TransformationMatrix object that represents a 4x4 homogenous transformation matrix

        Returns:
            A TransformationMatrix object that is a result of a multiplication of two TransformationMatrix objects

        Raises:
            Exception: If the matrix is not instance of TransformationMatrix

        """
        if isinstance(multiplicator, TransformationMatrix):
            return TransformationMatrix.from_matrix(
                matrix=np.matmul(self.as_matrix(), multiplicator.as_matrix()),
            )
        raise Exception("Multiplicator must be of instance TransformationMatrix!")
