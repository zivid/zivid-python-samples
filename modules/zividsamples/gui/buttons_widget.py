from typing import List, Optional

import zivid
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QCheckBox, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from zividsamples.gui.hand_eye_configuration import HandEyeConfiguration


class CameraButtonsWidget(QWidget):
    connect_button_clicked = pyqtSignal()
    capture_button_clicked = pyqtSignal()

    def __init__(
        self,
        capture_button_text="Capture",
        parent=None,
    ):
        super().__init__(parent)

        # Define buttons
        self.connect_button = QPushButton("Connect")
        self.connect_button.setCheckable(True)
        self.connect_button.setStyleSheet("")
        self.connect_button.setObjectName("Camera-connect_button")
        self.capture_button = QPushButton(capture_button_text)
        self.capture_button.setCheckable(True)
        self.capture_button.setEnabled(False)
        self.capture_button.setObjectName("Camera-capture_button")

        self.information_label = QLabel()
        self.information_label.hide()

        # Connect signals
        self.capture_button.clicked.connect(self.on_capture_button_clicked)
        self.connect_button.clicked.connect(self.on_connect_button_clicked)

        # Add buttons to layout
        capture_group_box = QGroupBox("Camera")
        capture_group_box_layout = QVBoxLayout()
        capture_group_box.setLayout(capture_group_box_layout)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.connect_button)
        self.buttons_layout.addWidget(self.capture_button)
        capture_group_box_layout.addLayout(self.buttons_layout)
        capture_group_box_layout.addWidget(self.information_label)

        layout = QHBoxLayout()
        layout.addWidget(capture_group_box)

        self.setLayout(layout)

    def on_capture_button_clicked(self):
        self.capture_button.setChecked(True)
        self.capture_button.setStyleSheet("background-color: yellow;")
        QApplication.processEvents()
        self.capture_button_clicked.emit()
        self.capture_button.setChecked(False)
        self.capture_button.setStyleSheet("")

    def on_connect_button_clicked(self):
        self.connect_button.setChecked(True)
        self.connect_button.setStyleSheet("background-color: yellow;")
        QApplication.processEvents()
        self.connect_button_clicked.emit()

    def set_connection_status(self, camera: Optional[zivid.Camera]):
        if camera is None:
            self.connect_button.setText("Connect")
            self.connect_button.setChecked(False)
            self.connect_button.setStyleSheet("")
            self.capture_button.setEnabled(False)
        else:
            if camera.state.connected:
                self.connect_button.setText(f"Connected to {camera.info.model_name} ({camera.info.serial_number})")
            else:
                self.connect_button.setText(f"Disconnected ({camera.state.status}) (click to re-connect)")
            self.connect_button.setChecked(camera.state.connected)
            self.connect_button.setStyleSheet("background-color: green;" if camera.state.connected else "")
            self.capture_button.setEnabled(camera.state.connected)

    def set_information(self, text: str):
        if text == "":
            self.information_label.hide()
        else:
            self.information_label.show()
        self.information_label.setText(text)

    def disable_buttons(self):
        self.connect_button.setEnabled(False)
        self.capture_button.setEnabled(False)

    def enable_buttons(self):
        self.connect_button.setEnabled(True)
        self.capture_button.setEnabled(True)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        return [self.connect_button, self.capture_button]


class HandEyeCalibrationButtonsWidget(QWidget):
    use_data_button_clicked = pyqtSignal()
    calibrate_button_clicked = pyqtSignal()
    use_fixed_objects_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Define buttons
        self.use_data_button = QPushButton("Use Data")
        self.use_data_button.setObjectName("HandEye-use_data_button")
        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.setObjectName("HandEye-calibrate_button")
        self.use_fixed_objects_checkbox = QCheckBox("Fixed Objects - for low DOF systems")
        self.use_fixed_objects_checkbox.setObjectName("HandEye-fixed_objects_checkbox")

        # Connect signals
        self.use_data_button.clicked.connect(self.on_use_data_button_clicked)
        self.calibrate_button.clicked.connect(self.on_calibrate_button_clicked)
        self.use_fixed_objects_checkbox.toggled.connect(self.on_use_fixed_objects_toggled)

        # Add buttons to layout
        calibrate_group_box = QGroupBox("Calibrate")
        calibrate_group_box_layout = QHBoxLayout()
        calibrate_group_box.setLayout(calibrate_group_box_layout)

        calibrate_group_box_layout.addWidget(self.use_data_button)
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

    def on_use_data_button_clicked(self):
        self.use_data_button.setStyleSheet("background-color: yellow;")
        QApplication.processEvents()
        self.use_data_button_clicked.emit()
        self.use_data_button.setStyleSheet("")

    def on_use_fixed_objects_toggled(self, checked: bool):
        self.use_fixed_objects_toggled.emit(checked)

    def disable_buttons(self):
        self.use_data_button.setEnabled(False)
        self.calibrate_button.setEnabled(False)

    def enable_buttons(self):
        self.use_data_button.setEnabled(True)
        self.calibrate_button.setEnabled(True)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        return [self.use_data_button, self.calibrate_button]


class HandEyeVerificationButtonsWidget(QWidget):
    project_button_clicked = pyqtSignal()

    def __init__(
        self,
        hand_eye_configuration: HandEyeConfiguration,
        parent=None,
    ):
        super().__init__(parent)

        # Define buttons
        self.project_button = QPushButton()
        self.project_button.setCheckable(True)
        self.project_button.setDisabled(True)
        self.on_hand_eye_configuration_updated(hand_eye_configuration)

        # Connect signals
        self.project_button.clicked.connect(self.on_project_button_clicked)

        # Add buttons to layout
        verify_group_box = QGroupBox("Projection")
        verify_group_box_layout = QHBoxLayout()
        verify_group_box.setLayout(verify_group_box_layout)

        verify_group_box_layout.addWidget(self.project_button)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(verify_group_box)

        self.setLayout(buttons_layout)

    def on_project_button_clicked(self):
        self.project_button_clicked.emit()
        if self.project_button.isChecked():
            self.project_button.setStyleSheet("background-color: green;")
        else:
            self.project_button.setStyleSheet("")

    def on_hand_eye_configuration_updated(self, hand_eye_configuration: HandEyeConfiguration):
        self.project_button.setText(f"Project on {hand_eye_configuration.calibration_object.name}")
