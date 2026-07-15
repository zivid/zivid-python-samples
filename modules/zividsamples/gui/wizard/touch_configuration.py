"""
Touch Configuration

Note: This script requires PyQt5 to be installed.

"""

from typing import List, Optional

import numpy as np
from PyQt5.QtCore import QSettings, QSignalBlocker
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from zivid.calibration import MarkerDictionary
from zividsamples.gui.widgets.pose_widget import PoseWidget, PoseWidgetDisplayMode
from zividsamples.gui.wizard.rotation_format_configuration import RotationInformation
from zividsamples.transformation_matrix import TransformationMatrix

_TOUCH_TOOL_TRANSFORM_KEY = "touch_tool_transform"
_DEFAULT_Z_OFFSET_MM = 300


def _touch_tool_transform_from_qsettings(qsettings: QSettings) -> TransformationMatrix:
    """Load touch_tool_transform from QSettings, or build from legacy z_offset.

    Args:
        qsettings: QSettings group to read the touch tool transform from

    Returns:
        The stored touch tool transform, or one built from the legacy z_offset
    """
    try:
        stored = qsettings.value(_TOUCH_TOOL_TRANSFORM_KEY)
        if stored is not None and isinstance(stored, (list, tuple)) and len(stored) == 16:
            matrix = np.array(stored, dtype=np.float32).reshape(4, 4)
            return TransformationMatrix.from_matrix(matrix)
        z_offset = qsettings.value("z_offset", _DEFAULT_Z_OFFSET_MM, type=int)
        transform = TransformationMatrix()
        transform.translation[2] = -float(z_offset)
        return transform
    except (ValueError, TypeError):
        transform = TransformationMatrix()
        transform.translation[2] = -float(_DEFAULT_Z_OFFSET_MM)
        return transform


def _touch_tool_transform_to_list(transform: TransformationMatrix) -> List[float]:
    """Serialize touch tool transform for QSettings.

    Args:
        transform: Touch tool transform to serialize

    Returns:
        The transform as a flat list of 16 floats
    """
    return transform.as_matrix().flatten().tolist()


class TouchConfiguration:

    def __init__(
        self,
        *,
        marker_id: Optional[int] = None,
        marker_dictionary: Optional[str] = None,
        touch_tool_transform: Optional[TransformationMatrix] = None,
    ):
        qsettings = QSettings("Zivid", "HandEyeGUI")
        qsettings.beginGroup("touch_configuration")
        if marker_id is not None:
            self.marker_id = marker_id
        else:
            self.marker_id = qsettings.value("marker_id", 1, type=int)
        if marker_dictionary is not None:
            self.marker_dictionary = marker_dictionary
        else:
            self.marker_dictionary = qsettings.value("marker_dictionary", MarkerDictionary.aruco4x4_250, type=str)
        if touch_tool_transform is not None:
            self.touch_tool_transform = touch_tool_transform
        else:
            self.touch_tool_transform = _touch_tool_transform_from_qsettings(qsettings)
        qsettings.endGroup()

    def save_choice(self) -> None:
        qsettings = QSettings("Zivid", "HandEyeGUI")
        qsettings.beginGroup("touch_configuration")
        qsettings.setValue("marker_id", self.marker_id)
        qsettings.setValue("marker_dictionary", self.marker_dictionary)
        qsettings.setValue(_TOUCH_TOOL_TRANSFORM_KEY, _touch_tool_transform_to_list(self.touch_tool_transform))
        qsettings.endGroup()

    def __str__(self):
        return (
            f"TouchConfiguration(marker_id={self.marker_id}, marker_dictionary={self.marker_dictionary}, "
            f"touch_tool_transform=<4x4>)"
        )


class TouchConfigurationWidget(QWidget):
    def __init__(
        self,
        initial_touch_configuration: TouchConfiguration = TouchConfiguration(),
        *,
        initial_rotation_information: Optional[RotationInformation] = None,
        eye_in_hand: bool = True,
    ):
        super().__init__()
        self.touch_configuration = initial_touch_configuration
        rotation_info = initial_rotation_information or RotationInformation()

        self.marker_id_selection = QSpinBox()
        self.marker_id_selection.setRange(
            0, MarkerDictionary.marker_count(self.touch_configuration.marker_dictionary) - 1
        )
        self.marker_id_selection.setValue(self.touch_configuration.marker_id)
        self.marker_id_selection.setObjectName("Touch-marker_id_selection")
        self.marker_dictionary_selection = QComboBox()
        self.marker_dictionary_selection.addItems(MarkerDictionary.valid_values())
        self.marker_dictionary_selection.setCurrentText(self.touch_configuration.marker_dictionary)
        self.marker_dictionary_selection.setObjectName("Touch-marker_dictionary_selection")

        self.z_offset_spinbox = QDoubleSpinBox()
        self.z_offset_spinbox.setRange(-10000, 10000)
        self.z_offset_spinbox.setDecimals(1)
        self.z_offset_spinbox.setSuffix(" mm")
        self.z_offset_spinbox.setValue(-self.touch_configuration.touch_tool_transform.translation[2])
        self.z_offset_spinbox.setObjectName("Touch-z_offset")

        self.touch_tool_pose_widget = PoseWidget(
            title="Touch Tool Transform",
            initial_rotation_information=rotation_info,
            eye_in_hand=eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_transformation_matrix=self.touch_configuration.touch_tool_transform,
            descriptive_image_paths=None,
        )
        self.touch_tool_pose_widget.setVisible(False)

        marker_list_layout = QFormLayout()
        marker_list_layout.addRow("Marker to touch:", self.marker_id_selection)
        marker_list_layout.addRow("Marker dictionary:", self.marker_dictionary_selection)
        marker_list_layout.addRow("Z offset:", self.z_offset_spinbox)

        layout = QVBoxLayout()
        layout.addLayout(marker_list_layout)
        layout.addWidget(self.touch_tool_pose_widget)
        self.setLayout(layout)

        self.marker_id_selection.valueChanged.connect(self.on_marker_id_changed)
        self.marker_dictionary_selection.currentIndexChanged.connect(self.on_marker_dictionary_changed)
        self.z_offset_spinbox.valueChanged.connect(self._on_z_offset_changed)
        self.touch_tool_pose_widget.pose_updated.connect(self._on_touch_tool_pose_updated)

    def _on_z_offset_changed(self):
        transform = self.touch_configuration.touch_tool_transform
        transform.translation[2] = -self.z_offset_spinbox.value()
        self.touch_tool_pose_widget.set_transformation_matrix(transform)

    def _on_touch_tool_pose_updated(self):
        self.touch_configuration.touch_tool_transform = self.touch_tool_pose_widget.get_transformation_matrix()
        with QSignalBlocker(self.z_offset_spinbox):
            self.z_offset_spinbox.setValue(-self.touch_configuration.touch_tool_transform.translation[2])

    def toggle_advanced_view(self, advanced: bool):
        self.z_offset_spinbox.setVisible(not advanced)
        self.touch_tool_pose_widget.setVisible(advanced)

    def on_marker_id_changed(self) -> None:
        self.touch_configuration.marker_id = self.marker_id_selection.value()

    def on_marker_dictionary_changed(self) -> None:
        self.touch_configuration.marker_dictionary = self.marker_dictionary_selection.currentText()
        self.touch_configuration.marker_id = self.marker_id_selection.value()
        if self.touch_configuration.marker_id > MarkerDictionary.marker_count(
            self.touch_configuration.marker_dictionary
        ):
            self.touch_configuration.marker_id = 0
            self.marker_id_selection.setValue(self.touch_configuration.marker_id)
        self.marker_id_selection.setRange(
            0, MarkerDictionary.marker_count(self.touch_configuration.marker_dictionary) - 1
        )

    def set_rotation_format(self, rotation_information: RotationInformation) -> None:
        self.touch_tool_pose_widget.set_rotation_format(rotation_information)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.touch_configuration.save_choice()
        return super().closeEvent(a0)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = [self.marker_id_selection, self.marker_dictionary_selection]
        widgets.extend(self.touch_tool_pose_widget.get_tab_widgets_in_order())
        return widgets
