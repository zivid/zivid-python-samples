from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
import zivid
from matplotlib.path import Path
from nptyping import Float32, Int, NDArray, Shape
from zividsamples.paths import get_data_file_path


@dataclass(frozen=True)
class FOVThresholds:
    center_thresholds = 0.20  # fraction of the image resolution
    edge_threshold = 0.10  # fraction of the image resolution
    checker_size = 30.0  # mm
    edge_margin = 120.0  # mm


@dataclass
class CameraFOV:
    distance: float
    width: float
    height: float

    @classmethod
    def from_model_and_distance(cls, camera_info: zivid.CameraInfo, distance: float) -> "CameraFOV":
        fov_constants = CameraFOVConstants(camera_info)
        z = distance

        # Clip distance z at min and max distance
        if z < fov_constants.minimum_distance:
            z = fov_constants.minimum_distance
        elif z > fov_constants.maximum_distance:
            z = fov_constants.maximum_distance

        return CameraFOV(
            distance=z,
            width=fov_constants.width_at_distance(z),
            height=fov_constants.height_at_distance(z),
        )


class CameraFOVConstants:
    camera_parameters = pd.read_json(get_data_file_path("camera_parameters.json"), orient="index")

    def __init__(self, camera_info: zivid.CameraInfo):
        self.focus: float = self.camera_parameters.loc[camera_info.model_name]["key_a"]  # type: ignore
        self.maximum_distance: float = self.camera_parameters.loc[camera_info.model_name]["key_b"]["distance"]["acceptable"]["max"]  # type: ignore
        self.minimum_distance: float = self.camera_parameters.loc[camera_info.model_name]["key_b"]["distance"]["acceptable"]["min"]  # type: ignore
        self.width_at_distances: list[dict[str, float]] = self.camera_parameters.loc[camera_info.model_name]["key_b"]["width_at_distances"]  # type: ignore
        self.height_at_distances: list[dict[str, float]] = self.camera_parameters.loc[camera_info.model_name]["key_b"]["height_at_distances"]  # type: ignore

    def _find_value_range(self, distance, value_at_distances):
        if distance < value_at_distances[0]["distance"]:
            raise RuntimeError(f"No data available to interpolate at this distance {distance}")
        for value_at_distance_min, value_at_distance_max in zip(
            value_at_distances[:-1], value_at_distances[1:], strict=False
        ):
            if value_at_distance_min["distance"] <= distance <= value_at_distance_max["distance"]:
                return {
                    "value": {
                        "min": value_at_distance_min["value"],
                        "max": value_at_distance_max["value"],
                    },
                    "distance": {
                        "min": value_at_distance_min["distance"],
                        "max": value_at_distance_max["distance"],
                    },
                }
        return {
            "value": {
                "min": value_at_distances[-2]["value"],
                "max": value_at_distances[-1]["value"],
            },
            "distance": {
                "min": value_at_distances[2]["distance"],
                "max": value_at_distances[-1]["distance"],
            },
        }

    def _find_width_range(self, distance):
        return self._find_value_range(
            distance,
            self.width_at_distances,
        )

    def _find_height_range(self, distance):
        return self._find_value_range(
            distance,
            self.height_at_distances,
        )

    def _value_at_distance(self, distance, value_range):
        return (
            (value_range["value"]["max"] - value_range["value"]["min"])
            / (value_range["distance"]["max"] - value_range["distance"]["min"])
        ) * (distance - value_range["distance"]["min"]) + value_range["value"]["min"]

    def width_at_distance(self, distance: float) -> float:
        return self._value_at_distance(distance, self._find_width_range(distance))

    def height_at_distance(self, distance: float) -> float:
        return self._value_at_distance(distance, self._find_height_range(distance))


class LocationInFOV(Enum):
    Center = (0,)
    TopLeft = 1
    TopRight = 2
    BottomLeft = 3
    BottomRight = 4
    Left = 5
    Right = 6
    Top = 7
    Bottom = 8


class DistanceInFOV(Enum):
    Focus = (0,)
    Near = 1
    Far = 2
    VeryNear = 3
    VeryFar = 4


@dataclass
class PointsOfInterest:
    full_fov_corners: NDArray[Shape["4, 3"], Float32]  # type: ignore
    full_fov_corners_with_margin: NDArray[Shape["4, 3"], Float32]  # type: ignore
    center_corners: NDArray[Shape["4, 3"], Float32]  # type: ignore
    left_top_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    left_bottom_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    top_left_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    top_right_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    right_top_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    right_bottom_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    bottom_left_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    bottom_right_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    left_center_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    top_center_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    right_center_line: NDArray[Shape["2, 3"], Float32]  # type: ignore
    bottom_center_line: NDArray[Shape["2, 3"], Float32]  # type: ignore

    def lines_3d(self) -> NDArray[Shape["8, 2, 3"], Float32]:  # type: ignore
        return np.asarray(
            [
                self.left_top_line,
                self.left_bottom_line,
                self.top_left_line,
                self.top_right_line,
                self.right_top_line,
                self.right_bottom_line,
                self.bottom_left_line,
                self.bottom_right_line,
                self.left_center_line,
                self.top_center_line,
                self.right_center_line,
                self.bottom_center_line,
            ],
            dtype=np.float32,
        )


@dataclass
class PointsOfInterest2D:
    full_fov_corners: NDArray[Shape["4, 2"], Int]  # type: ignore
    full_fov_corners_with_margin: NDArray[Shape["4, 2"], Int]  # type: ignore
    center_corners: NDArray[Shape["4, 2"], Int]  # type: ignore
    left_top_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    left_bottom_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    top_left_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    top_right_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    right_top_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    right_bottom_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    bottom_left_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    bottom_right_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    left_center_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    top_center_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    right_center_line: NDArray[Shape["2, 2"], Int]  # type: ignore
    bottom_center_line: NDArray[Shape["2, 2"], Int]  # type: ignore

    def lines_2d(self) -> NDArray[Shape["8, 2, 2"], Int]:  # type: ignore
        return np.asarray(
            [
                self.left_top_line,
                self.left_bottom_line,
                self.top_left_line,
                self.top_right_line,
                self.right_top_line,
                self.right_bottom_line,
                self.bottom_left_line,
                self.bottom_right_line,
                self.left_center_line,
                self.top_center_line,
                self.right_center_line,
                self.bottom_center_line,
            ],
            dtype=np.int32,
        )


@dataclass
class PositionInFOV:
    distance: DistanceInFOV = DistanceInFOV.Focus
    location: LocationInFOV = LocationInFOV.Center
    is_outside: bool = False

    def __str__(self) -> str:
        if self.is_outside:
            return f"{self.distance.name} - {self.location.name} - outside"
        return f"{self.distance.name} - {self.location.name}"

    def point_in_polygon(self, point: tuple[float, float], polygon: np.ndarray) -> bool:
        return Path(polygon).contains_point(point)

    @classmethod
    def from_points_of_interest_and_camera(
        cls, camera_info: zivid.CameraInfo, point_xyz: NDArray[Shape["3"], Float32], points_of_interest: PointsOfInterest  # type: ignore
    ) -> "PositionInFOV":

        def to_2d(points3d):
            return points3d[:, :2]

        def regions(points_of_interest: PointsOfInterest):
            return {
                # Recall, for each line, the first point is the one on the center rectangle
                LocationInFOV.Center: to_2d(points_of_interest.center_corners),
                LocationInFOV.Left: to_2d(
                    np.vstack([points_of_interest.left_top_line, points_of_interest.left_bottom_line[::-1]])
                ),
                LocationInFOV.Right: to_2d(
                    np.vstack([points_of_interest.right_top_line, points_of_interest.right_bottom_line[::-1]])
                ),
                LocationInFOV.Top: to_2d(
                    np.vstack([points_of_interest.top_left_line, points_of_interest.top_right_line[::-1]])
                ),
                LocationInFOV.Bottom: to_2d(
                    np.vstack([points_of_interest.bottom_right_line, points_of_interest.bottom_left_line[::-1]])
                ),
                LocationInFOV.TopLeft: to_2d(
                    np.array(
                        [
                            points_of_interest.full_fov_corners_with_margin[0],
                            points_of_interest.top_left_line[1],
                            points_of_interest.top_left_line[0],
                            points_of_interest.center_corners[0],
                            points_of_interest.left_top_line[0],
                            points_of_interest.left_top_line[1],
                        ]
                    )
                ),
                LocationInFOV.TopRight: to_2d(
                    np.array(
                        [
                            points_of_interest.top_right_line[0],
                            points_of_interest.top_right_line[1],
                            points_of_interest.full_fov_corners_with_margin[1],
                            points_of_interest.right_top_line[1],
                            points_of_interest.right_top_line[0],
                            points_of_interest.center_corners[1],
                        ]
                    )
                ),
                LocationInFOV.BottomRight: to_2d(
                    np.array(
                        [
                            points_of_interest.right_bottom_line[0],
                            points_of_interest.right_bottom_line[1],
                            points_of_interest.full_fov_corners_with_margin[2],
                            points_of_interest.bottom_right_line[1],
                            points_of_interest.bottom_right_line[0],
                            points_of_interest.center_corners[2],
                        ]
                    )
                ),
                LocationInFOV.BottomLeft: to_2d(
                    np.array(
                        [
                            points_of_interest.left_bottom_line[1],
                            points_of_interest.left_bottom_line[0],
                            points_of_interest.center_corners[3],
                            points_of_interest.bottom_left_line[0],
                            points_of_interest.bottom_left_line[1],
                            points_of_interest.full_fov_corners_with_margin[3],
                        ]
                    )
                ),
            }

        def classify_region(
            point_xy: NDArray[Shape["2"], Float32], points_of_interest: PointsOfInterest  # type: ignore
        ) -> tuple[LocationInFOV, bool]:

            # Determine the location in FOV
            regions_inside = regions(points_of_interest)
            for region, polygon in regions_inside.items():
                if Path(polygon).contains_point(tuple(point_xy)):
                    return region, True

            if point_xy[1] < 0.0:  # Top?
                if point_xy[0] < 0.0:  # Left?
                    return LocationInFOV.TopLeft, False
                return LocationInFOV.TopRight, False
            if point_xy[0] < 0.0:  # Left?
                return LocationInFOV.BottomLeft, False
            return LocationInFOV.BottomRight, False

        location, is_inside = classify_region(point_xyz[:2], points_of_interest)
        is_outside = not is_inside

        fov_constants = CameraFOVConstants(camera_info)

        def distance_in_fov(distance_z: float, fov_constants: CameraFOVConstants) -> DistanceInFOV:
            distance_range = fov_constants.maximum_distance - fov_constants.minimum_distance
            abs_distance_from_focus = abs(fov_constants.focus - distance_z)
            focus_threshold = 0.1 * distance_range
            near_threshold = fov_constants.focus - (fov_constants.focus - fov_constants.minimum_distance) * 0.5
            far_threshold = fov_constants.focus + (fov_constants.maximum_distance - fov_constants.focus) * 0.5
            if abs_distance_from_focus < focus_threshold:
                return DistanceInFOV.Focus
            if distance_z < near_threshold:
                return DistanceInFOV.VeryNear
            if distance_z > far_threshold:
                return DistanceInFOV.VeryFar
            if distance_z < fov_constants.focus:
                return DistanceInFOV.Near
            return DistanceInFOV.Far

        return cls(distance=distance_in_fov(point_xyz[2], fov_constants), location=location, is_outside=is_outside)
