from dataclasses import dataclass
from enum import Enum

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)
from zividsamples.gui.qt_application import ZividQtApplication


class CalibrationObject(Enum):
    Checkerboard = (0,)
    Markers = 1


@dataclass
class HandEyeConfiguration:
    eye_in_hand: bool = True
    calibration_object: CalibrationObject = CalibrationObject.Checkerboard


class HandEyeButtonsWidget(QWidget):
    hand_eye_configuration: HandEyeConfiguration
    hand_eye_configuration_updated = pyqtSignal(HandEyeConfiguration)
    calibration_object_selection_active: bool
    eye_in_hand_selection_active: bool

    def __init__(
        self,
        initial_hand_eye_configuration: HandEyeConfiguration,
        show_calibration_object_selection: bool = True,
        show_eye_in_hand_selection: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.hand_eye_configuration = initial_hand_eye_configuration
        self.calibration_object_selection_active = show_calibration_object_selection
        self.eye_in_hand_selection_active = show_eye_in_hand_selection

        if show_eye_in_hand_selection is False and show_calibration_object_selection is False:
            raise ValueError(
                "At least one of `show_eye_in_hand_selection` or `show_calibration_object_selection` must be True"
            )

        # Define buttons
        if self.eye_in_hand_selection_active:
            self.eye_in_hand_radio_button = QRadioButton("Eye-In-Hand")
            self.eye_to_hand_radio_button = QRadioButton("Eye-To-Hand")
            radio_button_group = QButtonGroup()
            radio_button_group.addButton(self.eye_in_hand_radio_button)
            radio_button_group.addButton(self.eye_to_hand_radio_button)
            self.eye_in_hand_radio_button.setChecked(self.hand_eye_configuration.eye_in_hand)

        if self.calibration_object_selection_active:
            self.checkerboard_object_radio_button = QRadioButton("Checkerboard")
            self.marker_objects_radio_button = QRadioButton("Markers")
            self.calibration_object_selection_radio_button_group = QButtonGroup()
            self.calibration_object_selection_radio_button_group.addButton(self.checkerboard_object_radio_button)
            self.calibration_object_selection_radio_button_group.addButton(self.marker_objects_radio_button)
            if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
                self.checkerboard_object_radio_button.setChecked(True)
            else:
                self.marker_objects_radio_button.setChecked(True)

        # Connect signals
        if self.eye_in_hand_selection_active:
            self.eye_in_hand_radio_button.toggled.connect(self.on_eye_in_hand_toggled)
        if self.calibration_object_selection_active:
            self.checkerboard_object_radio_button.toggled.connect(self.on_calibration_object_toggled)

        # Add buttons to layout
        capture_group_box = QGroupBox("Hand-Eye Configuration")
        capture_group_box_layout = QVBoxLayout()
        capture_group_box.setLayout(capture_group_box_layout)

        if self.eye_in_hand_selection_active:
            radio_buttons_layout = QVBoxLayout()
            radio_buttons_layout.addWidget(self.eye_in_hand_radio_button)
            radio_buttons_layout.addWidget(self.eye_to_hand_radio_button)
        if self.calibration_object_selection_active:
            calibration_object_selection_radio_buttons_layout = QVBoxLayout()
            calibration_object_selection_radio_buttons_layout.addWidget(self.checkerboard_object_radio_button)
            calibration_object_selection_radio_buttons_layout.addWidget(self.marker_objects_radio_button)

        buttons_layout = QHBoxLayout()
        if self.eye_in_hand_selection_active:
            buttons_layout.addLayout(radio_buttons_layout)
        if self.calibration_object_selection_active:
            buttons_layout.addLayout(calibration_object_selection_radio_buttons_layout)
        capture_group_box_layout.addLayout(buttons_layout)

        layout = QHBoxLayout()
        layout.addWidget(capture_group_box)

        self.setLayout(layout)

    def set_hand_eye_configuration(self, updated_hand_eye_configuration: HandEyeConfiguration):
        self.checkerboard_object_radio_button.setChecked(
            updated_hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard
        )
        self.eye_in_hand_radio_button.setChecked(updated_hand_eye_configuration.eye_in_hand)

    def update_hand_eye_configuration(self):
        if self.calibration_object_selection_active:
            self.hand_eye_configuration.calibration_object = (
                CalibrationObject.Checkerboard
                if self.checkerboard_object_radio_button.isChecked()
                else CalibrationObject.Markers
            )
        if self.eye_in_hand_selection_active:
            self.hand_eye_configuration.eye_in_hand = self.eye_in_hand_radio_button.isChecked()
        self.hand_eye_configuration_updated.emit(self.hand_eye_configuration)

    def on_eye_in_hand_toggled(self, _: bool):
        self.update_hand_eye_configuration()

    def on_calibration_object_toggled(self, _: bool):
        self.update_hand_eye_configuration()

    def eye_in_hand(self) -> bool:
        return self.hand_eye_configuration.eye_in_hand

    def calibration_object(self) -> CalibrationObject:
        return self.hand_eye_configuration.calibration_object


class HandEyeConfigurationSelection(QDialog):

    def __init__(
        self,
        initial_hand_eye_configuration: HandEyeConfiguration = HandEyeConfiguration(),
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Select Hand-Eye Configuration")

        self.hand_eye_configuration = initial_hand_eye_configuration
        self.hand_eye_buttons = HandEyeButtonsWidget(initial_hand_eye_configuration=initial_hand_eye_configuration)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.hand_eye_buttons)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def accept(self):
        self.hand_eye_configuration = self.hand_eye_buttons.hand_eye_configuration
        super().accept()


def select_hand_eye_configuration(
    initial_hand_eye_configuration: HandEyeConfiguration = HandEyeConfiguration(),
) -> HandEyeConfiguration:
    dialog = HandEyeConfigurationSelection(initial_hand_eye_configuration)
    dialog.exec_()
    return dialog.hand_eye_configuration


if __name__ == "__main__":  # NOLINT
    with ZividQtApplication():
        hand_eye_configuration = select_hand_eye_configuration()
        print(f"Selected settings: {hand_eye_configuration}")
