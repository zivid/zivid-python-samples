import re
from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import zivid
from PyQt5.QtCore import QSignalBlocker, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit, QMessageBox, QScrollArea, QVBoxLayout, QWidget
from scipy.spatial.transform import Rotation
from zividsamples.gui.aspect_ratio_label import AspectRatioLabel
from zividsamples.gui.qt_application import create_horizontal_line, create_vertical_line
from zividsamples.gui.rotation_format_configuration import (
    RotationFormats,
    RotationFormatSelectionWidget,
    RotationInformation,
)
from zividsamples.paths import get_image_file_path
from zividsamples.transformation_matrix import TransformationMatrix


def wrap_path(path: Path, wrap_length: int) -> str:
    parts = path.parts  # Get parts of the Path
    wrapped_lines = []
    current_line = parts[0]
    divider = "/" if current_line.endswith(":") else "\\"
    for part in parts[1:]:
        if len(f"{current_line}{divider}{part}") > wrap_length:
            wrapped_lines.append(f"{current_line}{divider}")
            current_line = part
        else:
            current_line = f"{current_line}{divider}{part}"
    wrapped_lines.append(current_line)
    return "\n".join(wrapped_lines)


class PoseWidgetDisplayMode(Enum):
    OnlyPose = 0
    Basic = 1
    Advanced = 2


class BasePoseWidget(QWidget):
    transformation_matrix: TransformationMatrix = TransformationMatrix()
    descriptive_image_eye_in_hand: Optional[QPixmap] = None
    descriptive_image_eye_to_hand: Optional[QPixmap] = None
    pose_updated = pyqtSignal()
    rotation_information: RotationInformation

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        title: str,
        initial_rotation_information: RotationInformation,
        eye_in_hand: bool,
        display_mode: PoseWidgetDisplayMode,
        descriptive_image_paths: Optional[Tuple[Path, Path]] = None,
        read_only: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.title = title
        self.eye_in_hand = eye_in_hand
        self.rotation_information = initial_rotation_information
        self.display_mode = display_mode
        self.read_only = read_only

        if descriptive_image_paths is not None:
            self.descriptive_image_eye_in_hand = QPixmap(descriptive_image_paths[0].as_posix())
            self.descriptive_image_eye_to_hand = QPixmap(descriptive_image_paths[1].as_posix())

        if initial_rotation_information.format not in RotationFormats.as_list():
            raise ValueError(f"Invalid variant: {initial_rotation_information.format}")
        # self.variant = initial_rotation_information.variant
        if self.rotation_information.euler_variant:
            # self.euler_variant = self.rotation_format.euler_variant
            self.extrinsic_euler = self.rotation_information.euler_variant.islower()
        else:
            self.rotation_information.euler_variant = "XYZ"
            self.extrinsic_euler = False
        # self.rotation_format.use_degrees = initial_rotation_information.use_degrees

        self.setup_base_widgets(title, descriptive_image_paths)
        self.setup_base_layout()
        self.setup_base_connections()

    def setup_base_widgets(self, title, descriptive_image_paths: Optional[Tuple[Path, Path]]):
        if self.display_mode != PoseWidgetDisplayMode.OnlyPose:
            self.rotation_format_selection_widget = RotationFormatSelectionWidget(self.rotation_information)

        if descriptive_image_paths is not None:
            descriptive_image = (
                self.descriptive_image_eye_in_hand if self.eye_in_hand else self.descriptive_image_eye_to_hand
            )
            self.descriptive_image_label = AspectRatioLabel(title, descriptive_image)
        else:
            self.descriptive_image_label = None

    def setup_base_layout(self):
        if self.display_mode == PoseWidgetDisplayMode.OnlyPose:
            self.grid_layout = QGridLayout()
        else:
            self.grid_layout = self.rotation_format_selection_widget.grid_layout

    def setup_base_connections(self):
        if self.display_mode != PoseWidgetDisplayMode.OnlyPose:
            self.rotation_format_selection_widget.rotation_format_update.connect(self.on_rotation_format_update)

    def get_rotation_format(self) -> RotationInformation:
        return self.rotation_information

    def set_rotation_format(self, rotation_format: RotationInformation):
        self.rotation_information = rotation_format
        if self.display_mode != PoseWidgetDisplayMode.OnlyPose:
            self.rotation_format_selection_widget.set_rotation_format(rotation_format)
        self.update_from_transformation_matrix()

    def on_eye_in_hand_toggled(self, eye_in_hand: bool):
        descriptive_image = self.descriptive_image_eye_in_hand if eye_in_hand else self.descriptive_image_eye_to_hand
        if descriptive_image is not None and self.descriptive_image_label is not None:
            self.descriptive_image_label.set_original_pixmap(descriptive_image)

    def get_transformation_matrix(self):
        return self.transformation_matrix

    def set_transformation_matrix(self, transformation_matrix: TransformationMatrix):
        self.transformation_matrix = transformation_matrix
        self.update_from_transformation_matrix()

    def on_rotation_format_update(self, rotation_information: RotationInformation):
        self.rotation_information = rotation_information
        self.update_from_transformation_matrix()

    @abstractmethod
    def update_from_transformation_matrix(self) -> None:
        raise RuntimeError("Method not implemented")

    def rotation_from_parameters(self, rotation_parameters) -> Rotation:
        rotation = None
        if self.rotation_information.format.name == "Angle-Axis":
            rotvec = np.asarray(rotation_parameters[1:]) * rotation_parameters[0]
            rotation = Rotation.from_rotvec(rotvec, degrees=self.rotation_information.use_degrees)
        elif self.rotation_information.format == RotationFormats.euler:
            rotation = Rotation.from_euler(
                self.rotation_information.euler_variant,
                rotation_parameters,
                degrees=self.rotation_information.use_degrees,
            )
        elif self.rotation_information.format.name == "Quaternion":
            rotation = Rotation.from_quat(rotation_parameters)
        elif self.rotation_information.format.name == "Rotation Vector":
            rotation = Rotation.from_rotvec(rotation_parameters, degrees=self.rotation_information.use_degrees)
        elif self.rotation_information.format.name == "Rotation Matrix":
            rotation_matrix = np.asarray(rotation_parameters).reshape([3, 3])
            rotation = Rotation.from_matrix(rotation_matrix)
        else:
            raise ValueError(f"Invalid variant: {self.variant}")
        return rotation

    def parameters_from_rotation(self, rotation: Rotation) -> List[float]:
        parameters = []
        if self.rotation_information.format.name == "Angle-Axis":
            rotvec = rotation.as_rotvec(degrees=self.rotation_information.use_degrees)
            angle = np.linalg.norm(rotvec)
            axis = rotvec / angle if angle else np.asarray([0, 0, 1])
            parameters = [angle, axis[0], axis[1], axis[2]]
        elif self.rotation_information.format == RotationFormats.euler:
            parameters = list(
                rotation.as_euler(
                    self.rotation_information.euler_variant, degrees=self.rotation_information.use_degrees
                )
            )
        elif self.rotation_information.format.name == "Quaternion":
            parameters = list(rotation.as_quat())
        elif self.rotation_information.format.name == "Rotation Vector":
            parameters = list(rotation.as_rotvec(degrees=self.rotation_information.use_degrees))
        elif self.rotation_information.format.name == "Rotation Matrix":
            parameters = list(rotation.as_matrix().flatten())
        else:
            raise ValueError(f"Invalid variant: {self.rotation_information.format.name}")
        if len(parameters) != self.rotation_information.format.number_of_parameters:
            raise ValueError(
                f"Expected number of parameters to be {self.rotation_information.format.number_of_parameters}, got {len(parameters)}"
            )
        return parameters

    def zivid_transformation_matrix(self):
        return zivid.Matrix4x4(self.transformation_matrix.as_matrix())

    def _rotation_label_text(self):
        degrees = (
            " (°)"
            if self.rotation_information.use_degrees
            and self.rotation_information.format not in ["Quaternion", "Rotation Matrix"]
            else (" (rad)" if self.rotation_information.format not in ["Quaternion", "Rotation Matrix"] else "")
        )
        return f"Rotation as {self.rotation_information.format.name}{degrees}"


def parameter_text_to_float(text: str) -> float:
    sanitized_text = text.strip().replace(",", ".")
    if sanitized_text == "":
        return 0.0
    if not re.fullmatch(r"[0-9.\-]+", sanitized_text):
        raise ValueError(f"Invalid input: {text}")
    return float(sanitized_text)


class PoseWidget(BasePoseWidget):
    yaml_pose_path: Path
    rotation_parameters: List[float]
    rotation_parameter_editors: List[QLineEdit]
    translation_parameter_editors: List[QLineEdit]
    pose_updated = pyqtSignal()
    rotation_vector_user_parameters: List[float] = [0.0, 0.0, 0.0]

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        title: str,
        initial_rotation_information: RotationInformation,
        yaml_pose_path: Path,
        eye_in_hand: bool,
        display_mode: PoseWidgetDisplayMode,
        descriptive_image_paths: Optional[Tuple[Path, Path]] = None,
        read_only: bool = False,
        parent=None,
    ):
        super().__init__(
            title, initial_rotation_information, eye_in_hand, display_mode, descriptive_image_paths, read_only, parent
        )

        self.yaml_pose_path = yaml_pose_path

        self.setup_widgets()
        self.setup_layout()
        self.setup_connections()

        if self.yaml_pose_path.exists():
            self.load_yaml()
        else:
            print(f"{self.yaml_pose_path} does not exist.")
        self.update_from_transformation_matrix()
        self.toggle_advanced_section(display_mode == PoseWidgetDisplayMode.Advanced)

    def setup_widgets(self):
        self.translation_parameters_label = QLabel()
        self.translation_parameters_label.setText("Translation")
        self.translation_parameter_editors = [QLineEdit() for _ in range(3)]
        for index, parameter_editor in enumerate(self.translation_parameter_editors):
            parameter_editor.setObjectName(f"translation_parameter_{index}")
            parameter_editor.setReadOnly(self.read_only)

        self.rotation_parameters_layout = QGridLayout()
        self.rotation_parameters_label = QLabel()
        self.rotation_parameters_label.setText(self._rotation_label_text())
        self.rotation_parameter_editors = [QLineEdit() for _ in range(9)]
        for index, parameter_editor in enumerate(self.rotation_parameter_editors):
            parameter_editor.setObjectName(f"rotation_parameter_{index}")
            parameter_editor.setReadOnly(self.read_only)

        self.advanced_divider = create_horizontal_line()
        self.pose_label = QLabel()
        self.pose_label.setText(f"Translation + {self._rotation_label_text()}")
        self.pose_text = QLineEdit()
        self.pose_text.setReadOnly(self.read_only)

    def setup_layout(self):

        self.group_box = QGroupBox(self.title)

        group_layout = QVBoxLayout()

        row_offset = 0 if self.display_mode == PoseWidgetDisplayMode.OnlyPose else 3

        if self.display_mode != PoseWidgetDisplayMode.OnlyPose:
            self.grid_layout.addWidget(create_horizontal_line(), row_offset, 0, 1, 4)
            row_offset = row_offset + 1

        self.grid_layout.addWidget(self.translation_parameters_label, row_offset, 0)
        for index, parameter_editor in enumerate(self.translation_parameter_editors, start=1):
            self.grid_layout.addWidget(parameter_editor, row_offset, index, 1, 1)
        row_offset = row_offset + 1

        self.grid_layout.addWidget(create_horizontal_line(), row_offset, 0, 1, 4)
        row_offset = row_offset + 1

        for index, parameter_editor in enumerate(self.rotation_parameter_editors):
            row = index // 3 if self.rotation_information.format.number_of_parameters == 9 else 0
            col = index % 3 if self.rotation_information.format.number_of_parameters == 9 else index
            self.rotation_parameters_layout.addWidget(parameter_editor, row, col)
        self.grid_layout.addWidget(self.rotation_parameters_label, row_offset, 0)
        self.grid_layout.addLayout(self.rotation_parameters_layout, row_offset, 1, 1, 3)
        row_offset = row_offset + 1

        self.grid_layout.addWidget(self.advanced_divider, row_offset, 0, 1, 4)
        self.grid_layout.addWidget(self.pose_label, row_offset + 1, 0)
        self.grid_layout.addWidget(self.pose_text, row_offset + 1, 1, 1, 3)
        self.advanced_widgets = [self.advanced_divider, self.pose_label, self.pose_text]
        row_offset = row_offset + 2

        if self.descriptive_image_label is not None:
            rowspan = 3
            if self.display_mode == PoseWidgetDisplayMode.Advanced:
                rowspan = rowspan + 6
                self.grid_layout.addWidget(
                    self.descriptive_image_label, row_offset, 3, 3, 1, alignment=Qt.AlignVCenter | Qt.AlignCenter
                )
                self.descriptive_image_label.setFixedHeight(self._height_of_yaml_text())
            elif self.display_mode == PoseWidgetDisplayMode.Basic:
                rowspan = rowspan + 4
                self.grid_layout.addWidget(
                    self.descriptive_image_label, 0, 4, 7, 1, alignment=Qt.AlignVCenter | Qt.AlignCenter
                )
                self.descriptive_image_label.setHeightFromGrid(self.grid_layout, 0, 5, 0, 4)
            elif self.display_mode == PoseWidgetDisplayMode.OnlyPose:
                self.grid_layout.addWidget(
                    self.descriptive_image_label, 0, 4, 3, 1, alignment=Qt.AlignVCenter | Qt.AlignCenter
                )
                self.descriptive_image_label.setHeightFromGrid(self.grid_layout, 0, 2, 0, 4)
            else:
                raise ValueError(f"Invalid display mode: {self.display_mode}")

        if self.display_mode == PoseWidgetDisplayMode.OnlyPose:
            group_layout.addLayout(self.grid_layout)
        else:
            group_layout.addWidget(self.rotation_format_selection_widget)
        self.group_box.setLayout(group_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.group_box)
        self.setLayout(main_layout)

    def setup_connections(self):
        for parameter_editor in self.translation_parameter_editors:
            parameter_editor.editingFinished.connect(self.on_translation_parameter_changed)
        for parameter_editor in self.rotation_parameter_editors:
            parameter_editor.editingFinished.connect(self.on_rotation_parameter_changed)
        self.pose_text.editingFinished.connect(self.on_pose_text_changed)

    def toggle_advanced_section(self, checked: bool):
        for widget in self.advanced_widgets:
            widget.setVisible(checked)
        if self.descriptive_image_label is not None:
            self.grid_layout.removeWidget(self.descriptive_image_label)
            rowspan = 3
            if self.display_mode != PoseWidgetDisplayMode.OnlyPose:
                rowspan += 4
            if checked:
                rowspan += 2
            self.grid_layout.addWidget(
                self.descriptive_image_label, 0, 4, rowspan, 1, alignment=Qt.AlignVCenter | Qt.AlignCenter
            )

    def update_from_transformation_matrix(self) -> None:
        self.rotation_parameters = self.parameters_from_rotation(self.transformation_matrix.rotation)
        if self.rotation_information.format == "Rotation Vector" and not np.all(
            np.asarray(self.rotation_vector_user_parameters) == np.zeros(3)
        ):
            self.rotation_parameters = self.rotation_vector_user_parameters
        self.rotation_parameters_label.setText(self._rotation_label_text())
        self.pose_label.setText(f"Translation + {self._rotation_label_text()}")
        for i in reversed(range(self.rotation_parameters_layout.count())):
            widget = self.rotation_parameters_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        for index, parameter_editor in enumerate(self.rotation_parameter_editors):
            row = index // 3 if self.rotation_information.format.number_of_parameters == 9 else 0
            col = index % 3 if self.rotation_information.format.number_of_parameters == 9 else index
            self.rotation_parameters_layout.addWidget(parameter_editor, row, col)
        with QSignalBlocker(self.pose_text):
            self.pose_text.setText(
                " ".join([f"{value:.3f}" for value in list(self.transformation_matrix.translation)])
                + " "
                + " ".join([f"{value:.3f}" for value in self.rotation_parameters])
            )
        for i, parameter_editor in enumerate(self.rotation_parameter_editors):
            if i < self.rotation_information.format.number_of_parameters:
                with QSignalBlocker(parameter_editor):
                    parameter_editor.setText(f"{self.rotation_parameters[i]:.3f}")
                parameter_editor.setVisible(True)
            else:
                parameter_editor.setVisible(False)
        for i, parameter_editor in enumerate(self.translation_parameter_editors):
            with QSignalBlocker(parameter_editor):
                parameter_editor.setText(f"{self.transformation_matrix.translation[i]:.3f}")
        self.reset_parameter_editor_styles()
        self.pose_updated.emit()

    def on_rotation_parameter_changed(self):
        modified_index = int(self.sender().objectName().split("_")[-1])
        try:
            update_parameter = parameter_text_to_float(self.sender().text())
            if np.isclose(update_parameter, self.rotation_parameters[modified_index]):
                return
        except ValueError:
            # We have invalid input, ignore it and revert to what we had before.
            self.update_from_transformation_matrix()
            return

        updated_rotation_parameters = [
            parameter_text_to_float(parameter_editor.text())
            for i, parameter_editor in enumerate(self.rotation_parameter_editors)
            if i < self.rotation_information.format.number_of_parameters
        ]
        if self.rotation_information.format == "Rotation Vector":
            self.rotation_vector_user_parameters = updated_rotation_parameters
        updated_rotation = self.rotation_from_parameters(updated_rotation_parameters)
        parameters_from_updated_rotation = self.parameters_from_rotation(updated_rotation)
        has_valid_input = True
        for index, rotation_parameters in enumerate(updated_rotation_parameters):
            if index != modified_index and not np.isclose(parameters_from_updated_rotation[index], rotation_parameters):
                self.sender().setStyleSheet("background-color: yellow; color: black;")
                has_valid_input = False
        if self.rotation_information.format == "Rotation Vector":
            rotation_from_scipy_rotvec = self.rotation_from_parameters(parameters_from_updated_rotation)
            rotation_from_user_rotvec = self.rotation_from_parameters(self.rotation_vector_user_parameters)
            if np.allclose(rotation_from_scipy_rotvec.as_rotvec(), rotation_from_user_rotvec.as_rotvec()):
                has_valid_input = True
        if has_valid_input:
            self.rotation_parameters = updated_rotation_parameters
            self.transformation_matrix.rotation = updated_rotation
            self.update_from_transformation_matrix()

    def on_translation_parameter_changed(self):
        modified_index = int(self.sender().objectName().split("_")[-1])
        try:
            update_parameter = parameter_text_to_float(self.sender().text())
            if np.isclose(update_parameter, self.transformation_matrix.translation[modified_index]):
                return
        except ValueError:
            # We have invalid input, ignore it and revert to what we had before.
            self.update_from_transformation_matrix()
            return

        for i, parameter_editor in enumerate(self.translation_parameter_editors):
            self.transformation_matrix.translation[i] = parameter_text_to_float(parameter_editor.text())
        self.update_from_transformation_matrix()

    def on_pose_text_changed(self):
        parameter_list = re.split(r"[,\s]+", self.pose_text.text().strip())
        if len(parameter_list) < (3 + len(self.rotation_parameters)):
            # Wait for user to finish entering data
            return
        self.transformation_matrix.translation = np.array([float(value) for value in parameter_list[:3]])
        updated_rotation_parameters = [float(value) for value in parameter_list[3:]]
        if self.rotation_information.format == "Rotation Vector":
            self.rotation_vector_user_parameters = updated_rotation_parameters
        updated_rotation = self.rotation_from_parameters(updated_rotation_parameters)
        self.rotation_parameters = updated_rotation_parameters
        self.transformation_matrix.rotation = updated_rotation
        self.update_from_transformation_matrix()

    def reset_parameter_editor_styles(self):
        for parameter_editor in self.rotation_parameter_editors:
            parameter_editor.setStyleSheet("")

    def set_yaml_path_and_save(self, yaml_pose_path: Path):
        self.yaml_pose_path = yaml_pose_path
        self.save_yaml()

    def set_yaml_path_and_load(self, yaml_pose_path: Path):
        if not yaml_pose_path.exists():
            QMessageBox.warning(self, "Warning", f"File {yaml_pose_path} does not exist!")
        self.yaml_pose_path = yaml_pose_path
        self.load_yaml()

    def save_yaml(self):
        self.zivid_transformation_matrix().save(self.yaml_pose_path)

    def load_yaml(self):
        error_message = None
        try:
            transformation_matrix = zivid.Matrix4x4(self.yaml_pose_path)
            matrix = np.array(transformation_matrix)
            if matrix is None:
                raise ValueError("Invalid transform")
            try:
                zivid.calibration.Pose(matrix)
            except RuntimeError as ex:
                raise RuntimeError("matrix is not affine") from ex
            self.transformation_matrix = TransformationMatrix.from_matrix(np.asarray(transformation_matrix))
            self.update_from_transformation_matrix()
        except Exception as ex:
            error_message = f"Failed to load from {self.yaml_pose_path}: {ex}"
            QMessageBox.warning(self, "Load Error", error_message)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        for parameter_editor in self.translation_parameter_editors:
            if parameter_editor.isVisible():
                widgets.append(parameter_editor)
        for parameter_editor in self.rotation_parameter_editors:
            if parameter_editor.isVisible():
                widgets.append(parameter_editor)
        if self.pose_text.isVisible():
            widgets.append(self.pose_text)
        return widgets

    @classmethod
    def HandEye(
        cls,
        yaml_pose_path: Path,
        eye_in_hand: bool,
        display_mode: PoseWidgetDisplayMode = PoseWidgetDisplayMode.Basic,
        initial_rotation_information: RotationInformation = RotationInformation(),
    ):
        ee_camera_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-on-robot-ee-camera-pose-low-res.png"
        )
        rob_camera_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-rob-camera-pose-low-res.png"
        )
        return cls(
            title="Hand Eye Transform",
            initial_rotation_information=initial_rotation_information,
            yaml_pose_path=yaml_pose_path,
            eye_in_hand=eye_in_hand,
            display_mode=display_mode,
            descriptive_image_paths=(ee_camera_pose_img_path, rob_camera_pose_img_path),
        )

    @classmethod
    def Robot(
        cls,
        yaml_pose_path: Path,
        eye_in_hand: bool,
        display_mode: PoseWidgetDisplayMode = PoseWidgetDisplayMode.Basic,
        initial_rotation_information: RotationInformation = RotationInformation(),
    ):
        robot_ee_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-on-robot-robot-ee-pose-low-res.png"
        )
        rob_ee_pose_img_path = get_image_file_path("hand-eye-robot-and-calibration-board-rob-ee-pose-low-res.png")
        return cls(
            title="Robot Pose",
            initial_rotation_information=initial_rotation_information,
            yaml_pose_path=yaml_pose_path,
            eye_in_hand=eye_in_hand,
            display_mode=display_mode,
            descriptive_image_paths=(robot_ee_pose_img_path, rob_ee_pose_img_path),
        )

    @classmethod
    def CalibrationBoardInCameraFrame(
        cls,
        yaml_pose_path: Path,
        eye_in_hand: bool,
        display_mode: PoseWidgetDisplayMode = PoseWidgetDisplayMode.Basic,
        initial_rotation_information: RotationInformation = RotationInformation(),
    ):
        eih_camera_object_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-on-robot-camera-object-pose-low-res.png"
        )
        eth_camera_object_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-object-pose-low-res.png"
        )
        return cls(
            title="Checkerboard Pose In Camera Frame",
            initial_rotation_information=initial_rotation_information,
            yaml_pose_path=yaml_pose_path,
            eye_in_hand=eye_in_hand,
            display_mode=display_mode,
            descriptive_image_paths=(eih_camera_object_pose_img_path, eth_camera_object_pose_img_path),
            read_only=True,
        )

    @classmethod
    def CalibrationBoardInRobotFrame(
        cls,
        yaml_pose_path: Path,
        eye_in_hand: bool,
        display_mode: PoseWidgetDisplayMode = PoseWidgetDisplayMode.Basic,
        initial_rotation_information: RotationInformation = RotationInformation(),
    ):
        eih_robot_object_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-on-robot-robot-object-pose-low-res.png"
        )
        eth_robot_object_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-ee-object-pose-low-res.png"
        )
        return cls(
            title="Checkerboard Pose In Robot Base Frame",
            initial_rotation_information=initial_rotation_information,
            yaml_pose_path=yaml_pose_path,
            eye_in_hand=eye_in_hand,
            display_mode=display_mode,
            descriptive_image_paths=(eih_robot_object_pose_img_path, eth_robot_object_pose_img_path),
            read_only=True,
        )


class MarkerPosesWidget(BasePoseWidget):
    yaml_pose_path: Path
    markers: Dict[str, TransformationMatrix] = {}
    rotation_parameters: Dict[str, List[float]] = {}
    translation_parameters: Dict[str, List[float]] = {}
    max_rows_before_scrolling: int = 5
    pose_updated = pyqtSignal()

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        title: str,
        initial_rotation_information: RotationInformation,
        eye_in_hand: bool,
        display_mode: PoseWidgetDisplayMode,
        descriptive_image_paths: Optional[Tuple[Path, Path]] = None,
        read_only: bool = False,
        parent=None,
    ):
        super().__init__(
            title, initial_rotation_information, eye_in_hand, display_mode, descriptive_image_paths, read_only, parent
        )

        self.setup_widgets()
        self.setup_layout()

    def setup_widgets(self):
        self.ids_title_label = QLabel("IDs")
        self.translation_title_label = QLabel("Translation")
        self.rotation_title_label = QLabel(self._rotation_label_text())
        self.translation_parameter_labels = {}
        self.rotation_parameter_labels = {}

    def setup_layout(self):
        self.group_box = QGroupBox(self.title)

        self.grid_layout = QGridLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        self.group_box_contents = QWidget()
        self.group_box_contents.setLayout(self.grid_layout)

        self.scroll_area.setWidget(self.group_box_contents)

        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(0, 0, 0, 10)
        group_layout.setSpacing(0)
        group_layout.addWidget(self.scroll_area)
        self.group_box.setLayout(group_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.group_box)
        self.setLayout(main_layout)

        row_offset = 0 if self.display_mode == PoseWidgetDisplayMode.OnlyPose else 3

        self.grid_layout.addWidget(self.ids_title_label, row_offset, 0)
        self.grid_layout.addWidget(self.translation_title_label, row_offset, 1, 1, 3, alignment=Qt.AlignCenter)
        self.grid_layout.addWidget(create_vertical_line(), row_offset, 4)
        self.grid_layout.addWidget(
            self.rotation_title_label,
            row_offset,
            5,
            1,
            self.rotation_information.format.number_of_parameters,
            alignment=Qt.AlignCenter,
        )

        self.update_layout()

    def update_layout(self):
        row_start = row_offset = 1 if self.display_mode == PoseWidgetDisplayMode.OnlyPose else 4

        for row in range(row_offset, self.grid_layout.rowCount()):
            for col in range(self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(row, col)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        if widget != self.descriptive_image_label:
                            widget.deleteLater()
                        self.grid_layout.removeWidget(widget)

        for key, value in self.translation_parameters.items():
            # Add label for the ID or row label
            self.grid_layout.addWidget(QLabel(key), row_offset, 0, 1, 1)

            # Add translation parameters
            for index, parameter in enumerate(value, start=1):
                label = QLabel(f"{parameter:>7.1f}")
                label.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.grid_layout.addWidget(label, row_offset, index)

            self.grid_layout.addWidget(create_vertical_line(), row_offset, 4)

            # Add rotation parameters
            for index, parameter in enumerate(self.rotation_parameters[key], start=5):
                label_text = f"{parameter:>4.1f}" if self.rotation_information.use_degrees else f"{parameter:>2.3f}"
                label = QLabel(label_text)
                label.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.grid_layout.addWidget(label, row_offset, index)

            row_offset += 1

        if self.descriptive_image_label is not None:
            if self.display_mode in [PoseWidgetDisplayMode.OnlyPose, PoseWidgetDisplayMode.Basic]:
                self.grid_layout.addWidget(
                    self.descriptive_image_label,
                    row_start - 1,
                    self.rotation_information.format.number_of_parameters + 5,
                    min(row_offset - (row_start - 1), self.max_rows_before_scrolling),
                    1,
                    alignment=Qt.AlignVCenter | Qt.AlignCenter,
                )
                self.descriptive_image_label.setHeightFromGrid(
                    self.grid_layout, 1, row_offset, 0, self.rotation_information.format.number_of_parameters + 4
                )
            else:
                raise ValueError(f"Invalid display mode: {self.display_mode}")

        if row_offset > self.max_rows_before_scrolling:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def set_title(self, title: str):
        self.group_box.setTitle(title)

    def update_markers(self):
        self.translation_parameters = {}
        self.rotation_parameters = {}
        for key, transformation_matrix in self.markers.items():
            self.translation_parameters[key] = list(transformation_matrix.translation)
            self.rotation_parameters[key] = self.parameters_from_rotation(transformation_matrix.rotation)
        self.update_layout()

    def set_markers(self, markers: Dict[str, TransformationMatrix]):
        self.markers = markers
        self.update_markers()

    def on_transform_format_changed(self):
        self.rotation_title_label.setText(self._rotation_label_text())
        self.update_markers()

    def update_from_transformation_matrix(self) -> None:
        self.rotation_title_label.setText(self._rotation_label_text())
        self.update_markers()

    @classmethod
    def MarkersInCameraFrame(
        cls,
        eye_in_hand: bool,
        display_mode: PoseWidgetDisplayMode = PoseWidgetDisplayMode.Basic,
        initial_rotation_information: RotationInformation = RotationInformation(),
    ):
        eih_camera_object_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-on-robot-camera-object-pose-low-res.png"
        )
        eth_camera_object_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-object-pose-low-res.png"
        )
        return cls(
            title="Marker Poses In Camera Frame",
            initial_rotation_information=initial_rotation_information,
            eye_in_hand=eye_in_hand,
            display_mode=display_mode,
            descriptive_image_paths=(eih_camera_object_pose_img_path, eth_camera_object_pose_img_path),
            read_only=True,
        )

    @classmethod
    def MarkersInRobotFrame(
        cls,
        eye_in_hand: bool,
        display_mode: PoseWidgetDisplayMode = PoseWidgetDisplayMode.Basic,
        initial_rotation_information: RotationInformation = RotationInformation(),
    ):
        eih_robot_object_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-on-robot-robot-object-pose-low-res.png"
        )
        eth_robot_object_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-ee-object-pose-low-res.png"
        )
        return cls(
            title=f"Marker Poses In Robot {('Base' if eye_in_hand else 'Tool')} Frame",
            initial_rotation_information=initial_rotation_information,
            eye_in_hand=eye_in_hand,
            display_mode=display_mode,
            descriptive_image_paths=(eih_robot_object_pose_img_path, eth_robot_object_pose_img_path),
            read_only=True,
        )
