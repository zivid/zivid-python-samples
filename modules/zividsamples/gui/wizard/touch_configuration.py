"""
Touch Configuration

Note: This script requires PyQt5 to be installed.

"""

from typing import List, Optional

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QSpinBox,
    QWidget,
)
from zivid.calibration import MarkerDictionary


class TouchConfiguration:

    def __init__(
        self,
        *,
        marker_id: Optional[int] = None,
        marker_dictionary: Optional[str] = None,
        z_offset: Optional[int] = None,
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
        if z_offset is not None:
            self.z_offset = z_offset
        else:
            self.z_offset = qsettings.value("z_offset", 300, type=int)
        qsettings.endGroup()

    def save_choice(self):
        qsettings = QSettings("Zivid", "HandEyeGUI")
        qsettings.beginGroup("touch_configuration")
        qsettings.setValue("marker_id", self.marker_id)
        qsettings.setValue("marker_dictionary", self.marker_dictionary)
        qsettings.setValue("z_offset", self.z_offset)
        qsettings.endGroup()

    def __str__(self):
        return f"TouchConfiguration(marker_id={self.marker_id}, marker_dictionary={self.marker_dictionary}, z_offset={self.z_offset})"


class TouchConfigurationWidget(QWidget):
    def __init__(self, initial_touch_configuration: TouchConfiguration = TouchConfiguration()):
        super().__init__()
        self.touch_configuration = initial_touch_configuration

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
        self.z_offset = QSpinBox()
        self.z_offset.setRange(0, 400)
        self.z_offset.setValue(self.touch_configuration.z_offset)
        self.z_offset.setSuffix(" mm")
        self.z_offset.setObjectName("Touch-z_offset")
        marker_list_layout = QFormLayout()
        marker_list_layout.addRow("Marker to touch:", self.marker_id_selection)
        marker_list_layout.addRow("Marker dictionary:", self.marker_dictionary_selection)
        marker_list_layout.addRow("Touch tool length:", self.z_offset)

        self.setLayout(marker_list_layout)

        self.marker_id_selection.valueChanged.connect(self.on_marker_id_changed)
        self.marker_dictionary_selection.currentIndexChanged.connect(self.on_marker_dictionary_changed)
        self.z_offset.valueChanged.connect(self.on_z_offset_changed)

    def on_marker_id_changed(self):
        self.touch_configuration.marker_id = self.marker_id_selection.value()

    def on_marker_dictionary_changed(self):
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

    def on_z_offset_changed(self):
        self.touch_configuration.z_offset = self.z_offset.value()

    def closeEvent(self, a0):
        self.touch_configuration.save_choice()
        return super().closeEvent(a0)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        return [self.marker_id_selection, self.marker_dictionary_selection, self.z_offset]
