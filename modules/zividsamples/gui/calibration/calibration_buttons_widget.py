from typing import List, Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HandEyeCalibrationButtonsWidget(QWidget):
    calibrate_button_clicked = pyqtSignal()
    use_fixed_objects_toggled = pyqtSignal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.setObjectName("HandEye-calibrate_button")
        self.use_fixed_objects_checkbox = QCheckBox("Fixed Objects - for low DOF systems")
        self.use_fixed_objects_checkbox.setObjectName("HandEye-fixed_objects_checkbox")
        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setVisible(False)

        self.calibrate_button.clicked.connect(self.on_calibrate_button_clicked)
        self.use_fixed_objects_checkbox.toggled.connect(self.on_use_fixed_objects_toggled)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self.calibrate_button)
        buttons_row.addWidget(self.use_fixed_objects_checkbox)

        calibrate_group_box = QGroupBox("Calibrate")
        calibrate_group_box_layout = QVBoxLayout()
        calibrate_group_box.setLayout(calibrate_group_box_layout)
        calibrate_group_box_layout.addLayout(buttons_row)
        calibrate_group_box_layout.addWidget(self._status_label)

        outer_layout = QHBoxLayout()
        outer_layout.addWidget(calibrate_group_box)
        self.setLayout(outer_layout)

    def on_calibrate_button_clicked(self) -> None:
        self.calibrate_button.setEnabled(False)
        self.calibrate_button.setStyleSheet("background-color: #C07800; color: white;")
        QApplication.processEvents()
        self.calibrate_button_clicked.emit()
        self.calibrate_button.setStyleSheet("")
        self.calibrate_button.setEnabled(True)

    def on_use_fixed_objects_toggled(self, checked: bool) -> None:
        self.use_fixed_objects_toggled.emit(checked)

    def set_calibration_status(self, style: str, message: str) -> None:
        self._status_label.setStyleSheet(style)
        self._status_label.setText(message)
        self._status_label.setVisible(True)

    def hide_calibration_status(self) -> None:
        self._status_label.setVisible(False)

    def disable_buttons(self) -> None:
        self.calibrate_button.setEnabled(False)

    def enable_buttons(self) -> None:
        self.calibrate_button.setEnabled(True)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        return [self.calibrate_button]
