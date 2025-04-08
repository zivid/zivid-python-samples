"""
Stitch GUI

This sample demonstrates how to capture and stitch images based on robot pose
and hand-eye calibration.

Note: This script requires the Zivid Python API, Open3D and PyQt5 to be installed.

"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import zivid
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget
from zividsamples.gui.capture_at_pose_selection_widget import CaptureAtPose, CaptureAtPoseSelectionWidget
from zividsamples.gui.hand_eye_configuration import HandEyeConfiguration
from zividsamples.gui.pose_widget import PoseWidget, PoseWidgetDisplayMode
from zividsamples.gui.robot_control import RobotTarget
from zividsamples.gui.rotation_format_configuration import RotationInformation
from zividsamples.transformation_matrix import TransformationMatrix

if sys.version_info < (3, 12):
    from zividsamples.gui.pointcloud_visualizer import Open3DVisualizerWidget


class StitchGUI(QWidget):
    data_directory: Path
    use_robot: bool
    qimage_rgba: Optional[QImage] = None
    hand_eye_configuration: HandEyeConfiguration
    if sys.version_info < (3, 12):
        point_cloud_widget: Optional[Open3DVisualizerWidget] = None
        show_warning_once: bool = False
    else:
        point_cloud_widget = None
        show_warning_once: bool = True
    has_detection_result: bool = False
    has_confirmed_robot_pose: bool = False
    instructions_updated: pyqtSignal = pyqtSignal()
    description: List[str]
    instruction_steps: Dict[str, bool]

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        data_directory: Path,
        use_robot: bool,
        hand_eye_configuration: HandEyeConfiguration,
        initial_rotation_information: RotationInformation,
        parent=None,
    ):
        super().__init__(parent)

        self.description = [
            "Hand-Eye calibration can be used to convert between the coordinate systems of the camera and the robot. "
            + "If the robot coordinates represent a fixed world frame, then the hand-eye calibration can be used to stitch images together from different points of view.",
            "If the camera is mounted on the robot then the hand-eye transform plus the robot pose can be used to get the point cloud into robot base frame.",
            "If the camera is stationary then the hand-eye transform plus the robot pose can be used to get the point cloud into end effector frame."
            + "With this method an object can be scanned from multiple angles if the object is held by the robot and presented to the camera at different angles.",
            "The steps above will guide you through the process.",
        ]

        self.data_directory = data_directory
        self.use_robot = use_robot
        self.hand_eye_configuration = hand_eye_configuration

        self.create_widgets(initial_rotation_information=initial_rotation_information)
        self.setup_layout()
        self.connect_signals()
        self.update_instructions(captured=False, robot_pose_confirmed=False)

    def create_widgets(self, initial_rotation_information: RotationInformation):
        self.robot_pose_widget = PoseWidget.Robot(
            self.data_directory / "robot_pose.yaml",
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.confirm_robot_pose_button = QPushButton("Confirm Robot Pose")
        self.confirm_robot_pose_button.setVisible(not self.use_robot)
        self.confirm_robot_pose_button.setCheckable(True)
        self.confirm_robot_pose_button.setObjectName("Stitch-confirm_robot_pose_button")
        self.hand_eye_pose_widget = PoseWidget.HandEye(
            self.data_directory / "hand_eye_transform.yaml",
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.capture_at_pose_selection_widget = CaptureAtPoseSelectionWidget(directory=self.data_directory)

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
        center_layout.addLayout(left_panel)
        center_layout.addLayout(right_panel)
        layout.addLayout(center_layout)

        self.setLayout(layout)

    def connect_signals(self):
        self.confirm_robot_pose_button.clicked.connect(self.on_confirm_robot_pose_button_clicked)
        self.capture_at_pose_selection_widget.capture_at_pose_clicked.connect(self.on_capture_at_pose_selected)
        self.capture_at_pose_selection_widget.selected_captures_updated.connect(self.update_stitched_view)

    def update_instructions(self, captured: bool, robot_pose_confirmed: bool):
        self.has_confirmed_robot_pose = robot_pose_confirmed
        self.instruction_steps = {}
        if self.use_robot:
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

    def stop_3d_visualizer(self):
        if self.point_cloud_widget is not None:
            self.point_cloud_widget.closeEvent(None)
        self.point_cloud_widget = None

    def start_3d_visualizer(self):
        self.stop_3d_visualizer()
        if sys.version_info < (3, 12):
            self.point_cloud_widget = Open3DVisualizerWidget()
        elif self.show_warning_once:
            folder_path = self.capture_at_pose_selection_widget.directory
            QMessageBox.warning(
                self,
                "Visualization",
                f"""\
Visualizing the point cloud requires Python 3.11 or earlier.

All transformed captures will be saved as .ply files in the folder:

{folder_path.as_posix()}""",
            )
            self.show_warning_once = False
        self.update_stitched_view()

    def hand_eye_configuration_update(self, hand_eye_configuration: HandEyeConfiguration):
        self.hand_eye_configuration = hand_eye_configuration
        self.hand_eye_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.robot_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)

    def rotation_format_update(self, rotation_format: RotationInformation):
        self.hand_eye_pose_widget.set_rotation_format(rotation_format)
        self.robot_pose_widget.set_rotation_format(rotation_format)

    def toggle_use_robot(self, use_robot: bool):
        self.use_robot = use_robot
        self.confirm_robot_pose_button.setVisible(not self.use_robot)
        self.update_instructions(captured=False, robot_pose_confirmed=self.has_confirmed_robot_pose)

    def on_confirm_robot_pose_button_clicked(self):
        self.update_instructions(captured=False, robot_pose_confirmed=self.confirm_robot_pose_button.isChecked())

    def on_actual_pose_updated(self, robot_target: RobotTarget):
        self.robot_pose_widget.set_transformation_matrix(robot_target.pose)
        self.update_instructions(captured=False, robot_pose_confirmed=True)

    def update_stitched_view(self):
        xyz_total = []
        rgb_total = []
        capture_at_poses = self.capture_at_pose_selection_widget.get_selected_capture_at_poses()
        for capture_at_pose in capture_at_poses:
            point_cloud = capture_at_pose.camera_frame.point_cloud()
            capture_at_pose.save_as_ply()
            xyz = point_cloud.copy_data("xyz").reshape(-1, 3)
            rgb = point_cloud.copy_data("rgba_srgb")[:, :, :3].reshape(-1, 3)
            valid_indices = np.logical_not(np.isnan(xyz).any(axis=1))
            xyz_total.append(xyz[valid_indices])
            rgb_total.append(rgb[valid_indices])
        if self.point_cloud_widget is not None:
            self.point_cloud_widget.set_point_cloud(xyz_total, rgb_total)

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

    def set_save_directory(self, data_directory: Path):
        if self.data_directory != data_directory:
            self.data_directory = data_directory
            self.capture_at_pose_selection_widget.set_directory(self.data_directory)

    def set_load_directory(self, data_directory: Path):
        self.data_directory = Path(data_directory)
        self.hand_eye_pose_widget.set_yaml_path_and_load(self.data_directory / "hand_eye_transform.yaml")
        self.capture_at_pose_selection_widget.on_clear_button_clicked()
        self.capture_at_pose_selection_widget.set_directory(self.data_directory)
        self.capture_at_pose_selection_widget.load_capture_at_poses(
            self.hand_eye_pose_widget.get_transformation_matrix(),
            self.hand_eye_configuration.eye_in_hand,
        )
        self.update_stitched_view()

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        widgets.extend(self.robot_pose_widget.get_tab_widgets_in_order())
        widgets.append(self.confirm_robot_pose_button)
        widgets.extend(self.hand_eye_pose_widget.get_tab_widgets_in_order())
        return widgets
