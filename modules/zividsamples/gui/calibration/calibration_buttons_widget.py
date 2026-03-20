from typing import List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QCheckBox, QGroupBox, QHBoxLayout, QPushButton, QWidget


class HandEyeCalibrationButtonsWidget(QWidget):
    calibrate_button_clicked = pyqtSignal()
    use_fixed_objects_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Define buttons
        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.setObjectName("HandEye-calibrate_button")
        self.use_fixed_objects_checkbox = QCheckBox("Fixed Objects - for low DOF systems")
        self.use_fixed_objects_checkbox.setObjectName("HandEye-fixed_objects_checkbox")

        # Connect signals
        self.calibrate_button.clicked.connect(self.on_calibrate_button_clicked)
        self.use_fixed_objects_checkbox.toggled.connect(self.on_use_fixed_objects_toggled)

        # Add buttons to layout
        calibrate_group_box = QGroupBox("Calibrate")
        calibrate_group_box_layout = QHBoxLayout()
        calibrate_group_box.setLayout(calibrate_group_box_layout)

        calibrate_group_box_layout.addWidget(self.calibrate_button)
        calibrate_group_box_layout.addWidget(self.use_fixed_objects_checkbox)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(calibrate_group_box)

        self.setLayout(buttons_layout)

    def on_calibrate_button_clicked(self):
        self.calibrate_button.setStyleSheet("background-color: yellow;")
        QApplication.processEvents()
        self.calibrate_button_clicked.emit()
        self.calibrate_button.setStyleSheet("")

    def on_use_fixed_objects_toggled(self, checked: bool):
        self.use_fixed_objects_toggled.emit(checked)

    def disable_buttons(self):
        self.calibrate_button.setEnabled(False)

    def enable_buttons(self):
        self.calibrate_button.setEnabled(True)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        return [self.calibrate_button]
