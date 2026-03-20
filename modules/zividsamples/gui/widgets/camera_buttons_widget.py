from typing import List, Optional

import zivid
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


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

    def disable_buttons(self, capture_tooltip: str = ""):
        self.connect_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        self.capture_button.setToolTip(capture_tooltip)

    def enable_buttons(self):
        self.connect_button.setEnabled(True)
        self.capture_button.setEnabled(True)
        self.capture_button.setToolTip("")

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        return [self.connect_button, self.capture_button]
