"""
Stitch GUI

This sample demonstrates how to capture and stitch images based on robot pose
and hand-eye calibration.

Note: This script requires the Zivid Python API and PyQt5 to be installed.

"""

from pathlib import Path
from typing import Dict, List, Optional

import zivid
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from zividsamples.gui.capture_at_pose_selection_widget import CaptureAtPose, CaptureAtPoseSelectionWidget
from zividsamples.gui.hand_eye_configuration import HandEyeConfiguration
from zividsamples.gui.pointcloud_visualizer import VisualizerWidget
from zividsamples.gui.pose_widget import PoseWidget, PoseWidgetDisplayMode
from zividsamples.gui.robot_configuration import RobotConfiguration
from zividsamples.gui.robot_control import RobotTarget
from zividsamples.gui.rotation_format_configuration import RotationInformation
from zividsamples.gui.tab_with_robot_support import TabWidgetWithRobotSupport
from zividsamples.transformation_matrix import TransformationMatrix


class StitchGUI(TabWidgetWithRobotSupport):
    robot_configuration: RobotConfiguration
    qimage_rgba: Optional[QImage] = None
    hand_eye_configuration: HandEyeConfiguration
    has_detection_result: bool = False
    has_confirmed_robot_pose: bool = False
    point_cloud_widget: VisualizerWidget
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
        parent=None,
    ):
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

    def create_widgets(self, initial_rotation_information: RotationInformation):
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

    def setup_layout(self):
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
        right_panel.addWidget(self.uniform_color_check_box)
        center_layout.addLayout(left_panel)
        center_layout.addLayout(right_panel)
        layout.addLayout(center_layout)

        self.setLayout(layout)

    def connect_signals(self):
        self.confirm_robot_pose_button.clicked.connect(self.on_confirm_robot_pose_button_clicked)
        self.capture_at_pose_selection_widget.capture_at_pose_clicked.connect(self.on_capture_at_pose_selected)
        self.capture_at_pose_selection_widget.selected_captures_updated.connect(self.update_stitched_view)
        self.uniform_color_check_box.stateChanged.connect(self.update_stitched_view)

    def update_instructions(self, captured: bool, robot_pose_confirmed: bool):
        self.has_confirmed_robot_pose = robot_pose_confirmed
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

    def on_pending_changes(self):
        if self.data_directory_has_data():
            self.capture_at_pose_selection_widget.on_clear_button_clicked()
            self.capture_at_pose_selection_widget.set_directory(self.data_directory)
            self.capture_at_pose_selection_widget.load_capture_at_poses(
                self.hand_eye_pose_widget.get_transformation_matrix(),
                self.hand_eye_configuration.eye_in_hand,
            )
            self.update_stitched_view()
        else:
            self.capture_at_pose_selection_widget.set_directory(self.data_directory)

    def on_tab_visibility_changed(self, is_current: bool):
        if is_current:
            self.update_stitched_view()
        else:
            self.point_cloud_widget.hide()

    def hand_eye_configuration_update(self, hand_eye_configuration: HandEyeConfiguration):
        self.hand_eye_configuration = hand_eye_configuration
        self.hand_eye_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.robot_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)

    def rotation_format_update(self, rotation_information: RotationInformation):
        self.hand_eye_pose_widget.set_rotation_format(rotation_information)
        self.robot_pose_widget.set_rotation_format(rotation_information)

    def robot_configuration_update(self, robot_configuration: RobotConfiguration):
        self.robot_configuration = robot_configuration
        self.confirm_robot_pose_button.setVisible(self.robot_configuration.has_no_robot())
        self.update_instructions(captured=False, robot_pose_confirmed=self.has_confirmed_robot_pose)

    def on_confirm_robot_pose_button_clicked(self):
        self.update_instructions(captured=False, robot_pose_confirmed=self.confirm_robot_pose_button.isChecked())

    def on_actual_pose_updated(self, robot_target: RobotTarget):
        self.robot_pose_widget.set_transformation_matrix(robot_target.pose)
        self.update_instructions(captured=False, robot_pose_confirmed=True)

    def update_stitched_view(self):
        capture_at_poses = self.capture_at_pose_selection_widget.get_selected_capture_at_poses()
        unorganized_point_cloud = zivid.UnorganizedPointCloud()
        for capture_at_pose in capture_at_poses:
            point_cloud_at_pose = capture_at_pose.camera_frame.point_cloud().to_unorganized_point_cloud()
            if self.uniform_color_check_box.isChecked():
                point_cloud_at_pose.paint_uniform_color(capture_at_pose.color + [128])
            unorganized_point_cloud.extend(point_cloud_at_pose)
        if unorganized_point_cloud.size > 0:
            unorganized_point_cloud = unorganized_point_cloud.voxel_downsampled(voxel_size=1, min_points_per_voxel=1)
            self.point_cloud_widget.set_point_cloud(unorganized_point_cloud)

    def on_capture_at_pose_selected(self, capture_at_pose: CaptureAtPose):
        self.robot_pose_widget.set_transformation_matrix(capture_at_pose.robot_pose)

    def process_capture(self, frame: zivid.Frame, _, __):  # type: ignore
        if self.has_confirmed_robot_pose:
            self.capture_at_pose_selection_widget.add_capture_at_pose(
                robot_pose=self.robot_pose_widget.get_transformation_matrix(),
                camera_frame=frame,
                hand_eye_transform=self.hand_eye_pose_widget.get_transformation_matrix(),
                eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            )
            self.update_stitched_view()
            self.update_instructions(captured=True, robot_pose_confirmed=False)

    def set_hand_eye_transformation_matrix(self, transformation_matrix: TransformationMatrix):
        self.hand_eye_pose_widget.set_transformation_matrix(transformation_matrix)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        widgets.extend(self.robot_pose_widget.get_tab_widgets_in_order())
        widgets.append(self.confirm_robot_pose_button)
        widgets.extend(self.hand_eye_pose_widget.get_tab_widgets_in_order())
        return widgets

    def closeEvent(self, event) -> None:  # pylint: disable=C0103
        self.point_cloud_widget.close()
        super().closeEvent(event)
