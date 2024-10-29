"""
Convenience functions and a class for 4x4 transformation matrices.

"""

from dataclasses import dataclass, field

import numpy as np
from nptyping import Float32, NDArray, Shape
from scipy.spatial.transform import Rotation


@dataclass
class Distance:
    translation: float
    rotation: float


@dataclass
class TransformationMatrix:
    rotation: Rotation = Rotation.from_matrix(np.identity(3))
    translation: NDArray[Shape["3"], Float32] = field(  # type: ignore
        default_factory=lambda: np.array([0, 0, 0], np.float32)
    )

    def as_matrix(self) -> NDArray[Shape["4, 4"], Float32]:  # type: ignore
        matrix = np.identity(4, np.float32)
        matrix[:3, :3] = self.rotation.as_matrix().astype(np.float32)
        matrix[:3, 3] = self.translation
        return matrix

    @staticmethod
    def from_matrix(matrix: NDArray[Shape["4, 4"], Float32]) -> "TransformationMatrix":  # type: ignore
        return TransformationMatrix(rotation=Rotation.from_matrix(matrix[:3, :3]), translation=matrix[:3, 3])

    def inv(self) -> "TransformationMatrix":
        return TransformationMatrix.from_matrix(np.linalg.inv(self.as_matrix()))

    def __mul__(self, other: "TransformationMatrix") -> "TransformationMatrix":
        if isinstance(other, TransformationMatrix):
            return TransformationMatrix.from_matrix(self.as_matrix() @ other.as_matrix())
        raise NotImplementedError(other)

    def rotate(
        self, points: NDArray[Shape["N, M, 3"], Float32]  # type: ignore
    ) -> NDArray[Shape["N, M, 3"], Float32]:  # type: ignore
        return points.dot(self.rotation.as_matrix().astype(np.float32).T)

    def transform(
        self, points: NDArray[Shape["N, M, 3"], Float32]  # type: ignore
    ) -> NDArray[Shape["N, M, 3"], Float32]:  # type: ignore
        return self.rotate(points=points) + self.translation.reshape((1, 1, 3))

    def distance_to(self, other: "TransformationMatrix") -> Distance:
        translation_diff = self.translation - other.translation
        rotation_diff = self.rotation.as_matrix() - other.rotation.as_matrix()
        translation_distance = np.linalg.norm(translation_diff)
        rotation_distance = np.linalg.norm(rotation_diff)
        return Distance(
            translation=float(translation_distance),
            rotation=float(rotation_distance),
        )

    def is_identity(self) -> bool:
        identity = np.identity(4)
        if np.all(np.isclose(self.as_matrix(), identity)):
            return True
        return False
