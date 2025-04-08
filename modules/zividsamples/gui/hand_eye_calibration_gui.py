"""
Hand-Eye Calibration GUI


Note: This script requires the Zivid Python API and PyQt5 to be installed.

"""

import copy
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import zivid
from nptyping import NDArray, Shape, UInt8
from PyQt5.QtCore import QSignalBlocker, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget
from zivid.experimental.hand_eye_low_dof import calibrate_eye_in_hand_low_dof, calibrate_eye_to_hand_low_dof
from zividsamples.gui.buttons_widget import HandEyeCalibrationButtonsWidget
from zividsamples.gui.cv2_handler import CV2Handler
from zividsamples.gui.detection_visualization import DetectionVisualizationWidget
from zividsamples.gui.hand_eye_configuration import CalibrationObject, HandEyeConfiguration
from zividsamples.gui.marker_widget import MarkerConfiguration
from zividsamples.gui.pose_pair_selection_widget import PosePair, PosePairSelectionWidget, directory_has_pose_pair_data
from zividsamples.gui.pose_widget import PoseWidget, PoseWidgetDisplayMode
from zividsamples.gui.robot_control import RobotTarget
from zividsamples.gui.rotation_format_configuration import RotationInformation
from zividsamples.gui.set_fixed_objects import FixedCalibrationObjectsData, set_fixed_objects
from zividsamples.gui.settings_selector import SettingsPixelMappingIntrinsics
from zividsamples.gui.show_yaml_dialog import show_yaml_dialog
from zividsamples.transformation_matrix import TransformationMatrix


class HandEyeCalibrationGUI(QWidget):
    data_directory: Path
    use_robot: bool
    hand_eye_configuration: HandEyeConfiguration
    marker_configuration: MarkerConfiguration = MarkerConfiguration()
    pose_pair: PosePair
    has_detection_result: bool = False
    has_confirmed_robot_pose: bool = False
    checkerboard_pose_in_camera_frame: Optional[TransformationMatrix] = None
    minimum_pose_pairs_for_calibration: int = 6
    calibration_finished = pyqtSignal(TransformationMatrix)
    instructions_updated: pyqtSignal = pyqtSignal()
    description: List[str]
    fixed_objects: FixedCalibrationObjectsData
    instruction_steps: Dict[str, bool]

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        data_directory: Path,
        use_robot: bool,
        hand_eye_configuration: HandEyeConfiguration,
        marker_configuration: MarkerConfiguration,
        cv2_handler: CV2Handler,
        initial_rotation_information: RotationInformation,
        parent=None,
    ):
        super().__init__(parent)

        self.description = [
            "In order to calibrate the hand-eye transformation we need to collect data from the robot and the camera. "
            + "We need to capture images of the calibration object from the camera and record the robot pose at the same time. "
            + "Once we have enough data, we can calibrate the hand-eye transformation. "
            + "We recommend 10 to 20 pairs.",
            "The steps above will guide you through the process.",
        ]

        self.data_directory = data_directory
        self.use_robot = use_robot
        self.hand_eye_configuration = hand_eye_configuration
        self.marker_configuration = marker_configuration
        self.fixed_objects = FixedCalibrationObjectsData(
            hand_eye_configuration=self.hand_eye_configuration, marker_configuration=self.marker_configuration
        )

        self.cv2_handler = cv2_handler

        self.create_widgets(initial_rotation_information=initial_rotation_information)
        self.setup_layout()
        self.connect_signals()
        self.update_instructions(
            has_detection_result=self.has_detection_result,
            robot_pose_confirmed=self.has_confirmed_robot_pose,
            used_data=False,
            calibrated=False,
        )

    def create_widgets(self, initial_rotation_information: RotationInformation):
        self.robot_pose_widget = PoseWidget.Robot(
            self.data_directory / "robot_pose.yaml",
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.robot_pose_widget.setObjectName("HE-Calibration-robot_pose_widget")
        self.confirm_robot_pose_button = QPushButton("Confirm Robot Pose")
        self.confirm_robot_pose_button.setCheckable(True)
        self.confirm_robot_pose_button.setVisible(not self.use_robot)
        self.confirm_robot_pose_button.setObjectName("HE-Calibration-confirm_robot_pose_button")
        self.detection_visualization_widget = DetectionVisualizationWidget(
            hand_eye_configuration=self.hand_eye_configuration
        )
        self.pose_pair_selection_widget = PosePairSelectionWidget(directory=self.data_directory)
        self.pose_pair_selection_widget.setVisible(False)
        self.hand_eye_calibration_buttons = HandEyeCalibrationButtonsWidget()
        self.hand_eye_calibration_buttons.use_data_button.setEnabled(False)
        self.hand_eye_calibration_buttons.calibrate_button.setEnabled(False)
        self.hand_eye_calibration_buttons.setObjectName("HE-Calibration-hand_eye_calibration_buttons")

    def setup_layout(self):
        layout = QVBoxLayout()
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        center_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        confirm_robot_pose_layout = QHBoxLayout()
        confirm_robot_pose_layout.addStretch()
        confirm_robot_pose_layout.addWidget(self.confirm_robot_pose_button)

        left_panel.addWidget(self.robot_pose_widget)
        left_panel.addLayout(confirm_robot_pose_layout)
        left_panel.addWidget(self.detection_visualization_widget)
        right_panel.addWidget(self.pose_pair_selection_widget)
        center_layout.addLayout(left_panel)
        center_layout.addLayout(right_panel)
        layout.addLayout(center_layout)

        bottom_layout.addWidget(self.hand_eye_calibration_buttons)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def connect_signals(self):
        self.hand_eye_calibration_buttons.use_data_button_clicked.connect(self.on_use_data_button_clicked)
        self.hand_eye_calibration_buttons.calibrate_button_clicked.connect(self.on_calibrate_button_clicked)
        self.hand_eye_calibration_buttons.use_fixed_objects_toggled.connect(self.on_use_fixed_objects_toggled)
        self.confirm_robot_pose_button.clicked.connect(self.on_confirm_robot_pose_button_clicked)
        self.robot_pose_widget.pose_updated.connect(self.on_robot_pose_manually_updated)
        self.pose_pair_selection_widget.pose_pair_clicked.connect(self.on_pose_pair_clicked)
        self.pose_pair_selection_widget.pose_pairs_updated.connect(self.on_pose_pairs_update)

    def update_instructions(
        self, has_detection_result: bool, robot_pose_confirmed: bool, used_data: bool, calibrated: bool
    ):
        self.has_confirmed_robot_pose = robot_pose_confirmed
        self.has_detection_result = has_detection_result and self.has_confirmed_robot_pose
        minimum_captures_to_go = (
            self.minimum_pose_pairs_for_calibration - self.pose_pair_selection_widget.number_of_active_pose_pairs()
        )
        self.instruction_steps = {}
        if self.use_robot:
            self.instruction_steps[
                "Move Robot (click 'Move to next target', 'Home' or Disconnect→manually move robot→Connect)"
            ] = self.has_confirmed_robot_pose
        else:
            self.instruction_steps["Confirm Robot Pose"] = self.has_confirmed_robot_pose
        if minimum_captures_to_go > 0:
            self.instruction_steps[f"Capture (at least {minimum_captures_to_go} more)"] = self.has_detection_result
        else:
            self.instruction_steps["Capture"] = self.has_detection_result
        self.instruction_steps["Use data"] = used_data
        if minimum_captures_to_go <= 0:
            self.instruction_steps["Calibrate"] = calibrated
        self.instructions_updated.emit()
        self.hand_eye_calibration_buttons.use_data_button.setEnabled(
            self.has_detection_result and self.has_confirmed_robot_pose
        )
        self.confirm_robot_pose_button.setStyleSheet(
            "background-color: green;" if self.has_confirmed_robot_pose else ""
        )
        self.confirm_robot_pose_button.setChecked(self.has_confirmed_robot_pose)

    def hand_eye_configuration_update(self, hand_eye_configuration: HandEyeConfiguration):
        self.hand_eye_configuration = hand_eye_configuration
        self.detection_visualization_widget.on_hand_eye_configuration_updated(self.hand_eye_configuration)
        self.robot_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.minimum_pose_pairs_for_calibration = (
            4 if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard else 6
        )
        self.fixed_objects.update_hand_eye_configuration(self.hand_eye_configuration)

    def marker_configuration_update(self, marker_configuration: MarkerConfiguration):
        self.marker_configuration = marker_configuration
        self.fixed_objects.update_marker_configuration(self.marker_configuration)

    def rotation_format_update(self, rotation_format: RotationInformation):
        self.robot_pose_widget.set_rotation_format(rotation_format)

    def on_select_fixed_objects_action_triggered(self):
        updated_fixed_objects = set_fixed_objects(self.fixed_objects, self.robot_pose_widget.rotation_information)
        if updated_fixed_objects is not None:
            self.fixed_objects = updated_fixed_objects

    def toggle_advanced_view(self, checked):
        self.robot_pose_widget.toggle_advanced_section(checked)

    def toggle_use_robot(self, use_robot: bool):
        self.use_robot = use_robot
        self.confirm_robot_pose_button.setVisible(not self.use_robot)
        self.update_instructions(
            has_detection_result=self.has_detection_result,
            robot_pose_confirmed=self.has_confirmed_robot_pose,
            used_data=False,
            calibrated=False,
        )

    def on_start_auto_run(self) -> bool:
        if self.pose_pair_selection_widget.number_of_active_pose_pairs() == 0:
            return True
        reply = QMessageBox.question(
            self,
            "Clear Captures",
            "This will clear all current captures. Do you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.pose_pair_selection_widget.clear()
            return True
        return False

    def on_pose_pair_clicked(self, pose_pair: PosePair):
        self.pose_pair = pose_pair
        self.robot_pose_widget.set_transformation_matrix(self.pose_pair.robot_pose)
        self.detection_visualization_widget.set_image(self.pose_pair.qimage_rgba)

    def on_pose_pairs_update(self, number_of_pose_pairs: int):
        self.hand_eye_calibration_buttons.calibrate_button.setEnabled(
            number_of_pose_pairs >= self.minimum_pose_pairs_for_calibration
        )
        self.pose_pair_selection_widget.setVisible(number_of_pose_pairs > 0)

    def process_capture(self, frame: zivid.Frame, rgba: NDArray[Shape["N, M, 4"], UInt8], settings: SettingsPixelMappingIntrinsics):  # type: ignore
        try:
            detection_result = (
                zivid.calibration.detect_calibration_board(frame)
                if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard
                else zivid.calibration.detect_markers(
                    frame,
                    self.marker_configuration.id_list,
                    self.marker_configuration.dictionary,
                )
            )
            if not detection_result.valid():
                if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
                    raise RuntimeError(f"Failed to detect Checkerboard. {detection_result.status_description()}")
                raise RuntimeError("Failed to detect Markers.")
            rgb = rgba[:, :, :3].copy().astype(np.uint8)
            camera_pose = None
            if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
                pose = detection_result.pose()
                camera_pose = TransformationMatrix.from_matrix(np.asarray(pose.to_matrix()))
                rgba[:, :, :3] = self.cv2_handler.draw_projected_axis_cross(settings.intrinsics, rgb, camera_pose)
            else:
                detected_markers = detection_result.detected_markers()
                all_marker_ids = [marker.identifier for marker in detected_markers]
                unique_markers = set(all_marker_ids)
                if len(unique_markers) != len(all_marker_ids):
                    raise RuntimeError("Detected duplicate markers")  # TODO: list duplicated IDs
                rgba[:, :, :3] = self.cv2_handler.draw_detected_markers(detected_markers, rgb, settings.pixel_mapping)
            self.detection_visualization_widget.set_rgba_image(rgba)
            self.pose_pair = PosePair(
                robot_pose=copy.deepcopy(self.robot_pose_widget.transformation_matrix),
                camera_frame=frame,
                qimage_rgba=self.detection_visualization_widget.get_qimage(
                    self.hand_eye_configuration.calibration_object
                ),
                detection_result=detection_result,
                camera_pose=copy.deepcopy(camera_pose),
            )
            self.update_instructions(
                has_detection_result=True,
                robot_pose_confirmed=self.has_confirmed_robot_pose,
                used_data=False,
                calibrated=False,
            )
        except RuntimeError as ex:
            self.detection_visualization_widget.set_error_message(str(ex))
            raise ex

    def on_use_data_button_clicked(self):
        self.pose_pair_selection_widget.add_pose_pair(self.pose_pair)
        self.update_instructions(
            has_detection_result=False,
            robot_pose_confirmed=False,
            used_data=True,
            calibrated=False,
        )

    def on_use_fixed_objects_toggled(self, checked: bool):
        if checked:
            updated_fixed_objects = set_fixed_objects(self.fixed_objects, self.robot_pose_widget.rotation_information)
            if updated_fixed_objects is None:
                self.hand_eye_calibration_buttons.use_fixed_objects_checkbox.setChecked(False)
            else:
                self.hand_eye_calibration_buttons.use_fixed_objects_checkbox.setChecked(self.fixed_objects.has_data())
                self.fixed_objects = updated_fixed_objects

    def on_calibrate_button_clicked(self):
        try:
            detection_results = self.pose_pair_selection_widget.get_detection_results()
            calibration_result = (
                (
                    calibrate_eye_in_hand_low_dof(detection_results, self.fixed_objects.to_fixed_calibration_objects())
                    if self.hand_eye_calibration_buttons.use_fixed_objects_checkbox.isChecked()
                    else zivid.calibration.calibrate_eye_in_hand(detection_results)
                )
                if self.hand_eye_configuration.eye_in_hand
                else (
                    calibrate_eye_to_hand_low_dof(detection_results, self.fixed_objects.to_fixed_calibration_objects())
                    if self.hand_eye_calibration_buttons.use_fixed_objects_checkbox.isChecked()
                    else zivid.calibration.calibrate_eye_to_hand(detection_results)
                )
            )
            if calibration_result is not None and calibration_result.valid():
                print("Hand-Eye calibration OK")
                print(f"Result:\n{calibration_result}")
                hand_eye_transform = calibration_result.transform()
                hand_eye_transform_path = self.data_directory / "hand_eye_transform.yaml"
                zivid.Matrix4x4(hand_eye_transform).save(hand_eye_transform_path)
                self.pose_pair_selection_widget.set_residuals(calibration_result.residuals())
                show_yaml_dialog(hand_eye_transform_path, "Hand Eye Calibration Transform")
                self.update_instructions(
                    has_detection_result=False,
                    robot_pose_confirmed=False,
                    used_data=False,
                    calibrated=True,
                )
                self.calibration_finished.emit(TransformationMatrix.from_matrix(hand_eye_transform))
            else:
                raise RuntimeError()
        except RuntimeError as ex:
            print(f"Failed to calibrate eye to hand: {ex}")
            QMessageBox.critical(self, "Hand-Eye Calibration Error", str(ex))
            self.calibration_finished.emit(TransformationMatrix())

    def confirm_robot_pose(self, confirmed: bool = True):
        self.update_instructions(
            has_detection_result=False,
            robot_pose_confirmed=confirmed,
            used_data=False,
            calibrated=False,
        )

    def on_confirm_robot_pose_button_clicked(self, checked: bool):
        self.confirm_robot_pose(checked)

    def on_robot_pose_manually_updated(self):
        self.confirm_robot_pose(False)

    def on_actual_pose_updated(self, robot_target: RobotTarget):
        self.has_detection_result = False
        self.confirm_robot_pose(True)
        with QSignalBlocker(self.robot_pose_widget):
            self.robot_pose_widget.set_transformation_matrix(robot_target.pose)

    def on_target_pose_updated(self, robot_target: RobotTarget):
        self.robot_pose_widget.set_transformation_matrix(robot_target.pose)

    def set_save_directory(self, data_directory: Path):
        if self.data_directory != data_directory:
            if directory_has_pose_pair_data(data_directory):
                message_box = QMessageBox()
                message_box.setText("Directory already contains pose pair data. Overwrite?")
                message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                message_box.setDefaultButton(QMessageBox.No)
                if message_box.exec() == QMessageBox.No:
                    return
            self.data_directory = data_directory
            self.pose_pair_selection_widget.set_directory(self.data_directory)

    def set_load_directory(self, data_directory: Path):
        self.data_directory = Path(data_directory)
        self.pose_pair_selection_widget.set_directory(self.data_directory)
        self.pose_pair_selection_widget.load_pose_pairs(
            calibration_object=self.hand_eye_configuration.calibration_object,
            marker_configuration=self.marker_configuration,
        )

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        widgets.extend(self.robot_pose_widget.get_tab_widgets_in_order())
        if self.confirm_robot_pose_button.isVisible():
            widgets.append(self.confirm_robot_pose_button)
        widgets.extend(self.hand_eye_calibration_buttons.get_tab_widgets_in_order())
        return widgets
