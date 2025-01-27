"""
Touch GUI - with Robot Control

This sample demonstrates how to capture, detect aruco marker and then
touch the marker based on robot pose, aruco pose and hand-eye calibration.
In addition it allows control of Robot via RoboDK.

Note: This script requires the Zivid Python API, Open3D, RoboDK and PyQt5 to be
installed.

"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import zivid
from nptyping import NDArray, Shape, UInt8
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from zividsamples.gui.cv2_handler import CV2Handler
from zividsamples.gui.hand_eye_configuration import HandEyeConfiguration
from zividsamples.gui.image_viewer import ImageViewer
from zividsamples.gui.marker_widget import TouchMarkerWidget, generate_marker_dictionary
from zividsamples.gui.pose_widget import MarkerPosesWidget, PoseWidget, PoseWidgetDisplayMode
from zividsamples.gui.robot_control import RobotTarget
from zividsamples.gui.rotation_format_configuration import RotationInformation
from zividsamples.gui.settings_selector import SettingsPixelMappingIntrinsics
from zividsamples.transformation_matrix import TransformationMatrix


class TouchGUI(QWidget):
    data_directory: Path
    camera: Optional[zivid.Camera] = None
    qimage_rgba: Optional[QImage] = None
    hand_eye_configuration: HandEyeConfiguration
    marker_confirmed: bool = False
    marker_captured: bool = False
    touch_pose_updated: pyqtSignal = pyqtSignal(TransformationMatrix)
    instructions_updated: pyqtSignal = pyqtSignal()
    description: List[str]
    instruction_steps: Dict[str, bool]

    def __init__(
        self,
        data_directory: Path,
        hand_eye_configuration: HandEyeConfiguration,
        initial_rotation_information: RotationInformation,
        parent=None,
    ):
        super().__init__(parent)

        self.cv2_handler = CV2Handler()

        self.description = [
            "Hand-Eye calibration is used to convert between the coordinate systems of the camera and the robot. "
            + "If the robot coordinates represent a fixed world frame, then the hand-eye calibration can be used to stitch images together from different points of view.",
            "If the camera is mounted on the robot then the hand-eye transform plus the robot pose can be used to get the point cloud into robot base frame.",
            "If the camera is stationary then the hand-eye transform plus the robot pose can be used to get the point cloud into end effector frame. "
            + "With this method an object can be scanned from multiple angles if the object is held by the robot and presented to the camera at different angles.",
            "The steps above will guide you through the process.",
        ]

        self.data_directory = data_directory
        self.hand_eye_configuration = hand_eye_configuration
        self.create_widgets(initial_rotation_information=initial_rotation_information)
        self.setup_layout()
        self.connect_signals()
        self.update_instructions(marker_confirmed=False, marker_captured=False)

    def create_widgets(self, initial_rotation_information: RotationInformation):
        self.hand_eye_pose_widget = PoseWidget.HandEye(
            self.data_directory / "hand_eye_transform.yaml",
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.robot_pose_widget = PoseWidget.Robot(
            self.data_directory / "robot_pose.yaml",
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.markers_in_robot_base_frame_pose_widget = MarkerPosesWidget.MarkersInRobotFrame(
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.markers_in_robot_base_frame_pose_widget.setMinimumHeight(180)
        self.marker_selection = TouchMarkerWidget()
        self.calibration_object_image = ImageViewer()
        self.calibration_object_image.setMinimumHeight(300)
        self.calibration_object_image.setMinimumWidth(300)
        self.confirm_marker_button = QPushButton("Confirm marker to touch")
        self.confirm_marker_button.setCheckable(True)
        self.confirm_marker_button.setObjectName("Touch-confirm_marker_button")

    def setup_layout(self):
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        center_layout = QHBoxLayout()

        layout.addLayout(top_layout)

        left_panel.addWidget(self.hand_eye_pose_widget)
        left_panel.addWidget(self.robot_pose_widget)
        right_panel.addWidget(self.marker_selection)
        right_panel.addWidget(self.confirm_marker_button)
        right_panel.addWidget(self.calibration_object_image)
        center_layout.addLayout(left_panel)
        center_layout.addLayout(right_panel)
        layout.addLayout(center_layout)
        layout.addWidget(self.markers_in_robot_base_frame_pose_widget)

        self.setLayout(layout)

    def connect_signals(self):
        self.confirm_marker_button.clicked.connect(self.on_confirm_marker_button_clicked)

    def update_instructions(self, marker_confirmed: bool, marker_captured: bool):
        self.marker_confirmed = marker_confirmed
        self.instruction_steps = {}
        self.instruction_steps["Confirm marker to touch"] = self.marker_confirmed
        self.instruction_steps["Capture"] = marker_captured and self.marker_confirmed
        self.instruction_steps["Touch"] = False
        self.instructions_updated.emit()
        self.confirm_marker_button.setChecked(self.marker_confirmed)
        self.confirm_marker_button.setStyleSheet("background-color: green;" if self.marker_confirmed else "")

    def on_confirm_marker_button_clicked(self):
        self.update_instructions(marker_confirmed=self.confirm_marker_button.isChecked(), marker_captured=False)

    def hand_eye_configuration_update(self, hand_eye_configuration: HandEyeConfiguration):
        self.hand_eye_configuration = hand_eye_configuration
        self.hand_eye_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.robot_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)

    def rotation_format_update(self, rotation_format: RotationInformation):
        self.hand_eye_pose_widget.set_rotation_format(rotation_format)
        self.robot_pose_widget.set_rotation_format(rotation_format)

    def toggle_use_robot(self, _: bool):
        pass

    def on_actual_pose_updated(self, robot_target: RobotTarget):
        self.robot_pose_widget.set_transformation_matrix(robot_target.pose)

    def process_capture(self, frame: zivid.Frame, rgba: NDArray[Shape["N, M, 4"], UInt8], settings: SettingsPixelMappingIntrinsics):  # type: ignore
        detection_result = zivid.calibration.detect_markers(
            frame, [self.marker_selection.marker_id], self.marker_selection.marker_dictionary
        )
        markers = detection_result.detected_markers()
        rgb = rgba[:, :, :3].copy().astype(np.uint8)
        rgba[:, :, :3] = self.cv2_handler.draw_detected_markers(markers, rgb, settings.pixel_mapping)
        qimage_rgba = QImage(
            rgba.data,
            rgba.shape[1],
            rgba.shape[0],
            QImage.Format_RGBA8888,
        )
        self.calibration_object_image.set_pixmap(QPixmap.fromImage(qimage_rgba))
        if len(markers) == 0:
            raise RuntimeError("No markers found")
        marker_poses = generate_marker_dictionary(markers)
        detected_marker_poses_in_camera_frame = {
            key: TransformationMatrix.from_matrix(np.asarray(value.pose.to_matrix()))
            for key, value in marker_poses.items()
        }
        hand_eye_transform = self.hand_eye_pose_widget.transformation_matrix
        robot_transform = self.robot_pose_widget.transformation_matrix
        robot_frame_transform = (
            robot_transform * hand_eye_transform
            if self.hand_eye_configuration.eye_in_hand
            else robot_transform.inv() * hand_eye_transform
        )
        detected_marker_poses_in_robot_frame = {
            key: robot_frame_transform * value for key, value in detected_marker_poses_in_camera_frame.items()
        }
        self.markers_in_robot_base_frame_pose_widget.set_markers(detected_marker_poses_in_robot_frame)
        touch_pose = list(detected_marker_poses_in_robot_frame.values())[0]
        touch_tool = TransformationMatrix()
        touch_tool.translation[2] = -self.marker_selection.z_offset.value()
        self.touch_pose_updated.emit(touch_pose * touch_tool)
        self.update_instructions(marker_confirmed=self.marker_confirmed, marker_captured=True)

    def set_save_directory(self, data_directory: Path):
        if self.data_directory != data_directory:
            self.data_directory = data_directory
            self.hand_eye_pose_widget.set_yaml_path_and_save(self.data_directory / "hand_eye_transform.yaml")
            self.robot_pose_widget.set_yaml_path_and_save(self.data_directory / "robot_pose.yaml")

    def set_load_directory(self, data_directory: Path):
        self.data_directory = Path(data_directory)
        self.hand_eye_pose_widget.set_yaml_path_and_load(self.data_directory / "hand_eye_transform.yaml")
        self.robot_pose_widget.set_yaml_path_and_load(self.data_directory / "robot_pose.yaml")

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        widgets.extend(self.robot_pose_widget.get_tab_widgets_in_order())
        widgets.extend(self.hand_eye_pose_widget.get_tab_widgets_in_order())
        widgets.extend(self.marker_selection.get_tab_widgets_in_order())
        widgets.append(self.confirm_marker_button)
        return widgets

    def set_hand_eye_transformation_matrix(self, transformation_matrix: TransformationMatrix):
        self.hand_eye_pose_widget.set_transformation_matrix(transformation_matrix)
