"""
Settings Selection

Note: This script requires PyQt5 to be installed.

"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtGui import QDoubleValidator, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from zivid.calibration import Pose
from zivid.experimental.hand_eye_low_dof import (
    FixedPlacementOfCalibrationBoard,
    FixedPlacementOfCalibrationObjects,
    FixedPlacementOfFiducialMarker,
    FixedPlacementOfFiducialMarkers,
)
from zividsamples.gui.aspect_ratio_label import AspectRatioLabel
from zividsamples.gui.hand_eye_configuration import CalibrationObject, HandEyeConfiguration
from zividsamples.gui.marker_widget import MarkerConfiguration
from zividsamples.gui.pose_widget import PoseWidget, PoseWidgetDisplayMode, TransformationMatrix
from zividsamples.gui.qt_application import ZividQtApplication
from zividsamples.gui.rotation_format_configuration import RotationInformation
from zividsamples.paths import get_image_file_path


@dataclass
class FixedCalibrationObjectsData:
    hand_eye_configuration: HandEyeConfiguration
    marker_configuration: Optional[MarkerConfiguration] = None
    marker_positions_eye_in_hand: Optional[dict[int, list[float]]] = None
    marker_positions_eye_to_hand: Optional[dict[int, list[float]]] = None
    calibration_board_pose_eye_in_hand: Optional[TransformationMatrix] = None
    calibration_board_pose_eye_to_hand: Optional[TransformationMatrix] = None
    use_rotation: bool = False

    def update_hand_eye_configuration(self, hand_eye_configuration: HandEyeConfiguration):
        self.hand_eye_configuration = hand_eye_configuration
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Markers:
            assert self.marker_configuration is not None
            self.update_marker_configuration(self.marker_configuration)

    def update_marker_configuration(self, marker_configuration: MarkerConfiguration):
        self.marker_configuration = marker_configuration
        marker_positions = (
            self.marker_positions_eye_in_hand
            if self.hand_eye_configuration.eye_in_hand
            else self.marker_positions_eye_to_hand
        )
        if marker_positions is not None:
            marker_positions = {
                marker_id: marker_positions.get(marker_id, [0.0, 0.0, 0.0])
                for marker_id in self.marker_configuration.id_list
            }
            if self.hand_eye_configuration.eye_in_hand:
                self.marker_positions_eye_in_hand = marker_positions
            else:
                self.marker_positions_eye_to_hand = marker_positions

    def has_data(self) -> bool:
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            if self.hand_eye_configuration.eye_in_hand:
                return self.calibration_board_pose_eye_in_hand is not None
            return self.calibration_board_pose_eye_to_hand is not None
        if self.hand_eye_configuration.eye_in_hand:
            return self.marker_positions_eye_in_hand is not None
        return self.marker_positions_eye_to_hand is not None

    def to_fixed_calibration_objects(self) -> FixedPlacementOfCalibrationObjects:
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            transformation_matrix = TransformationMatrix()
            if self.hand_eye_configuration.eye_in_hand:
                if self.calibration_board_pose_eye_in_hand is None:
                    raise ValueError(
                        "Calibration board pose in robot base frame must be set when checkerboard is selected as calibration object."
                    )
                transformation_matrix = self.calibration_board_pose_eye_in_hand
            else:
                if self.calibration_board_pose_eye_to_hand is None:
                    raise ValueError(
                        "Calibration board pose in end-effector frame must be set when checkerboard is selected as calibration object."
                    )
                transformation_matrix = self.calibration_board_pose_eye_to_hand
            if self.use_rotation:
                return FixedPlacementOfCalibrationObjects(
                    FixedPlacementOfCalibrationBoard(Pose(transformation_matrix.as_matrix()))
                )
            return FixedPlacementOfCalibrationObjects(
                FixedPlacementOfCalibrationBoard(transformation_matrix.translation)
            )
        if self.marker_configuration is None:
            raise ValueError("Marker configuration must be set when Markers is selected as calibration object.")
        if self.hand_eye_configuration.eye_in_hand:
            if self.marker_positions_eye_in_hand is None:
                raise ValueError(
                    "Marker positions in robot base frame must be set when Markers is selected as calibration object."
                )
        else:
            if self.marker_positions_eye_to_hand is None:
                raise ValueError(
                    "Marker positions in end-effector frame must be set when Markers is selected as calibration object."
                )
        marker_positions = (
            self.marker_positions_eye_in_hand
            if self.hand_eye_configuration.eye_in_hand
            else self.marker_positions_eye_to_hand
        )
        assert marker_positions is not None
        return FixedPlacementOfCalibrationObjects(
            FixedPlacementOfFiducialMarkers(
                marker_dictionary=self.marker_configuration.dictionary,
                markers=[
                    FixedPlacementOfFiducialMarker(marker_id=int(marker_id), position=marker_position)
                    for marker_id, marker_position in marker_positions.items()
                ],
            )
        )


class MarkerWithPosition:
    marker_id: QLabel
    pose_x: QLineEdit
    pose_y: QLineEdit
    pose_z: QLineEdit

    def __init__(self, marker_id: int, position: list[float]):
        self.marker_id = QLabel(str(marker_id))
        self.marker_id.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.pose_x = QLineEdit(str(position[0]))
        self.pose_x.setValidator(QDoubleValidator())
        self.pose_x.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)
        self.pose_y = QLineEdit(str(position[1]))
        self.pose_y.setValidator(QDoubleValidator())
        self.pose_y.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)
        self.pose_z = QLineEdit(str(position[2]))
        self.pose_z.setValidator(QDoubleValidator())
        self.pose_z.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)

    def position(self) -> list[float]:
        current_locale = QLocale()
        return [current_locale.toDouble(pose.text())[0] for pose in [self.pose_x, self.pose_y, self.pose_z]]


class DynamicMarkerList(QWidget):

    def __init__(self, fixed_calibration_objects: FixedCalibrationObjectsData):
        super().__init__()
        self.markers_with_position_widgets: list[MarkerWithPosition] = []

        self.marker_container = QWidget()
        self.marker_scrollable_area = QScrollArea()
        self.marker_scrollable_area.setWidgetResizable(True)
        self.marker_scrollable_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.marker_scrollable_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.marker_scrollable_area.setWidget(self.marker_container)
        layout = QVBoxLayout(self.marker_scrollable_area)
        self.grid_layout = QGridLayout()
        layout.addLayout(self.grid_layout)
        self.grid_layout.addWidget(QLabel("ID"), 0, 0)
        x_label = QLabel("X")
        x_label.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(x_label, 0, 1)
        y_label = QLabel("Y")
        y_label.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(y_label, 0, 2)
        z_label = QLabel("Z")
        z_label.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(z_label, 0, 3)
        marker_positions = (
            fixed_calibration_objects.marker_positions_eye_in_hand
            if fixed_calibration_objects.hand_eye_configuration.eye_in_hand
            else fixed_calibration_objects.marker_positions_eye_to_hand
        )
        if marker_positions is not None:
            for row, (marker_id, position) in enumerate(marker_positions.items(), start=1):
                self.add_marker(row, marker_id, position)
        else:
            assert fixed_calibration_objects.marker_configuration is not None
            for row, marker_id in enumerate(fixed_calibration_objects.marker_configuration.id_list, start=1):
                self.add_marker(row, marker_id, [0.0, 0.0, 0.0])
        self.setLayout(layout)

    def add_marker(self, row: int, marker_id: int, position: list[float]):
        marker_with_position = MarkerWithPosition(
            marker_id=marker_id,
            position=position,
        )
        self.grid_layout.addWidget(marker_with_position.marker_id, row, 0)
        self.grid_layout.addWidget(marker_with_position.pose_x, row, 1)
        self.grid_layout.addWidget(marker_with_position.pose_y, row, 2)
        self.grid_layout.addWidget(marker_with_position.pose_z, row, 3)
        self.markers_with_position_widgets.append(marker_with_position)

    def get_markers(self) -> dict[int, list[float]]:
        return {
            int(marker_with_position.marker_id.text()): marker_with_position.position()
            for marker_with_position in self.markers_with_position_widgets
        }


class FixedObjectsSelectionDialog(QDialog):

    def __init__(
        self,
        current_fixed_calibration_objects_data: FixedCalibrationObjectsData,
        initial_rotation_information: RotationInformation,
    ):
        super().__init__()
        self.setWindowTitle("Set Fixed Objects")
        self.fixed_calibration_objects_data = current_fixed_calibration_objects_data
        self.create_common_widgets()
        if (
            self.fixed_calibration_objects_data.hand_eye_configuration.calibration_object
            == CalibrationObject.Checkerboard
        ):
            self.create_checkerboard_widgets(initial_rotation_information)
        else:
            self.create_marker_widgets()
        self.create_common_layout()
        if (
            self.fixed_calibration_objects_data.hand_eye_configuration.calibration_object
            == CalibrationObject.Checkerboard
        ):
            self.create_checkerboard_layout()
        else:
            self.create_marker_layout()

    def create_common_widgets(self):
        self.descriptive_text = QLabel()
        self.fixed_object_pose_eye_to_hand_label = AspectRatioLabel(
            title="Pose of fixed objects in Eye-to-Hand configuration",
            pixmap=QPixmap(get_image_file_path("hand-eye-robot-and-calibration-board-ee-object-pose.png").as_posix()),
        )
        self.fixed_object_pose_eye_in_hand_label = AspectRatioLabel(
            title="Pose of fixed objects in Eye-in-Hand configuration",
            pixmap=QPixmap(
                get_image_file_path(
                    "hand-eye-robot-and-calibration-board-camera-on-robot-robot-object-pose.png"
                ).as_posix()
            ),
        )
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)

    def create_checkerboard_widgets(
        self,
        initial_rotation_information: RotationInformation,
    ):
        if self.fixed_calibration_objects_data.hand_eye_configuration.eye_in_hand:
            self.descriptive_text.setText(
                (
                    "Enter the position of the calibration board relative to robot base. "
                    "For a more accurate calibration, enter the rotation of the calibration board as well."
                )
            )
        else:
            self.descriptive_text.setText(
                (
                    "Enter the position of the calibration board relative to your current tool center point (TCP). "
                    "For a more accurate calibration, enter the rotation of the calibration board as well."
                )
            )
        self.pose_widget = PoseWidget(
            title="Calibration Board Pose",
            initial_rotation_information=initial_rotation_information,
            yaml_pose_path=Path("fixed_calibration_object_pose.yaml"),
            eye_in_hand=self.fixed_calibration_objects_data.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.Basic,
        )
        transformation_matrix = (
            self.fixed_calibration_objects_data.calibration_board_pose_eye_in_hand
            if self.fixed_calibration_objects_data.hand_eye_configuration.eye_in_hand
            else self.fixed_calibration_objects_data.calibration_board_pose_eye_to_hand
        )
        if transformation_matrix is None:
            transformation_matrix = TransformationMatrix()
        self.pose_widget.set_transformation_matrix(transformation_matrix)
        self.pose_widget.setObjectName("SetFixedObjects-pose_widget")
        self.use_rotation_checkbox = QCheckBox("Use rotation")
        self.use_rotation_checkbox.setChecked(self.fixed_calibration_objects_data.use_rotation)
        self.use_rotation_checkbox.setObjectName("SetFixedObjects-use_rotation_checkbox")

        self.calibration_board_pose_label = AspectRatioLabel(
            title="Calibration Board Pose", pixmap=QPixmap(get_image_file_path("zvd_cb01_pose.png").as_posix())
        )

    def create_marker_widgets(self):
        current_hand_eye_configuration = self.fixed_calibration_objects_data.hand_eye_configuration
        if current_hand_eye_configuration.eye_in_hand:
            self.descriptive_text.setText("For each marker, enter its position relative to robot base.")
        else:
            self.descriptive_text.setText(
                "For each marker, enter its position relative to your current tool center point (TCP)."
            )
        self.markers_widget = DynamicMarkerList(self.fixed_calibration_objects_data)
        self.markers_widget.setObjectName("SetFixedObjects-markers_widget")

    def create_common_layout(self):
        descriptive_text_box = QGroupBox("Description")
        descriptive_text_layout = QVBoxLayout()
        descriptive_text_layout.addWidget(self.descriptive_text)
        descriptive_text_box.setLayout(descriptive_text_layout)
        self.horizontal_layout = QHBoxLayout()
        self.left_vertical_layout = QVBoxLayout()
        self.left_vertical_layout.addWidget(self.button_box)
        self.left_vertical_layout.addWidget(descriptive_text_box)
        self.horizontal_layout.addLayout(self.left_vertical_layout)
        if self.fixed_calibration_objects_data.hand_eye_configuration.eye_in_hand:
            self.horizontal_layout.addWidget(self.fixed_object_pose_eye_in_hand_label)
        else:
            self.horizontal_layout.addWidget(self.fixed_object_pose_eye_to_hand_label)
        self.setLayout(self.horizontal_layout)

    def create_checkerboard_layout(self):
        self.left_vertical_layout.addWidget(self.pose_widget)
        self.left_vertical_layout.addWidget(self.use_rotation_checkbox)
        self.horizontal_layout.addWidget(self.calibration_board_pose_label)

    def create_marker_layout(self):
        self.left_vertical_layout.addWidget(self.markers_widget)

    def accept(self):
        if (
            self.fixed_calibration_objects_data.hand_eye_configuration.calibration_object
            == CalibrationObject.Checkerboard
        ):
            if self.fixed_calibration_objects_data.hand_eye_configuration.eye_in_hand:
                self.fixed_calibration_objects_data.calibration_board_pose_eye_in_hand = (
                    self.pose_widget.transformation_matrix
                )
            else:
                self.fixed_calibration_objects_data.calibration_board_pose_eye_to_hand = (
                    self.pose_widget.transformation_matrix
                )
            self.fixed_calibration_objects_data.use_rotation = self.use_rotation_checkbox.isChecked()
        elif self.fixed_calibration_objects_data.hand_eye_configuration.eye_in_hand:
            self.fixed_calibration_objects_data.marker_positions_eye_in_hand = self.markers_widget.get_markers()
        else:
            self.fixed_calibration_objects_data.marker_positions_eye_to_hand = self.markers_widget.get_markers()
        super().accept()


def set_fixed_objects(
    current_fixed_calibration_objects_data: FixedCalibrationObjectsData,
    rotation_information: RotationInformation = RotationInformation(),
) -> Optional[FixedCalibrationObjectsData]:
    dialog = FixedObjectsSelectionDialog(current_fixed_calibration_objects_data, rotation_information)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.fixed_calibration_objects_data
    return None


if __name__ == "__main__":
    with ZividQtApplication():
        # Example usage
        result = set_fixed_objects(
            FixedCalibrationObjectsData(
                hand_eye_configuration=HandEyeConfiguration(
                    eye_in_hand=True, calibration_object=CalibrationObject.Markers
                ),
                marker_configuration=MarkerConfiguration(),
                marker_positions_eye_in_hand={
                    0: [100.0, 1000.0, 0.0],
                    1: [150.0, 1050.0, 0.0],
                    2: [150.0, 1000.0, 0.0],
                    3: [100.0, 1050.0, 0.0],
                },
                marker_positions_eye_to_hand={
                    0: [100.0, 0.0, 0.0],
                    1: [150.0, 50.0, 0.0],
                    2: [150.0, 0.0, 0.0],
                    3: [100.0, 50.0, 0.0],
                },
                calibration_board_pose_eye_in_hand=TransformationMatrix(
                    translation=[-90.0, 1220.0, 0.0],
                ),
                calibration_board_pose_eye_to_hand=TransformationMatrix(
                    translation=[-90.0, 220.0, 0.0],
                ),
                use_rotation=True,
            )
        )
        if result:
            print("Fixed objects set successfully:")
            print(result.to_fixed_calibration_objects())
        else:
            print("Fixed objects not set.")
