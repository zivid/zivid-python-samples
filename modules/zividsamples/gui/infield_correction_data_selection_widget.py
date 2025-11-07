import json
from collections import OrderedDict
from pathlib import Path
from typing import List, Union

import numpy as np
import zivid
from matplotlib import pyplot as plt
from nptyping import Float32, NDArray, Shape
from numpy import uint8 as UInt8
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics, QImage
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from zividsamples.gui.cv2_handler import CV2Handler
from zividsamples.gui.fov import CameraFOV, FOVThresholds, PointsOfInterest, PointsOfInterest2D, PositionInFOV


def _label_width(label: QLabel, numbers: int) -> int:
    font_metrics = QFontMetrics(label.font())
    return (
        font_metrics.width(" -9999.9 ")
        if numbers == 1
        else font_metrics.width(" -9999.9 " + ", -9999.9" * (numbers - 1))
    )


class ButtonWithLabels(QPushButton):
    def __init__(self, labels: List[QLabel], parent=None):
        super().__init__(parent)

        self.labels = labels

        layout = QHBoxLayout(self)
        for label in self.labels:
            text_alignment = Qt.AlignCenter | Qt.AlignVCenter
            label.setMinimumWidth(_label_width(label, 1))
            label.setAlignment(text_alignment)
            layout.addWidget(label)
        combined_width = sum(label.sizeHint().width() for label in self.labels)
        self.setMinimumWidth(combined_width)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


class InfieldCorrectionInputDataCore:
    camera_frame: zivid.Frame
    rgba: NDArray[Shape["N, M, 4"], UInt8]  # type: ignore
    rgba_annotated: NDArray[Shape["N, M, 4"], UInt8]  # type: ignore
    local_trueness: float
    position_in_fov: PositionInFOV
    can_be_used_for_correction: bool

    def __init__(
        self,
        *,
        camera_frame: zivid.Frame,
        rgba: NDArray[Shape["N, M, 4"], UInt8],  # type: ignore
        rgba_annotated: NDArray[Shape["N, M, 4"], UInt8],  # type: ignore
        local_trueness: float = 0.0,
        position_in_fov: PositionInFOV,
        can_be_used_for_correction: bool,
    ):
        self.camera_frame = camera_frame
        self.rgba = rgba
        self.rgba_annotated = rgba_annotated
        self.local_trueness = local_trueness
        self.position_in_fov = position_in_fov
        self.can_be_used_for_correction = can_be_used_for_correction

    def local_trueness_as_string(self) -> str:
        return f"{self.local_trueness * 100:.3f}%"

    def save_data(self, data_path) -> None:
        with open(data_path.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "local_trueness": self.local_trueness,
                    "position_in_fov": self.position_in_fov.as_dict(),
                },
                f,
            )
        self.camera_frame.save(data_path.with_suffix(".zdf"))
        qimage = QImage(self.rgba.data, self.rgba.shape[1], self.rgba.shape[0], QImage.Format_RGBA8888)
        qimage.save(str(data_path.with_suffix(".png")))
        qimage_annotated = QImage(
            self.rgba_annotated.data, self.rgba_annotated.shape[1], self.rgba_annotated.shape[0], QImage.Format_RGBA8888
        )
        qimage_annotated.save(str(data_path.with_suffix(".png")).replace(".png", "_annotated.png"))

    @classmethod
    def from_path(cls, data_path: Path, cv2_handler: CV2Handler) -> "InfieldCorrectionInputDataCore":
        with open(data_path.with_suffix(".json"), "r", encoding="utf-8") as f:
            data_dict = json.load(f)
            try:
                camera_frame = zivid.Frame(data_path.with_suffix(".zdf"))
            except Exception as ex:
                raise RuntimeError(f"Failed to load ZDF file from {data_path.with_suffix('.zdf')}: {ex}") from ex
            try:
                rgba = cv2_handler.cv2.cvtColor(
                    cv2_handler.cv2.imread(str(data_path.with_suffix(".png")), cv2_handler.cv2.IMREAD_UNCHANGED),
                    cv2_handler.cv2.COLOR_BGRA2RGBA,
                )
            except Exception as ex:
                raise RuntimeError(f"Failed to load RGBA image from {data_path.with_suffix('.png')}: {ex}") from ex
            try:
                rgba_annotated = cv2_handler.cv2.cvtColor(
                    cv2_handler.cv2.imread(
                        str(data_path.with_suffix(".png")).replace(".png", "_annotated.png"),
                        cv2_handler.cv2.IMREAD_UNCHANGED,
                    ),
                    cv2_handler.cv2.COLOR_BGRA2RGBA,
                )
            except Exception as ex:
                raise RuntimeError(
                    f"Failed to load annotated RGBA image from {str(data_path.with_suffix('.png')).replace('.png', '_annotated.png')}: {ex}"
                ) from ex
            return cls(
                camera_frame=camera_frame,
                rgba=rgba,
                rgba_annotated=rgba_annotated,
                local_trueness=data_dict["local_trueness"],
                position_in_fov=PositionInFOV.from_dict(data_dict["position_in_fov"]),
                can_be_used_for_correction=False,
            )


class InfieldCorrectionInputData(InfieldCorrectionInputDataCore):
    projector_image: NDArray[Shape["N, M, 4"], UInt8]  # type: ignore

    def __init__(
        self,
        *,
        camera: zivid.Camera,
        camera_frame: zivid.Frame,
        rgba: NDArray[Shape["N, M, 4"], UInt8],  # type: ignore
        infield_input: zivid.calibration.InfieldCorrectionInput,
        intrinsics: zivid.CameraIntrinsics,
    ):
        # TODO: Refactor so that we can call super().__init__()  # pylint: disable=super-init-not-called
        self.cv2_handler = CV2Handler()
        self.camera_frame = camera_frame
        self.intrinsics = intrinsics
        self.infield_input = infield_input
        self.can_be_used_for_correction = True
        camera_verification = zivid.calibration.verify_camera(self.infield_input)
        self.fov = CameraFOV.from_model_and_distance(
            camera_info=self.camera_frame.camera_info, distance=camera_verification.position()[2]
        )
        self.local_trueness = camera_verification.local_dimension_trueness()
        self.rgba = rgba.copy()

        self.fov_points_of_interest = self.fov_points_of_interest_3d(camera)
        self.position_in_fov = PositionInFOV.from_points_of_interest_and_camera(
            camera.info, camera_verification.position(), self.fov_points_of_interest
        )

        self.rgba_annotated = rgba.copy()
        rgb = rgba[:, :, :3].copy().astype(np.uint8)
        self.cv2_handler.draw_fov_division_from_3d(rgb, self.fov_points_of_interest, self.intrinsics)
        self.cv2_handler.draw_3d_points_in_2d(
            intrinsics,
            rgb,
            [camera_verification.position()],
            circle_color=(0, 0, 255, 255),
        )
        projector_resolution = zivid.projection.projector_resolution(camera)
        self.projector_height = projector_resolution[0]
        self.projector_width = projector_resolution[1]
        background_color = (0, 0, 0, 255)
        self.projector_image = np.full(
            (self.projector_height, self.projector_width, len(background_color)), background_color, dtype=np.uint8
        )
        self.cv2_handler.draw_fov_division(
            self.projector_image, self.points_of_interest_in_projector_2d_from_3d(camera), use_bgr=True
        )
        self.rgba_annotated[:, :, :3] = rgb

    def points_of_interest_in_projector_2d_from_3d(self, camera: zivid.Camera) -> PointsOfInterest2D:
        full_fov_corners_2d = np.asarray(
            zivid.projection.pixels_from_3d_points(camera, self.fov_points_of_interest.full_fov_corners * [1, 0.99, 1])
        )
        full_fov_corners_2d_with_margin = np.asarray(
            zivid.projection.pixels_from_3d_points(camera, self.fov_points_of_interest.full_fov_corners_with_margin)
        )
        center_points_2d = np.asarray(
            zivid.projection.pixels_from_3d_points(camera, self.fov_points_of_interest.center_corners)
        )
        line_points_2d = np.asarray(
            zivid.projection.pixels_from_3d_points(camera, self.fov_points_of_interest.lines_3d().reshape(-1, 3))
        )
        lines_2d = line_points_2d.reshape(-1, 2, 2).astype(int)
        return PointsOfInterest2D(
            full_fov_corners=np.array(full_fov_corners_2d, dtype=np.int32),
            full_fov_corners_with_margin=np.array(full_fov_corners_2d_with_margin, dtype=np.int32),
            center_corners=np.array(center_points_2d, dtype=np.int32),
            left_top_line=lines_2d[0],
            left_bottom_line=lines_2d[1],
            top_left_line=lines_2d[2],
            top_right_line=lines_2d[3],
            right_top_line=lines_2d[4],
            right_bottom_line=lines_2d[5],
            bottom_left_line=lines_2d[6],
            bottom_right_line=lines_2d[7],
            left_center_line=lines_2d[8],
            top_center_line=lines_2d[9],
            right_center_line=lines_2d[10],
            bottom_center_line=lines_2d[11],
        )

    def fov_points_of_interest_3d(self, camera: zivid.Camera) -> PointsOfInterest:
        vertical_margin_for_center = int(FOVThresholds.center_thresholds * (self.fov.height / 2))
        horizontal_margin_for_center = int(FOVThresholds.center_thresholds * (self.fov.width / 2))
        center_corners_in_3d = np.array(
            [
                [
                    -horizontal_margin_for_center,
                    -vertical_margin_for_center,
                    self.fov.distance,
                ],
                [
                    horizontal_margin_for_center,
                    -vertical_margin_for_center,
                    self.fov.distance,
                ],
                [
                    horizontal_margin_for_center,
                    vertical_margin_for_center,
                    self.fov.distance,
                ],
                [
                    -horizontal_margin_for_center,
                    vertical_margin_for_center,
                    self.fov.distance,
                ],
            ]
        )

        estimated_full_fov_corners_in_3d = np.array(
            [
                [
                    -self.fov.width / 2,
                    -self.fov.height / 2,
                    self.fov.distance,
                ],
                [
                    self.fov.width / 2,
                    -self.fov.height / 2,
                    self.fov.distance,
                ],
                [
                    self.fov.width / 2,
                    self.fov.height / 2,
                    self.fov.distance,
                ],
                [
                    -self.fov.width / 2,
                    self.fov.height / 2,
                    self.fov.distance,
                ],
            ]
        )
        fov_multiplier = 1.4
        excessive_full_fov_corners_in_3d = estimated_full_fov_corners_in_3d * [fov_multiplier, fov_multiplier, 1]
        # Shift all points in negative x by 10% of the width
        shift_percentage = 0.1
        shift_value = self.fov.width * shift_percentage
        excessive_full_fov_corners_in_3d[:, 0] -= shift_value
        excessive_full_fov_points_3d = self.generate_full_fov_mesh(excessive_full_fov_corners_in_3d)

        camera_fov_points_in_2d = self.cv2_handler.project_points(
            excessive_full_fov_points_3d.reshape(-1, 3), self.intrinsics
        )
        camera_fov_points_in_2d = camera_fov_points_in_2d.reshape(*excessive_full_fov_points_3d.shape[:2], 2).astype(
            np.float32
        )
        camera_resolution = np.array([self.rgba.shape[1], self.rgba.shape[0]])

        valid_mask_camera = self.valid_mask(camera_fov_points_in_2d, camera_resolution)
        camera_fov_corner_indices_in_3d = self.calculate_trapezoidal_corners(valid_mask_camera)
        camera_fov_corners_in_3d = np.array(
            [excessive_full_fov_points_3d[y, x] for x, y in camera_fov_corner_indices_in_3d]
        )

        projector_fov_points_in_2d = np.asarray(
            zivid.projection.pixels_from_3d_points(camera, excessive_full_fov_points_3d.reshape(-1, 3))
        )
        projector_fov_points_in_2d = projector_fov_points_in_2d.reshape(
            *excessive_full_fov_points_3d.shape[:2], 2
        ).astype(np.float32)
        projector_resolution = np.array(zivid.projection.projector_resolution(camera))[::-1]

        valid_mask_projector = self.valid_mask(projector_fov_points_in_2d, projector_resolution)
        projector_fov_corner_indices_in_3d = self.calculate_trapezoidal_corners(valid_mask_projector)
        projector_fov_corners_in_3d = np.array(
            [excessive_full_fov_points_3d[y, x] for x, y in projector_fov_corner_indices_in_3d]
        )

        full_fov_corners_in_3d = np.zeros((4, 3), dtype=np.float32)
        for i in range(4):
            sign = np.sign(center_corners_in_3d[i])
            full_fov_corners_in_3d[i] = (
                np.min([np.abs(camera_fov_corners_in_3d[i]), np.abs(projector_fov_corners_in_3d[i])], axis=0) * sign
            )

        # Calculate a smaller trapezoid by reducing each side by FOVThresholds.checker_size, only for X and Y
        full_fov_corners_in_3d_with_margin = full_fov_corners_in_3d.copy()
        center = np.array([0, 0, self.fov.distance])

        for index, _ in enumerate(full_fov_corners_in_3d_with_margin):
            direction = np.sign(full_fov_corners_in_3d[index] - center)
            full_fov_corners_in_3d_with_margin[index] = (
                full_fov_corners_in_3d[index] - FOVThresholds.edge_margin * direction
            )

        full_fov_width_top = full_fov_corners_in_3d_with_margin[1][0] - full_fov_corners_in_3d_with_margin[0][0]
        full_fov_width_bottom = full_fov_corners_in_3d_with_margin[2][0] - full_fov_corners_in_3d_with_margin[3][0]
        full_fov_height_left = full_fov_corners_in_3d_with_margin[3][1] - full_fov_corners_in_3d_with_margin[0][1]
        full_fov_height_right = full_fov_corners_in_3d_with_margin[2][1] - full_fov_corners_in_3d_with_margin[1][1]
        vertical_margin_left = int(FOVThresholds.edge_threshold * (full_fov_height_left / 2))
        vertical_margin_right = int(FOVThresholds.edge_threshold * (full_fov_height_right / 2))
        horizontal_margin_top = int(FOVThresholds.edge_threshold * (full_fov_width_top / 2))
        horizontal_margin_bottom = int(FOVThresholds.edge_threshold * (full_fov_width_bottom / 2))

        left_top_line = [
            [-horizontal_margin_for_center, -vertical_margin_left, self.fov.distance],
            [full_fov_corners_in_3d_with_margin[0][0], -vertical_margin_left, self.fov.distance],
        ]
        left_bottom_line = [
            [-horizontal_margin_for_center, vertical_margin_left, self.fov.distance],
            [full_fov_corners_in_3d_with_margin[3][0], vertical_margin_left, self.fov.distance],
        ]
        top_line_top = np.mean([full_fov_corners_in_3d_with_margin[0][1], full_fov_corners_in_3d_with_margin[1][1]])
        top_left_line = [
            [-horizontal_margin_top, -vertical_margin_for_center, self.fov.distance],
            [-horizontal_margin_top, top_line_top, self.fov.distance],
        ]
        top_right_line = [
            [horizontal_margin_top, -vertical_margin_for_center, self.fov.distance],
            [horizontal_margin_top, top_line_top, self.fov.distance],
        ]
        right_top_line = [
            [horizontal_margin_for_center, -vertical_margin_right, self.fov.distance],
            [full_fov_corners_in_3d_with_margin[1][0], -vertical_margin_right, self.fov.distance],
        ]
        right_bottom_line = [
            [horizontal_margin_for_center, vertical_margin_right, self.fov.distance],
            [full_fov_corners_in_3d_with_margin[2][0], vertical_margin_right, self.fov.distance],
        ]
        bottom_line_bottom = np.mean(
            [full_fov_corners_in_3d_with_margin[3][1], full_fov_corners_in_3d_with_margin[2][1]]
        )
        bottom_left_line = [
            [-horizontal_margin_bottom, vertical_margin_for_center, self.fov.distance],
            [-horizontal_margin_bottom, bottom_line_bottom, self.fov.distance],
        ]
        bottom_right_line = [
            [horizontal_margin_bottom, vertical_margin_for_center, self.fov.distance],
            [horizontal_margin_bottom, bottom_line_bottom, self.fov.distance],
        ]
        left_center_line = [
            [-horizontal_margin_for_center, 0, self.fov.distance],
            [full_fov_corners_in_3d_with_margin[0][0], 0, self.fov.distance],
        ]
        top_center_line = [
            [0, -vertical_margin_for_center, self.fov.distance],
            [0, top_line_top, self.fov.distance],
        ]
        right_center_line = [
            [horizontal_margin_for_center, 0, self.fov.distance],
            [full_fov_corners_in_3d_with_margin[1][0], 0, self.fov.distance],
        ]
        bottom_center_line = [
            [0, vertical_margin_for_center, self.fov.distance],
            [0, bottom_line_bottom, self.fov.distance],
        ]
        return PointsOfInterest(
            full_fov_corners=full_fov_corners_in_3d,
            full_fov_corners_with_margin=full_fov_corners_in_3d_with_margin,
            center_corners=center_corners_in_3d,
            left_top_line=np.array(left_top_line),
            left_bottom_line=np.array(left_bottom_line),
            top_left_line=np.array(top_left_line),
            top_right_line=np.array(top_right_line),
            right_top_line=np.array(right_top_line),
            right_bottom_line=np.array(right_bottom_line),
            bottom_left_line=np.array(bottom_left_line),
            bottom_right_line=np.array(bottom_right_line),
            left_center_line=np.array(left_center_line),
            top_center_line=np.array(top_center_line),
            right_center_line=np.array(right_center_line),
            bottom_center_line=np.array(bottom_center_line),
        )

    def valid_masks(self, points_in_2d, resolution):
        non_nan_mask = ~np.isnan(points_in_2d).any(axis=2)
        points_in_2d[np.isnan(points_in_2d)] = -1
        resolution_mask_camera = np.logical_and(
            points_in_2d[:, :, 0] >= 0,
            points_in_2d[:, :, 0] < resolution[0],
        )
        resolution_mask_camera = np.logical_and(
            resolution_mask_camera,
            np.logical_and(
                points_in_2d[:, :, 1] >= 0,
                points_in_2d[:, :, 1] < resolution[1],
            ),
        )
        return non_nan_mask, resolution_mask_camera

    def valid_mask(self, points_in_2d, resolution):
        non_nan_mask, resolution_mask_camera = self.valid_masks(points_in_2d, resolution)
        return np.logical_and(non_nan_mask, resolution_mask_camera)

    def visualize_masks(self, points_in_2d, resolution, reference_frame="Camera"):
        non_nan_mask, resolution_mask_camera = self.valid_masks(points_in_2d, resolution)
        image = np.zeros(non_nan_mask.shape, dtype=np.uint8)
        image[~non_nan_mask] = 50
        image[~resolution_mask_camera] += 150
        # Visualize valid_mask_camera with matplotlib.pyplot
        if not hasattr(self.__class__, f"_figure_{reference_frame}"):
            setattr(self.__class__, f"_figure_{reference_frame}", plt.figure())
        plt.figure(getattr(self.__class__, f"_figure_{reference_frame}").number)
        plt.imshow(image, cmap="gray")
        plt.title(f"Valid Mask for {reference_frame}")
        plt.colorbar(label="Valid Points")
        plt.xlabel("Width")
        plt.ylabel("Height")
        plt.show()

    def generate_full_fov_mesh(self, corners: NDArray[Shape["4, 3"], Float32]) -> NDArray[Shape["N, 3"], Float32]:  # type: ignore
        # Define the two vectors spanning the rectangle
        vector_x = corners[1] - corners[0]  # From corner 0 to corner 1
        vector_y = corners[3] - corners[0]  # From corner 0 to corner 3

        distance_between_points_in_mm = 2

        width_in_mm = np.linalg.norm(vector_x)
        height_in_mm = np.linalg.norm(vector_y)
        num_points_x = int(width_in_mm / distance_between_points_in_mm)
        num_points_y = int(height_in_mm / distance_between_points_in_mm)

        # Generate evenly spaced points in 2D (parameter space)
        u = np.linspace(0, 1, num_points_x)
        v = np.linspace(0, 1, num_points_y)
        uu, vv = np.meshgrid(u, v)

        # Compute the 3D points using matrix operations
        full_fov_points_3d = corners[0] + np.outer(uu.ravel(), vector_x) + np.outer(vv.ravel(), vector_y)
        return full_fov_points_3d.reshape([uu.shape[0], uu.shape[1], 3])

    def calculate_trapezoidal_corners(self, valid_mask):
        valid_mask_cv = valid_mask.astype(np.uint8)
        contours, _ = self.cv2_handler.cv2.findContours(
            valid_mask_cv, self.cv2_handler.cv2.RETR_EXTERNAL, self.cv2_handler.cv2.CHAIN_APPROX_SIMPLE
        )
        contour = max(contours, key=self.cv2_handler.cv2.contourArea)

        # Approximate to quadrilateral using Ramer–Douglas–Peucker algorithm
        epsilon = 0.01 * self.cv2_handler.cv2.arcLength(contour, True)
        approx = self.cv2_handler.cv2.approxPolyDP(contour, epsilon, True)

        # Optionally, increase epsilon until we get exactly 4 points
        while len(approx) > 4:
            epsilon *= 1.1
            approx = self.cv2_handler.cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) != 4:
            raise RuntimeError(f"Failed to find a quadrilateral, found {len(approx)} points")

        full_fov_corner_pixel_coordinates = approx.reshape(-1, 2)

        if self.cv2_handler.cv2.contourArea(approx) > 0:  # Positive area means counter-clockwise
            full_fov_corner_pixel_coordinates[[1, 3]] = full_fov_corner_pixel_coordinates[[3, 1]]

        # Rotate the corners so the first is top-left (min row, then col)
        top_left_idx = np.lexsort((full_fov_corner_pixel_coordinates[:, 0], full_fov_corner_pixel_coordinates[:, 1]))[0]
        return np.roll(full_fov_corner_pixel_coordinates, -top_left_idx, axis=0)


class InfieldCorrectionInputWidget(QWidget):
    infield_correction_input_data: Union[InfieldCorrectionInputData, InfieldCorrectionInputDataCore]

    def __init__(
        self,
        poseID: int,
        directory: Path,
        infield_correction_input_data: Union[InfieldCorrectionInputData, InfieldCorrectionInputDataCore],
        parent=None,
    ):
        super().__init__(parent)

        self.poseID = poseID
        self.directory = directory
        self.camera_frame_path: Path = self.directory / f"infield_calibration_input_{self.poseID}.zdf"
        self.camera_image_path: Path = self.directory / f"infield_calibration_input_{self.poseID}.png"

        self.selected_checkbox = QCheckBox(f"{self.poseID:>2}")
        self.selected_checkbox.setLayoutDirection(Qt.RightToLeft)
        self.selected_checkbox.setChecked(infield_correction_input_data.can_be_used_for_correction)
        self.selected_checkbox.setCheckable(infield_correction_input_data.can_be_used_for_correction)
        self.position_in_fov_label = QLabel()
        self.trueness_label = QLabel()
        self.clickable_labels = ButtonWithLabels(
            [
                self.position_in_fov_label,
                self.trueness_label,
            ]
        )
        self.clickable_labels.setCheckable(True)
        self.clickable_labels.setChecked(False)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        pose_pair_layout = QHBoxLayout()
        pose_pair_layout.addWidget(self.selected_checkbox)
        pose_pair_layout.addWidget(self.clickable_labels)
        self.setLayout(pose_pair_layout)

        self.update_information(infield_correction_input_data)

    def update_information(
        self, infield_correction_input_data: Union[InfieldCorrectionInputData, InfieldCorrectionInputDataCore]
    ):
        self.infield_correction_input_data = infield_correction_input_data
        self.infield_correction_input_data.save_data(self.directory / f"infield_calibration_input_{self.poseID}")
        self.update_gui()

    def update_gui(self):
        self.position_in_fov_label.setText(str(self.infield_correction_input_data.position_in_fov))
        self.trueness_label.setText(self.infield_correction_input_data.local_trueness_as_string())


class InfieldCorrectionDataSelectionWidget(QWidget):
    data_directory: Path
    infield_input_data_clicked = pyqtSignal(InfieldCorrectionInputDataCore)
    infield_input_data_updated = pyqtSignal(int)

    def __init__(self, directory: Path, parent=None):
        super().__init__(parent)

        self.cv2_handler = CV2Handler()
        self.data_directory = directory
        self.infield_input_data_widgets: OrderedDict[int, InfieldCorrectionInputWidget] = OrderedDict()

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

    def create_widgets(self):
        self.infield_input_container = QWidget()

        self.infield_input_group_box = QGroupBox("Infield Correction Input Data")
        self.infield_input_scrollable_area = QScrollArea()
        self.infield_input_scrollable_area.setWidgetResizable(True)
        self.infield_input_scrollable_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.infield_input_scrollable_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.infield_input_scrollable_area.setWidget(self.infield_input_container)

        self.remove_last_infield_input_button = QPushButton("Remove Last")
        self.remove_last_infield_input_button.setEnabled(False)
        self.clear_infield_input_button = QPushButton("Clear")

    def setup_layout(self):
        self.infield_input_group_box_layout = QVBoxLayout()
        self.infield_input_group_box_layout.setAlignment(Qt.AlignTop)
        self.infield_input_group_box.setLayout(self.infield_input_group_box_layout)

        self.infield_input_layout = QVBoxLayout(self.infield_input_container)
        self.infield_input_layout.setAlignment(Qt.AlignTop)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.remove_last_infield_input_button)
        button_layout.addWidget(self.clear_infield_input_button)

        self.infield_input_group_box_layout.addLayout(self.create_title_row())
        self.infield_input_group_box_layout.addWidget(self.infield_input_scrollable_area)
        self.infield_input_group_box_layout.addLayout(button_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.infield_input_group_box)
        self.setLayout(layout)

    def connect_signals(self):
        self.clear_infield_input_button.clicked.connect(self.on_clear_button_clicked)
        self.remove_last_infield_input_button.clicked.connect(self.on_remove_last_infield_input_button_clicked)

    def update_data_directory(self, data_directory: Path):
        existing_files = list(data_directory.glob("infield_calibration_input_*.json"))
        warning_text = (
            """\
You are about to load old data. This will remove all current Infield Correction Input Data.
Do you want to proceed?
Note that while it is possible to review the infield session, it is not possible to
recalculate and apply infield correction from a previous session."""
            if existing_files
            else f"""\
This will remove all current Infield Correction Input Data.
Do you want to proceed?
Your current data is kept in {self.data_directory}."""
        )
        if len(self.infield_input_data_widgets) > 0:
            reply = QMessageBox.question(
                self,
                "Clear All Infield Input Data",
                warning_text,
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.clear_gui()
        self.data_directory = data_directory
        if len(existing_files) > 0:
            self.load_existing_data(existing_files)

    def load_existing_data(self, existing_files: List[Path]):
        self.infield_input_group_box.setStyleSheet(r"QGroupBox {border: 2px solid yellow;}")
        self.infield_input_group_box.setTitle("Infield Correction Input Data (loading...)")
        self.setVisible(True)
        QApplication.processEvents()
        for file in sorted(existing_files):
            try:
                infield_input_data = InfieldCorrectionInputDataCore.from_path(file, self.cv2_handler)
                self.add_infield_input_data(infield_input_data)
            except Exception as e:
                print(f"Failed to load: {e}")
            QApplication.processEvents()
        self.infield_input_group_box.setStyleSheet("")
        self.infield_input_group_box.setTitle("Infield Correction Input Data")

    def on_infield_input_data_widget_selection_box_clicked(self):
        self.infield_input_data_updated.emit(self.can_calculate_correction())

    def on_infield_input_data_widget_clicked(self, infield_correction_input_widget: InfieldCorrectionInputWidget):
        for clickable_area in [p.clickable_labels for p in self.infield_input_data_widgets.values()]:
            if clickable_area is not infield_correction_input_widget.clickable_labels:
                clickable_area.setChecked(False)
                QApplication.processEvents()
        self.infield_input_data_clicked.emit(infield_correction_input_widget.infield_correction_input_data)

    def on_remove_last_infield_input_button_clicked(self):
        if self.infield_input_data_widgets:
            _, widget_to_remove = self.infield_input_data_widgets.popitem()
            self.infield_input_layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()
            QApplication.processEvents()
            self.infield_input_data_updated.emit(self.can_calculate_correction())

    def on_clear_button_clicked(self):
        self.clear_all()

    def create_title_row(self) -> QHBoxLayout:
        checkbox_and_poseID_spacer = QSpacerItem(75, 40, QSizePolicy.Fixed, QSizePolicy.Minimum)
        remove_button_spacer = QSpacerItem(45, 40, QSizePolicy.Fixed, QSizePolicy.Minimum)
        title_labels = ButtonWithLabels([QLabel("Position in FOV"), QLabel("Local Trueness")])
        title_layout = QHBoxLayout()
        title_layout.addItem(checkbox_and_poseID_spacer)
        title_layout.addWidget(title_labels)
        title_layout.addItem(remove_button_spacer)
        return title_layout

    def show_as_busy(self, active: bool):
        self.setVisible(active or len(self.infield_input_data_widgets) > 0)
        self.infield_input_group_box.setStyleSheet(r"QGroupBox {border: 2px solid yellow;}" if active else "")
        self.infield_input_group_box.setTitle(
            "Infield Correction Input Data (processing...)" if active else "Infield Correction Input Data"
        )
        QApplication.processEvents()

    def add_infield_input_data(
        self, infield_input_data: Union[InfieldCorrectionInputData, InfieldCorrectionInputDataCore]
    ) -> None:
        poseID = self.get_current_poseID()
        if poseID in self.infield_input_data_widgets:
            reply = QMessageBox.question(
                self,
                "Replace Infield Input Data",
                "This will replace the selected Infield Input Data. Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.infield_input_data_widgets[poseID].update_information(infield_input_data)
            return

        infield_correction_input_widget = InfieldCorrectionInputWidget(
            poseID=poseID, directory=self.data_directory, infield_correction_input_data=infield_input_data
        )
        infield_correction_input_widget.clickable_labels.clicked.connect(
            lambda: self.on_infield_input_data_widget_clicked(infield_correction_input_widget)
        )
        infield_correction_input_widget.selected_checkbox.stateChanged.connect(
            self.on_infield_input_data_widget_selection_box_clicked
        )

        self.infield_input_layout.insertWidget(infield_correction_input_widget.poseID, infield_correction_input_widget)
        self.infield_input_data_widgets[poseID] = infield_correction_input_widget
        self.infield_input_data_updated.emit(self.can_calculate_correction())
        self.remove_last_infield_input_button.setEnabled(True)

    def get_current_poseID(self) -> int:
        for infield_correction_input_widget in self.infield_input_data_widgets.values():
            if infield_correction_input_widget.clickable_labels.isChecked():
                return infield_correction_input_widget.poseID
        return len(self.infield_input_data_widgets)

    def number_of_active_infield_input_data(self) -> int:
        return len(
            [
                infield_correction_input_widget
                for infield_correction_input_widget in self.infield_input_data_widgets.values()
                if infield_correction_input_widget.selected_checkbox.isChecked()
            ]
        )

    def can_calculate_correction(self) -> bool:
        return (
            len(
                [
                    infield_correction_input_widget
                    for infield_correction_input_widget in self.infield_input_data_widgets.values()
                    if infield_correction_input_widget.selected_checkbox.isChecked()
                    and infield_correction_input_widget.infield_correction_input_data.can_be_used_for_correction
                ]
            )
            > 0
        )

    def get_correction_results(self) -> List[zivid.calibration.InfieldCorrectionInput]:
        return [
            infield_correction_input_widget.infield_correction_input_data.infield_input
            for infield_correction_input_widget in self.infield_input_data_widgets.values()
            if infield_correction_input_widget.selected_checkbox.isChecked()
            and isinstance(infield_correction_input_widget.infield_correction_input_data, InfieldCorrectionInputData)
            and infield_correction_input_widget.infield_correction_input_data.can_be_used_for_correction
        ]

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            sublayout = item.layout()
            if sublayout:
                self._clear_layout(sublayout)

    def clear_gui(self):
        self._clear_layout(self.infield_input_layout)
        self.infield_input_data_widgets.clear()
        self.infield_input_data_updated.emit(self.can_calculate_correction())
        self.remove_last_infield_input_button.setEnabled(False)
        self.setVisible(False)

    def clear_all(self):
        self.clear_gui()
        if self.infield_input_data_widgets:
            reply = QMessageBox.question(
                self,
                "Clear All Infield Input Data",
                "This will remove all loaded Infield Correction Input Data. Do you want to proceed?"
                "Note that while it is possible to review the infield session, it is not possible to"
                "recalculate and apply infield correction from a previous session.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.clear_gui()
