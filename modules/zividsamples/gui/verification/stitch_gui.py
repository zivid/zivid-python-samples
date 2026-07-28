"""
Stitch GUI

This sample demonstrates how to capture and stitch images based on robot pose
and hand-eye calibration.

Note: This script requires the Zivid Python API and PyQt5 to be installed.

"""

from pathlib import Path
from typing import Dict, List, Optional

import zivid
from nptyping import NDArray, Shape, UInt8
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QCloseEvent, QImage
from PyQt5.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from zivid.experimental.point_cloud_export import export_unorganized_point_cloud
from zivid.experimental.point_cloud_export.file_format import PLY
from zividsamples.gui.robot.robot_control import RobotTarget
from zividsamples.gui.verification.capture_at_pose_selection_widget import (
    CaptureAtPose,
    CaptureAtPoseSelectionWidget,
    RoiConfig,
)
from zividsamples.gui.widgets.pointcloud_visualizer import VisualizerWidget
from zividsamples.gui.widgets.pose_widget import PoseWidget, PoseWidgetDisplayMode
from zividsamples.gui.widgets.tab_with_robot_support import TabWidgetWithRobotSupport
from zividsamples.gui.wizard.hand_eye_configuration import HandEyeConfiguration
from zividsamples.gui.wizard.robot_configuration import RobotConfiguration
from zividsamples.gui.wizard.rotation_format_configuration import RotationInformation
from zividsamples.gui.wizard.settings_selector import SettingsPixelMappingIntrinsics
from zividsamples.transformation_matrix import TransformationMatrix


class StitchGUI(TabWidgetWithRobotSupport):
    robot_configuration: RobotConfiguration
    qimage_rgba: Optional[QImage] = None
    hand_eye_configuration: HandEyeConfiguration
    has_detection_result: bool = False
    has_confirmed_robot_pose: bool = False
    has_captured: bool = False
    point_cloud_widget: VisualizerWidget
    stitched_point_cloud: Optional[zivid.UnorganizedPointCloud]
    loading_finished = pyqtSignal()
    instructions_updated: pyqtSignal = pyqtSignal()
    description: List[str]
    instruction_steps: Dict[str, bool]

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        data_directory: Path,
        robot_configuration: RobotConfiguration,
        hand_eye_configuration: HandEyeConfiguration,
        initial_rotation_information: RotationInformation,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(data_directory, parent)

        self.description = [
            "Hand-Eye calibration can be used to convert between the coordinate systems of the camera and the robot. "
            + "If the robot coordinates represent a fixed world frame, then the hand-eye calibration can be used to stitch images together from different points of view.",
            "If the camera is mounted on the robot then the hand-eye transform plus the robot pose can be used to get the point cloud into robot base frame.",
            "If the camera is stationary then the hand-eye transform plus the robot pose can be used to get the point cloud into end effector frame."
            + "With this method an object can be scanned from multiple angles if the object is held by the robot and presented to the camera at different angles.",
            "The steps above will guide you through the process.",
        ]

        self.robot_configuration = robot_configuration
        self.hand_eye_configuration = hand_eye_configuration

        self.create_widgets(initial_rotation_information=initial_rotation_information)
        self.setup_layout()
        self.connect_signals()
        self.update_instructions(captured=False, robot_pose_confirmed=False)

    def create_widgets(self, initial_rotation_information: RotationInformation) -> None:
        self.robot_pose_widget = PoseWidget.Robot(
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.confirm_robot_pose_button = QPushButton("Confirm Robot Pose")
        self.confirm_robot_pose_button.setVisible(self.robot_configuration.has_no_robot())
        self.confirm_robot_pose_button.setCheckable(True)
        self.confirm_robot_pose_button.setObjectName("Stitch-confirm_robot_pose_button")
        self.hand_eye_pose_widget = PoseWidget.HandEye(
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.capture_at_pose_selection_widget = CaptureAtPoseSelectionWidget(directory=self.data_directory)
        self.uniform_color_check_box = QCheckBox()
        self.uniform_color_check_box.setText("Use uniform color for point clouds")
        self.uniform_color_check_box.setChecked(True)
        self.point_cloud_widget = VisualizerWidget()
        self.save_point_cloud_button = QPushButton("Save Point Cloud")
        self.save_point_cloud_button.setEnabled(False)
        self.stitched_point_cloud: Optional[zivid.UnorganizedPointCloud] = None

        self.roi_enabled_checkbox = QCheckBox("Enable ROI masking")
        self.roi_enabled_checkbox.setChecked(False)

        self.roi_min_x_spinbox = self._create_roi_spinbox(-500)
        self.roi_max_x_spinbox = self._create_roi_spinbox(500)
        self.roi_min_y_spinbox = self._create_roi_spinbox(-500)
        self.roi_max_y_spinbox = self._create_roi_spinbox(500)
        self.roi_min_z_spinbox = self._create_roi_spinbox(-500)
        self.roi_max_z_spinbox = self._create_roi_spinbox(500)

        self.roi_group_box = QGroupBox(self._roi_frame_text())
        roi_layout = QVBoxLayout()
        roi_layout.addWidget(self.roi_enabled_checkbox)

        self.roi_extents_widget = QWidget()
        roi_grid = QGridLayout()
        roi_grid.setContentsMargins(0, 0, 0, 0)
        roi_grid.addWidget(QLabel(""), 0, 0)
        roi_grid.addWidget(QLabel("Min (mm)"), 0, 1)
        roi_grid.addWidget(QLabel("Max (mm)"), 0, 2)
        roi_grid.addWidget(QLabel("X"), 1, 0)
        roi_grid.addWidget(self.roi_min_x_spinbox, 1, 1)
        roi_grid.addWidget(self.roi_max_x_spinbox, 1, 2)
        roi_grid.addWidget(QLabel("Y"), 2, 0)
        roi_grid.addWidget(self.roi_min_y_spinbox, 2, 1)
        roi_grid.addWidget(self.roi_max_y_spinbox, 2, 2)
        roi_grid.addWidget(QLabel("Z"), 3, 0)
        roi_grid.addWidget(self.roi_min_z_spinbox, 3, 1)
        roi_grid.addWidget(self.roi_max_z_spinbox, 3, 2)
        self.roi_extents_widget.setLayout(roi_grid)
        self.roi_extents_widget.setVisible(False)
        roi_layout.addWidget(self.roi_extents_widget)
        self.roi_group_box.setLayout(roi_layout)

        self.roi_warning_label = QLabel()
        self.roi_warning_label.setStyleSheet("color: orange;")
        self.roi_warning_label.setWordWrap(True)
        self.roi_warning_label.setVisible(False)

    def setup_layout(self) -> None:
        layout = QVBoxLayout()
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        center_layout = QHBoxLayout()
        confirm_robot_pose_layout = QHBoxLayout()
        confirm_robot_pose_layout.addStretch()
        confirm_robot_pose_layout.addWidget(self.confirm_robot_pose_button)
        confirm_robot_pose_layout.addStretch()

        left_panel.addWidget(self.robot_pose_widget)
        left_panel.addLayout(confirm_robot_pose_layout)
        left_panel.addWidget(self.hand_eye_pose_widget)
        right_panel.addWidget(self.capture_at_pose_selection_widget)
        right_panel.addWidget(self.roi_group_box)
        right_panel.addWidget(self.roi_warning_label)
        right_panel.addWidget(self.uniform_color_check_box)
        right_panel.addWidget(self.save_point_cloud_button)
        center_layout.addLayout(left_panel)
        center_layout.addLayout(right_panel)
        layout.addLayout(center_layout)

        self.setLayout(layout)

    def connect_signals(self) -> None:
        self.confirm_robot_pose_button.clicked.connect(self.on_confirm_robot_pose_button_clicked)
        self.capture_at_pose_selection_widget.capture_at_pose_clicked.connect(self.on_capture_at_pose_selected)
        self.capture_at_pose_selection_widget.selected_captures_updated.connect(self.update_stitched_view)
        self.capture_at_pose_selection_widget.loading_finished.connect(self.update_stitched_view)
        self.capture_at_pose_selection_widget.loading_finished.connect(self.loading_finished)
        self.uniform_color_check_box.stateChanged.connect(self.update_stitched_view)
        self.save_point_cloud_button.clicked.connect(self.on_save_point_cloud_clicked)
        self.roi_enabled_checkbox.toggled.connect(self._on_roi_enabled_toggled)

    def update_instructions(self, captured: bool, robot_pose_confirmed: bool) -> None:
        self.has_confirmed_robot_pose = robot_pose_confirmed
        self.has_captured = captured
        self.instruction_steps = {}
        if self.robot_configuration.can_control():
            self.instruction_steps[
                "Move Robot (click 'Move to next target', 'Home' or Disconnect→manually move robot→Connect)"
            ] = self.has_confirmed_robot_pose
        else:
            self.instruction_steps["Confirm Robot Pose"] = self.has_confirmed_robot_pose
        self.instruction_steps["Capture"] = captured and self.has_confirmed_robot_pose
        self.instructions_updated.emit()
        self.confirm_robot_pose_button.setChecked(self.has_confirmed_robot_pose)
        self.confirm_robot_pose_button.setStyleSheet(
            "background-color: green;" if self.has_confirmed_robot_pose else ""
        )

    def on_pending_changes(self) -> None:
        if self.data_directory_has_data():
            self.capture_at_pose_selection_widget.on_clear_button_clicked()
            self.capture_at_pose_selection_widget.set_directory(self.data_directory)
            self.capture_at_pose_selection_widget.load_capture_at_poses(
                self.hand_eye_pose_widget.get_transformation_matrix(),
                self.hand_eye_configuration.eye_in_hand,
                roi_config=self._get_roi_config(),
            )
        else:
            self.capture_at_pose_selection_widget.set_directory(self.data_directory)

    def is_loading(self) -> bool:
        return self.capture_at_pose_selection_widget.is_loading()

    def on_tab_visibility_changed(self, is_current: bool) -> None:
        if is_current:
            self.update_stitched_view()
        else:
            self.point_cloud_widget.hide()

    def hand_eye_configuration_update(self, hand_eye_configuration: HandEyeConfiguration) -> None:
        self.hand_eye_configuration = hand_eye_configuration
        self.hand_eye_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.robot_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.roi_group_box.setTitle(self._roi_frame_text())

    def rotation_format_update(self, rotation_information: RotationInformation) -> None:
        self.hand_eye_pose_widget.set_rotation_format(rotation_information)
        self.robot_pose_widget.set_rotation_format(rotation_information)

    def robot_configuration_update(self, robot_configuration: RobotConfiguration) -> None:
        self.robot_configuration = robot_configuration
        self.confirm_robot_pose_button.setVisible(self.robot_configuration.has_no_robot())
        self.update_instructions(captured=False, robot_pose_confirmed=self.has_confirmed_robot_pose)

    def on_confirm_robot_pose_button_clicked(self) -> None:
        self.update_instructions(captured=False, robot_pose_confirmed=self.confirm_robot_pose_button.isChecked())

    def on_actual_pose_updated(self, robot_target: RobotTarget) -> None:
        self.robot_pose_widget.set_transformation_matrix(robot_target.pose)
        self.update_instructions(captured=False, robot_pose_confirmed=True)

    def update_stitched_view(self) -> None:
        capture_at_poses = self.capture_at_pose_selection_widget.get_selected_capture_at_poses()
        unorganized_point_cloud = zivid.UnorganizedPointCloud()
        for capture_at_pose in capture_at_poses:
            point_cloud_at_pose = capture_at_pose.camera_frame.point_cloud().to_unorganized_point_cloud()
            if self.uniform_color_check_box.isChecked():
                point_cloud_at_pose.paint_uniform_color(capture_at_pose.color + [128])
            unorganized_point_cloud.extend(point_cloud_at_pose)

        has_roi_warnings = any(cap.roi_all_points_masked for cap in capture_at_poses)
        if has_roi_warnings:
            self.roi_warning_label.setText(
                "ROI masking removed all points for one or more captures. Showing unmasked data — adjust ROI settings."
            )
            self.roi_warning_label.setVisible(True)
        else:
            self.roi_warning_label.setVisible(False)

        if unorganized_point_cloud.size > 0:
            unorganized_point_cloud = unorganized_point_cloud.voxel_downsampled(voxel_size=1, min_points_per_voxel=1)
            self.point_cloud_widget.set_point_cloud(unorganized_point_cloud)
        self.stitched_point_cloud = unorganized_point_cloud if unorganized_point_cloud.size > 0 else None
        self.save_point_cloud_button.setEnabled(self.stitched_point_cloud is not None)

    def on_save_point_cloud_clicked(self):
        if self.stitched_point_cloud is None:
            return
        file_path = QFileDialog.getSaveFileName(
            self, "Save Point Cloud", "stitched_pointcloud.ply", "PLY Files (*.ply)"
        )[0]
        if file_path:
            if not file_path.endswith(".ply"):
                file_path += ".ply"
            try:
                export_unorganized_point_cloud(self.stitched_point_cloud, PLY(file_path, layout=PLY.Layout.unordered))
            except Exception as ex:
                QMessageBox.critical(self, "Save failed", str(ex))

    def on_capture_at_pose_selected(self, capture_at_pose: CaptureAtPose) -> None:
        self.robot_pose_widget.set_transformation_matrix(capture_at_pose.robot_pose)

    def process_capture(self, frame: zivid.Frame, _: NDArray[Shape["N, M, 4"], UInt8], __: SettingsPixelMappingIntrinsics) -> None:  # type: ignore
        if self.has_confirmed_robot_pose:
            self.capture_at_pose_selection_widget.add_capture_at_pose(
                robot_pose=self.robot_pose_widget.get_transformation_matrix(),
                camera_frame=frame,
                hand_eye_transform=self.hand_eye_pose_widget.get_transformation_matrix(),
                eye_in_hand=self.hand_eye_configuration.eye_in_hand,
                roi_config=self._get_roi_config(),
            )
            self.update_stitched_view()
            self.update_instructions(captured=True, robot_pose_confirmed=False)

    def set_hand_eye_transformation_matrix(self, transformation_matrix: TransformationMatrix) -> None:
        self.hand_eye_pose_widget.set_transformation_matrix(transformation_matrix)
        self.update_instructions(captured=self.has_captured, robot_pose_confirmed=self.has_confirmed_robot_pose)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        widgets.extend(self.robot_pose_widget.get_tab_widgets_in_order())
        widgets.append(self.confirm_robot_pose_button)
        widgets.extend(self.hand_eye_pose_widget.get_tab_widgets_in_order())
        return widgets

    @staticmethod
    def _create_roi_spinbox(default_value: float) -> QDoubleSpinBox:
        spinbox = QDoubleSpinBox()
        spinbox.setRange(-10000, 10000)
        spinbox.setDecimals(1)
        spinbox.setSingleStep(10)
        spinbox.setValue(default_value)
        return spinbox

    def _roi_spinboxes(self) -> List[QDoubleSpinBox]:
        return [
            self.roi_min_x_spinbox,
            self.roi_max_x_spinbox,
            self.roi_min_y_spinbox,
            self.roi_max_y_spinbox,
            self.roi_min_z_spinbox,
            self.roi_max_z_spinbox,
        ]

    def _roi_frame_text(self) -> str:
        if self.hand_eye_configuration.eye_in_hand:
            return "Region of Interest (Robot Base Frame)"
        return "Region of Interest (Robot Flange Frame)"

    def _on_roi_enabled_toggled(self, enabled: bool):
        self.roi_extents_widget.setVisible(enabled)

    def _get_roi_config(self):
        if not self.roi_enabled_checkbox.isChecked():
            return None
        return RoiConfig(
            min_x=self.roi_min_x_spinbox.value(),
            max_x=self.roi_max_x_spinbox.value(),
            min_y=self.roi_min_y_spinbox.value(),
            max_y=self.roi_max_y_spinbox.value(),
            min_z=self.roi_min_z_spinbox.value(),
            max_z=self.roi_max_z_spinbox.value(),
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # pylint: disable=C0103
        self.point_cloud_widget.close()
        super().closeEvent(event)
