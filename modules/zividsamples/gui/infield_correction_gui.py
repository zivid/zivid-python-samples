"""
Hand-Eye Calibration GUI


Note: This script requires the Zivid Python API and PyQt5 to be installed.

"""

import copy
from pathlib import Path
from typing import Callable, Dict, List, Optional

import zivid
from nptyping import NDArray, Shape, UInt8
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget
from zividsamples.gui.cv2_handler import CV2Handler
from zividsamples.gui.detection_visualization import DetectionVisualizationWidget
from zividsamples.gui.hand_eye_configuration import CalibrationObject, HandEyeConfiguration
from zividsamples.gui.infield_correction_data_selection_widget import (
    InfieldCorrectionDataSelectionWidget,
    InfieldCorrectionInputData,
)
from zividsamples.gui.infield_correction_result_widget import InfieldCorrectionResultWidget
from zividsamples.gui.qt_application import styled_link
from zividsamples.gui.robot_configuration import RobotConfiguration
from zividsamples.gui.robot_control import RobotTarget
from zividsamples.gui.rotation_format_configuration import RotationInformation
from zividsamples.gui.settings_selector import SettingsPixelMappingIntrinsics
from zividsamples.gui.tab_with_robot_support import TabWidgetWithRobotSupport
from zividsamples.transformation_matrix import TransformationMatrix


class InfieldCorrectionGUI(TabWidgetWithRobotSupport):
    robot_configuration: RobotConfiguration
    infield_correction_input_data: Optional[InfieldCorrectionInputData] = None
    has_detection_result: bool = False
    applied_correction: bool = False
    hand_eye_configuration: HandEyeConfiguration
    checkerboard_pose_in_camera_frame: Optional[TransformationMatrix] = None
    correction_finished = pyqtSignal(TransformationMatrix)
    instructions_updated: pyqtSignal = pyqtSignal()
    apply_correction_button_clicked: pyqtSignal = pyqtSignal()
    update_projection = pyqtSignal(bool)
    description: List[str]
    instruction_steps: Dict[str, bool]

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        data_directory: Path,
        hand_eye_configuration: HandEyeConfiguration,
        cv2_handler: CV2Handler,
        get_camera: Callable[[], zivid.Camera],
        parent=None,
    ):
        super().__init__(data_directory, parent)

        self.description = [
            "The camera comes pre-calibrated. However, it is possible to add "
            "a correction to the calibration to improve the accuracy of the "
            "hand-eye calibration.",
            f'The tutorial {styled_link("Infield Correction", "https://support.zivid.com/en/latest/academy/camera/infield-correction/guidelines-for-performing-infield-correction.html")} goes into detail on the process.',
            "For each capture of the calibration board, its position in the FOV (Field-of-View) will be listed."
            "The image will also be annotated with an outline of the FOV.",
            "- The center green square indicates the center of the FOV.",
            "- The red square indicates a limit to where the center of the calibration board should be placed.",
            "If you click on 'Project FOV Hint', the same hint will be projected onto the scene. "
            "This hint only applies at this distance, but can be used to make sure you place the calibration "
            "board in a valid location.",
        ]

        self.data_directory = data_directory
        self.hand_eye_configuration = copy.deepcopy(hand_eye_configuration)
        self.hand_eye_configuration.calibration_object = CalibrationObject.Checkerboard

        self.cv2_handler = cv2_handler
        self.get_camera = get_camera

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()
        self.update_instructions(has_detection_result=self.has_detection_result, applied_correction=False)

    def create_widgets(self):
        self.apply_correction_button = QPushButton("Apply Correction")
        self.apply_correction_button.setEnabled(False)
        self.apply_correction_button.setObjectName("InfieldCorrection-apply_correction_button")
        self.project_fov_hint_button = QPushButton("Project FOV Hint")
        self.project_fov_hint_button.setCheckable(True)
        self.project_fov_hint_button.setEnabled(False)
        self.project_fov_hint_button.setObjectName("InfieldCorrection-project_fov_hint_button")
        self.detection_visualization_widget = DetectionVisualizationWidget(
            hand_eye_configuration=self.hand_eye_configuration, hide_descriptive_image=True
        )
        self.infield_input_data_selection_widget = InfieldCorrectionDataSelectionWidget(directory=self.data_directory)
        self.infield_input_data_selection_widget.setVisible(False)
        self.infield_correction_result_widget = InfieldCorrectionResultWidget()

    def setup_layout(self):
        layout = QVBoxLayout()
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        center_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        left_panel.addWidget(self.detection_visualization_widget)
        left_panel.addWidget(self.infield_correction_result_widget)
        right_panel.addWidget(self.infield_input_data_selection_widget)
        center_layout.addLayout(left_panel)
        center_layout.addLayout(right_panel)
        layout.addLayout(center_layout)

        bottom_layout.addWidget(self.apply_correction_button)
        bottom_layout.addWidget(self.project_fov_hint_button)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def connect_signals(self):
        self.apply_correction_button.clicked.connect(self.on_apply_infield_correction_button_clicked)
        self.project_fov_hint_button.clicked.connect(self.on_project_fov_hint_button_clicked)
        self.infield_input_data_selection_widget.infield_input_data_clicked.connect(self.on_infield_input_data_clicked)
        self.infield_input_data_selection_widget.infield_input_data_updated.connect(self.on_infield_input_data_updated)

    def update_instructions(self, has_detection_result: bool, applied_correction: bool):
        self.has_detection_result = has_detection_result
        self.applied_correction = applied_correction
        self.instruction_steps = {}
        self.instruction_steps["Capture"] = self.has_detection_result
        self.instruction_steps["Apply Correction"] = self.applied_correction
        self.instructions_updated.emit()

    def hand_eye_configuration_update(self, hand_eye_configuration: HandEyeConfiguration):
        self.hand_eye_configuration = copy.deepcopy(hand_eye_configuration)
        self.hand_eye_configuration.calibration_object = CalibrationObject.Checkerboard
        self.detection_visualization_widget.on_hand_eye_configuration_updated(self.hand_eye_configuration)

    def rotation_format_update(self, rotation_information: RotationInformation):
        pass

    def robot_configuration_update(self, robot_configuration: RobotConfiguration):
        self.robot_configuration = robot_configuration
        self.update_instructions(
            has_detection_result=self.has_detection_result, applied_correction=self.applied_correction
        )

    def on_actual_pose_updated(self, robot_target: RobotTarget):
        pass

    def on_pending_changes(self):
        self.infield_input_data_selection_widget.update_data_directory(self.data_directory)

    def on_tab_visibility_changed(self, is_current: bool):
        pass

    def on_start_auto_run(self) -> bool:
        if self.infield_input_data_selection_widget.number_of_active_infield_input_data() == 0:
            return True
        reply = QMessageBox.question(
            self,
            "Clear Captures",
            "This will clear all current captures. Do you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.infield_input_data_selection_widget.clear_gui()
            return True
        return False

    def on_infield_input_data_clicked(self, infield_correction_input_data: InfieldCorrectionInputData):
        self.infield_correction_input_data = infield_correction_input_data
        self.project_fov_hint_button.setEnabled(True)
        self.detection_visualization_widget.set_rgba_image(self.infield_correction_input_data.rgba_annotated)

    def on_infield_input_data_updated(self, can_calculate_correction: bool):
        if can_calculate_correction:
            correction_results = self.infield_input_data_selection_widget.get_correction_results()
            self.infield_correction_result_widget.update_result(
                zivid.calibration.compute_camera_correction(correction_results)
            )
            self.apply_correction_button.setText("Apply Correction")
            if self.project_fov_hint_button.isChecked():
                self.update_projection.emit(True)
            self.project_fov_hint_button.setEnabled(True)
        else:
            self.infield_correction_result_widget.update_result()
        self.apply_correction_button.setEnabled(can_calculate_correction)

    def process_capture(self, frame: zivid.Frame, rgba: NDArray[Shape["N, M, 4"], UInt8], settings: SettingsPixelMappingIntrinsics):  # type: ignore
        try:
            detection_result = zivid.calibration.detect_calibration_board(frame)
            if not detection_result.valid():
                raise RuntimeError("Failed to detect checkerboard")
            infield_input = zivid.calibration.InfieldCorrectionInput(detection_result)
            if not infield_input.valid():
                raise RuntimeError(
                    f"Failed to detect checkerboard for infield correction: {infield_input.status_description()}"
                )
            if self.applied_correction:
                raise RuntimeError("Cannot add infield correction data when a correction is already applied.")
            self.infield_input_data_selection_widget.show_as_busy(True)
            self.infield_correction_input_data = InfieldCorrectionInputData(
                camera=self.get_camera(),
                camera_frame=frame,
                rgba=rgba,
                infield_input=infield_input,
                intrinsics=settings.intrinsics,
            )
            self.detection_visualization_widget.set_rgba_image(self.infield_correction_input_data.rgba_annotated)
            self.infield_input_data_selection_widget.add_infield_input_data(self.infield_correction_input_data)
            self.infield_input_data_selection_widget.show_as_busy(False)
            self.update_instructions(has_detection_result=True, applied_correction=False)
        except RuntimeError as ex:
            self.detection_visualization_widget.set_error_message(str(ex))
            self.project_fov_hint_button.setChecked(False)
            self.project_fov_hint_button.setEnabled(False)
            self.update_instructions(has_detection_result=False, applied_correction=False)
            self.on_project_fov_hint_button_clicked()
            raise ex

    def on_apply_infield_correction_button_clicked(self):
        if self.applied_correction:
            self.infield_input_data_selection_widget.clear_gui()
            self.project_fov_hint_button.setChecked(False)
            self.project_fov_hint_button.setEnabled(False)
            self.update_instructions(has_detection_result=False, applied_correction=False)
            self.apply_correction_button.setText("Apply Correction")
        else:
            self.apply_correction_button_clicked.emit()

    def on_project_fov_hint_button_clicked(self):
        self.project_fov_hint_button.setStyleSheet(
            "background-color: green;" if self.project_fov_hint_button.isChecked() else ""
        )
        self.update_projection.emit(self.project_fov_hint_button.isChecked())

    def apply_correction(self, camera: zivid.Camera):
        try:
            correction_results = self.infield_input_data_selection_widget.get_correction_results()
            correction = zivid.calibration.compute_camera_correction(correction_results)
            zivid.calibration.write_camera_correction(camera, correction)
            self.update_instructions(has_detection_result=False, applied_correction=True)
            self.check_correction(camera)
            self.apply_correction_button.setText("Clear captures and restart")
        except RuntimeError as ex:
            print(f"Failed to perform infield correction: {ex}")
            QMessageBox.critical(self, "Infield Correction Error", str(ex))

    def check_correction(self, camera: zivid.Camera):
        if zivid.calibration.has_camera_correction(camera):
            self.infield_correction_result_widget.set_current_correction(
                zivid.calibration.camera_correction_timestamp(camera)
            )
        else:
            self.infield_correction_result_widget.set_current_correction()

    def has_features_to_project(self) -> bool:
        return self.project_fov_hint_button.isChecked() and isinstance(
            self.infield_correction_input_data, InfieldCorrectionInputData
        )

    def generate_projector_image(self, _: zivid.Camera):
        if not isinstance(self.infield_correction_input_data, InfieldCorrectionInputData):
            raise RuntimeError("No infield correction input data available to generate projection image.")
        return self.infield_correction_input_data.projector_image

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        widgets.append(self.apply_correction_button)
        widgets.append(self.project_fov_hint_button)
        return widgets
