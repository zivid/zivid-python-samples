from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget
from zividsamples.gui.wizard.hand_eye_configuration import HandEyeConfiguration


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
