from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import QFormLayout, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from zivid.experimental.calibration import CameraCorrection
from zividsamples.gui.qt_application import create_vertical_line


class InfieldCorrectionResultWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        self.infield_result_container = QWidget()

        self.infield_result_group_box = QGroupBox("Expected Infield Correction Results")

        self.expected_trueness_label = QLabel("NA")
        self.z_min_label = QLabel("NA")
        self.z_max_label = QLabel("NA")
        self.current_correction_label = QLabel("")

    def setup_layout(self):
        infield_correction_result_form = QFormLayout()
        infield_input_group_box_layout = QHBoxLayout()
        infield_input_group_box_layout.addLayout(infield_correction_result_form)
        infield_correction_result_form.addRow("Expected Trueness After Correction", self.expected_trueness_label)
        infield_correction_result_form.addRow("Z Min", self.z_min_label)
        infield_correction_result_form.addRow("Z Max", self.z_max_label)
        infield_input_group_box_layout.addStretch()
        infield_input_group_box_layout.addWidget(create_vertical_line())
        infield_input_group_box_layout.addStretch()
        infield_input_group_box_layout.addWidget(self.current_correction_label)
        self.infield_result_group_box.setLayout(infield_input_group_box_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.infield_result_group_box)
        self.setLayout(layout)

    def update_result(self, correction: Optional[CameraCorrection] = None):
        if correction:
            accuracy_estimate = correction.accuracy_estimate()
            self.expected_trueness_label.setText(f"{accuracy_estimate.dimension_accuracy() * 100:.3f}%")
            self.z_min_label.setText(f"{accuracy_estimate.z_min():4.0f} mm")
            self.z_max_label.setText(f"{accuracy_estimate.z_max():4.0f} mm")
        else:
            self.expected_trueness_label.setText("NA")
            self.z_min_label.setText("NA")
            self.z_max_label.setText("NA")

    def set_current_correction(self, timestamp: Optional[datetime] = None):
        if timestamp is None:
            self.current_correction_label.setText("No correction applied.")
        else:
            self.current_correction_label.setText(
                f"Last correction applied:\n{timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
