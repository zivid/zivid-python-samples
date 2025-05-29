"""
Hand-Eye Verification GUI


Note: This script requires the Zivid Python API and PyQt5 to be installed.

"""

from pathlib import Path
from typing import Callable, Dict, List

import numpy as np
import zivid
from nptyping import Float32, NDArray, Shape, UInt8
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGridLayout, QPushButton, QVBoxLayout, QWidget
from zivid.calibration import MarkerShape
from zividsamples.gui.cv2_handler import CV2Handler
from zividsamples.gui.detection_visualization import DetectionVisualizationWidget
from zividsamples.gui.hand_eye_configuration import CalibrationObject, HandEyeConfiguration
from zividsamples.gui.marker_widget import MarkerConfiguration, generate_marker_dictionary
from zividsamples.gui.pose_widget import MarkerPosesWidget, PoseWidget, PoseWidgetDisplayMode
from zividsamples.gui.robot_control import RobotTarget
from zividsamples.gui.rotation_format_configuration import RotationInformation
from zividsamples.gui.settings_selector import SettingsPixelMappingIntrinsics
from zividsamples.transformation_matrix import TransformationMatrix


def capture_rgba(
    capture_function: Callable[[zivid.Settings2D], zivid.Frame2D], settings_2d: zivid.Settings2D
) -> NDArray[Shape["H, W, 4"], UInt8]:  # type: ignore
    frame_2d = capture_function(settings_2d)
    return frame_2d.image_srgb().copy_data()


def create_board_in_camera_frame(
    transformation_matrix: TransformationMatrix,
) -> NDArray[Shape["6, 7, 3"], Float32]:  # type: ignore
    corner_size = 30.0
    board_points = np.zeros((6, 7, 3), dtype=np.float32)
    for row in range(6):
        for col in range(7):
            board_points[row, col, :] = [col * corner_size, row * corner_size, 0]
    return transformation_matrix.transform(board_points)


def extract_marker_points_in_camera_frame(
    markers: Dict[str, MarkerShape],
) -> NDArray[Shape["N, 3"], Float32]:  # type: ignore
    marker_points = np.zeros((len(markers) * 4, 3), dtype=np.float32)
    for index, marker in enumerate(markers.values()):
        row_offset = index * 4
        marker_points[row_offset : row_offset + 4, :] = marker.corners_in_camera_coordinates
    return marker_points


class HandEyeVerificationGUI(QWidget):
    use_robot: bool
    detected_markers: Dict[str, MarkerShape] = {}
    detected_marker_poses_in_robot_frame: Dict[str, TransformationMatrix] = {}
    detected_marker_points_in_robot_frame: NDArray[Shape["N, 3"], Float32] = np.zeros(  # type: ignore
        (0, 3), dtype=np.float32
    )
    detected_marker_poses_in_camera_frame: Dict[str, TransformationMatrix] = {}
    detected_marker_points_in_camera_frame: NDArray[Shape["N, 3"], Float32] = np.zeros(  # type: ignore
        (0, 3), dtype=np.float32
    )
    hand_eye_configuration: HandEyeConfiguration
    marker_configuration: MarkerConfiguration = MarkerConfiguration()
    advanced_view: bool = False
    has_set_object_poses_in_robot_frame: bool = False
    has_confirmed_robot_pose: bool = False
    update_projection = pyqtSignal(bool)
    instructions_updated: pyqtSignal = pyqtSignal()
    description: List[str]
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
            "The best way to verify the hand-eye transformation is to perform a touch test. ",
            # + "When we perform a touch test we apply the hand-eye transform to information found in the camera frame in order to get the information in the robot frame."
            "However, we can get an approximate test of the hand-eye calibration by using the projector in the 3D camera."
            + "First we need to capture a calibration object, find its pose in camera frame and record the robot pose at the same time."
            + "Then we apply the hand-eye transformation to calculate the calibration object pose in the robot frame."
            + "We can then use the same hand-eye transformation to figure out where the calibration object should be in the camera frame after moving the robot."
            + "When we know where the calibration object should be in the camera frame, we can project onto using the projector in the 3D camera.",
            "The steps above will guide you through the process.",
        ]

        self.data_directory = data_directory
        self.use_robot = use_robot
        self.hand_eye_configuration = hand_eye_configuration
        self.marker_configuration = marker_configuration
        self.cv2_handler = cv2_handler

        self.create_widgets(initial_rotation_information=initial_rotation_information)
        self.setup_layout()
        self.connect_signals()
        self.update_instructions(has_set_object_poses_in_robot_frame=False, robot_pose_confirmed=False)

    def create_widgets(self, initial_rotation_information: RotationInformation):
        self.robot_pose_widget = PoseWidget.Robot(
            self.data_directory / "robot_pose.yaml",
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.robot_pose_widget.setObjectName("HE-Verification-robot_pose_widget")
        self.confirm_robot_pose_button = QPushButton("Confirm Robot Pose")
        self.confirm_robot_pose_button.setVisible(not self.use_robot)
        self.confirm_robot_pose_button.setObjectName("HE-Verification-confirm_robot_pose_button")
        self.hand_eye_pose_widget = PoseWidget.HandEye(
            self.data_directory / "hand_eye_transform.yaml",
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.hand_eye_pose_widget.setObjectName("HE-Verification-hand_eye_pose_widget")
        self.calibration_board_in_camera_frame_pose_widget = PoseWidget.CalibrationBoardInCameraFrame(
            self.data_directory / "calibration_object_in_camera_frame_pose.yaml",
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.markers_in_camera_frame_pose_widget = MarkerPosesWidget.MarkersInCameraFrame(
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.calibration_board_in_robot_base_frame_pose_widget = PoseWidget.CalibrationBoardInRobotFrame(
            self.data_directory / "calibration_object_in_robot_base_frame_pose.yaml",
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.markers_in_robot_base_frame_pose_widget = MarkerPosesWidget.MarkersInRobotFrame(
            eye_in_hand=self.hand_eye_configuration.eye_in_hand,
            display_mode=PoseWidgetDisplayMode.OnlyPose,
            initial_rotation_information=initial_rotation_information,
        )
        self.detection_visualization_widget = DetectionVisualizationWidget(self.hand_eye_configuration)
        self.detection_visualization_widget.descriptive_image_label.hide()

    def setup_layout(self):
        layout = QVBoxLayout()
        self.calibration_object_poses_layout = QVBoxLayout()

        self.top_grid_layout = QGridLayout()
        self.top_grid_layout.addWidget(self.robot_pose_widget, 0, 0, 1, 2)
        self.top_grid_layout.addWidget(self.confirm_robot_pose_button, 1, 0)
        self.top_grid_layout.addWidget(self.detection_visualization_widget, 1, 1)

        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            self.calibration_object_poses_layout.addWidget(self.calibration_board_in_camera_frame_pose_widget)
            self.calibration_object_poses_layout.addWidget(self.calibration_board_in_robot_base_frame_pose_widget)
        else:
            self.calibration_object_poses_layout.addWidget(self.markers_in_camera_frame_pose_widget)
            self.calibration_object_poses_layout.addWidget(self.markers_in_robot_base_frame_pose_widget)
        self.toggle_advanced_view(self.advanced_view)
        layout.addLayout(self.top_grid_layout)
        layout.addLayout(self.calibration_object_poses_layout)

        self.setLayout(layout)

    def connect_signals(self):
        self.confirm_robot_pose_button.clicked.connect(self.on_confirm_robot_pose_button_clicked)
        self.robot_pose_widget.pose_updated.connect(self.on_robot_pose_manually_updated)

    def update_instructions(self, has_set_object_poses_in_robot_frame: bool, robot_pose_confirmed: bool):
        self.has_confirmed_robot_pose = robot_pose_confirmed
        self.has_set_object_poses_in_robot_frame = has_set_object_poses_in_robot_frame and self.has_confirmed_robot_pose
        self.instruction_steps = {}
        if self.use_robot:
            self.instruction_steps[
                "Move Robot (click 'Move to next target', 'Home' or Disconnect→manually move robot→Connect)"
            ] = self.has_confirmed_robot_pose
        else:
            self.instruction_steps["Confirm Robot Pose"] = self.has_confirmed_robot_pose
        self.instruction_steps["Capture - to set object poses in robot frame"] = (
            self.has_set_object_poses_in_robot_frame
        )
        if self.has_confirmed_robot_pose and self.has_set_object_poses_in_robot_frame:
            if self.use_robot:
                self.instruction_steps[
                    "Move Robot (click 'Move to next target' or Disconnect→manually move robot→Connect)"
                ] = False
            else:
                self.instruction_steps["Input robot pose and move the robot to this pose"] = False
        self.instructions_updated.emit()
        self.confirm_robot_pose_button.setStyleSheet(
            "background-color: green;" if self.has_confirmed_robot_pose else ""
        )

    def hand_eye_configuration_update(self, hand_eye_configuration: HandEyeConfiguration):
        self.hand_eye_configuration = hand_eye_configuration
        self.on_hand_eye_configuration_updated()

    def marker_configuration_update(self, marker_configuration: MarkerConfiguration):
        self.marker_configuration = marker_configuration

    def rotation_format_update(self, rotation_format: RotationInformation):
        self.hand_eye_pose_widget.set_rotation_format(rotation_format)
        self.robot_pose_widget.set_rotation_format(rotation_format)
        self.calibration_board_in_camera_frame_pose_widget.set_rotation_format(rotation_format)
        self.calibration_board_in_robot_base_frame_pose_widget.set_rotation_format(rotation_format)
        self.markers_in_camera_frame_pose_widget.set_rotation_format(rotation_format)
        self.markers_in_robot_base_frame_pose_widget.set_rotation_format(rotation_format)

    def toggle_advanced_view(self, checked):
        if checked != self.advanced_view:
            self.top_grid_layout.removeWidget(self.robot_pose_widget)
            self.top_grid_layout.removeWidget(self.confirm_robot_pose_button)
            self.top_grid_layout.removeWidget(self.detection_visualization_widget)
            if not checked:
                self.top_grid_layout.removeWidget(self.hand_eye_pose_widget)
                self.top_grid_layout.addWidget(self.robot_pose_widget, 0, 0, 1, 2)
                self.top_grid_layout.addWidget(self.confirm_robot_pose_button, 1, 0)
                self.top_grid_layout.addWidget(self.detection_visualization_widget, 1, 1)
                self.top_grid_layout.setColumnStretch(0, 1)
                self.top_grid_layout.setColumnStretch(1, 1)
            else:
                self.top_grid_layout.addWidget(self.robot_pose_widget, 0, 0)
                self.top_grid_layout.addWidget(self.confirm_robot_pose_button, 0, 1)
                self.top_grid_layout.addWidget(self.detection_visualization_widget, 0, 2, 2, 1)
                self.top_grid_layout.addWidget(self.hand_eye_pose_widget, 1, 0)
                self.top_grid_layout.setColumnStretch(0, 0)
                self.top_grid_layout.setColumnStretch(1, 0)
        self.advanced_view = checked
        self.hand_eye_pose_widget.setVisible(checked)
        self.hand_eye_pose_widget.toggle_advanced_section(checked)
        self.robot_pose_widget.setVisible(checked or not self.use_robot)
        self.robot_pose_widget.toggle_advanced_section(checked)
        show_marker_poses = (
            self.hand_eye_configuration.calibration_object == CalibrationObject.Markers
        ) and self.advanced_view
        show_calibration_board_pose = (
            self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard
        ) and self.advanced_view
        self.markers_in_camera_frame_pose_widget.setVisible(show_marker_poses)
        self.markers_in_robot_base_frame_pose_widget.setVisible(show_marker_poses)
        self.calibration_board_in_camera_frame_pose_widget.setVisible(show_calibration_board_pose)
        self.calibration_board_in_robot_base_frame_pose_widget.setVisible(show_calibration_board_pose)

    def toggle_use_robot(self, use_robot: bool):
        self.use_robot = use_robot
        self.confirm_robot_pose_button.setVisible(not self.use_robot)
        self.update_instructions(
            has_set_object_poses_in_robot_frame=self.has_set_object_poses_in_robot_frame,
            robot_pose_confirmed=self.has_confirmed_robot_pose,
        )

    def on_hand_eye_configuration_updated(self):
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            self.calibration_object_poses_layout.removeWidget(self.markers_in_camera_frame_pose_widget)
            self.calibration_object_poses_layout.removeWidget(self.markers_in_robot_base_frame_pose_widget)
            self.calibration_object_poses_layout.addWidget(self.calibration_board_in_camera_frame_pose_widget)
            self.calibration_object_poses_layout.addWidget(self.calibration_board_in_robot_base_frame_pose_widget)
        else:
            self.calibration_object_poses_layout.removeWidget(self.calibration_board_in_camera_frame_pose_widget)
            self.calibration_object_poses_layout.removeWidget(self.calibration_board_in_robot_base_frame_pose_widget)
            self.calibration_object_poses_layout.addWidget(self.markers_in_camera_frame_pose_widget)
            self.calibration_object_poses_layout.addWidget(self.markers_in_robot_base_frame_pose_widget)

        self.toggle_advanced_view(self.advanced_view)

        self.hand_eye_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.robot_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.calibration_board_in_camera_frame_pose_widget.on_eye_in_hand_toggled(
            self.hand_eye_configuration.eye_in_hand
        )
        self.calibration_board_in_robot_base_frame_pose_widget.on_eye_in_hand_toggled(
            self.hand_eye_configuration.eye_in_hand
        )
        self.markers_in_camera_frame_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.markers_in_robot_base_frame_pose_widget.on_eye_in_hand_toggled(self.hand_eye_configuration.eye_in_hand)
        self.markers_in_robot_base_frame_pose_widget.set_title(
            f"Marker Poses In Robot {('Base' if self.hand_eye_configuration.eye_in_hand else 'Tool')} Frame"
        )
        self.detection_visualization_widget.on_hand_eye_configuration_updated(self.hand_eye_configuration)

    def confirm_robot_pose(self):
        self.update_instructions(
            has_set_object_poses_in_robot_frame=self.has_set_object_poses_in_robot_frame, robot_pose_confirmed=True
        )

    def on_confirm_robot_pose_button_clicked(self):
        self.confirm_robot_pose()

    def on_robot_pose_manually_updated(self):
        self.calculate_calibration_object_in_camera_frame_pose()
        self.update_instructions(
            has_set_object_poses_in_robot_frame=self.has_set_object_poses_in_robot_frame, robot_pose_confirmed=False
        )
        self.update_projection.emit(True)

    def on_actual_pose_updated(self, robot_target: RobotTarget):
        self.robot_pose_widget.set_transformation_matrix(robot_target.pose)
        self.confirm_robot_pose()
        self.calculate_calibration_object_in_camera_frame_pose()
        self.update_projection.emit(True)

    def on_target_pose_updated(self, robot_target: RobotTarget):
        self.robot_pose_widget.set_transformation_matrix(robot_target.pose)
        self.has_confirmed_robot_pose = False
        self.calculate_calibration_object_in_camera_frame_pose()
        self.update_projection.emit(True)

    def process_capture(self, frame: zivid.Frame, rgba: NDArray[Shape["N, M, 4"], UInt8], settings: SettingsPixelMappingIntrinsics):  # type: ignore
        self.detected_markers = {}
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

        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            self.calibration_board_in_camera_frame_pose_widget.set_transformation_matrix(
                TransformationMatrix.from_matrix(np.asarray(detection_result.pose().to_matrix()))
            )
        else:
            self.detected_markers = generate_marker_dictionary(detection_result.detected_markers())
            self.detected_marker_points_in_camera_frame = extract_marker_points_in_camera_frame(self.detected_markers)
            self.detected_marker_poses_in_camera_frame = {
                key: TransformationMatrix.from_matrix(np.asarray(value.pose.to_matrix()))
                for key, value in self.detected_markers.items()
            }
        self.markers_in_camera_frame_pose_widget.set_markers(self.detected_marker_poses_in_camera_frame)
        self.calculate_calibration_object_in_robot_frame_pose()
        rgb = rgba[:, :, :3].copy().astype(np.uint8)
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            pose = detection_result.pose()
            camera_pose = TransformationMatrix.from_matrix(np.asarray(pose.to_matrix()))
            rgba[:, :, :3] = self.cv2_handler.draw_projected_axis_cross(settings.intrinsics, rgb, camera_pose)
        else:
            detected_markers = detection_result.detected_markers()
            rgba[:, :, :3] = self.cv2_handler.draw_detected_markers(detected_markers, rgb, settings.pixel_mapping)
        self.detection_visualization_widget.set_rgba_image(rgba)

    def generate_projector_image(self, camera: zivid.Camera):
        points_in_camera_frame = (
            create_board_in_camera_frame(self.calibration_board_in_camera_frame_pose_widget.transformation_matrix)
            if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard
            else self.detected_marker_points_in_camera_frame
        )
        projector_pixels = np.asarray(
            zivid.projection.pixels_from_3d_points(camera, points_in_camera_frame.reshape([-1, 3]))
        )
        projector_resolution = zivid.projection.projector_resolution(camera)
        background_color = (0, 0, 0, 255)
        projector_image = np.full(
            (projector_resolution[0], projector_resolution[1], len(background_color)), background_color, dtype=np.uint8
        )
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Markers:
            grouped_projector_pixels = projector_pixels.reshape((-1, 4, 2))
            grouped_projector_pixels[np.isnan(grouped_projector_pixels).any(axis=(1, 2))] = np.nan
            projector_pixels = grouped_projector_pixels.reshape((-1, 2))
        non_nan_projector_pixels = projector_pixels[~np.isnan(projector_pixels).any(axis=1)]
        non_nan_projector_image_indices = np.round(non_nan_projector_pixels).astype(int)
        color = (0, 255, 0, 255) if self.has_confirmed_robot_pose else (0, 255, 255, 255)
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            self.cv2_handler.draw_circles(projector_image, non_nan_projector_image_indices, color)
        else:
            self.cv2_handler.draw_polygons(projector_image, non_nan_projector_image_indices, color=color)
        # projector_image[0, 0] = [1, 1, 1, 255]  # TODO(ZIVID-8760): Remove workaround
        return projector_image

    def calculate_calibration_object_in_camera_frame_pose(self):
        hand_eye_transform = self.hand_eye_pose_widget.transformation_matrix
        robot_transform = self.robot_pose_widget.transformation_matrix
        camera_frame_transform = (
            hand_eye_transform.inv() * robot_transform.inv()
            if self.hand_eye_configuration.eye_in_hand
            else hand_eye_transform.inv() * robot_transform
        )
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            cb_robot_frame = self.calibration_board_in_robot_base_frame_pose_widget.transformation_matrix
            cb_camera = camera_frame_transform * cb_robot_frame
            self.calibration_board_in_camera_frame_pose_widget.set_transformation_matrix(cb_camera)
        elif len(self.detected_markers) > 0:
            self.detected_marker_points_in_camera_frame = camera_frame_transform.transform(
                self.detected_marker_points_in_robot_frame
            )
            self.detected_marker_poses_in_camera_frame = {
                key: camera_frame_transform * value for key, value in self.detected_marker_poses_in_robot_frame.items()
            }
            self.markers_in_camera_frame_pose_widget.set_markers(self.detected_marker_poses_in_camera_frame)

    def calculate_calibration_object_in_robot_frame_pose(self):
        if self.has_confirmed_robot_pose:
            self.update_instructions(
                has_set_object_poses_in_robot_frame=True, robot_pose_confirmed=self.has_confirmed_robot_pose
            )
            hand_eye_transform = self.hand_eye_pose_widget.transformation_matrix
            robot_transform = self.robot_pose_widget.transformation_matrix
            robot_frame_transform = (
                robot_transform * hand_eye_transform
                if self.hand_eye_configuration.eye_in_hand
                else robot_transform.inv() * hand_eye_transform
            )
            if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
                cb_camera = self.calibration_board_in_camera_frame_pose_widget.transformation_matrix
                cb_robot_frame = robot_frame_transform * cb_camera
                self.calibration_board_in_robot_base_frame_pose_widget.set_transformation_matrix(cb_robot_frame)
            else:
                self.detected_marker_points_in_robot_frame = robot_frame_transform.transform(
                    self.detected_marker_points_in_camera_frame
                )
                self.detected_marker_poses_in_robot_frame = {
                    key: robot_frame_transform * value
                    for key, value in self.detected_marker_poses_in_camera_frame.items()
                }
                self.markers_in_robot_base_frame_pose_widget.set_markers(self.detected_marker_poses_in_robot_frame)

    def set_hand_eye_transformation_matrix(self, transformation_matrix: TransformationMatrix):
        self.hand_eye_pose_widget.set_transformation_matrix(transformation_matrix)
        self.calculate_calibration_object_in_camera_frame_pose()
        self.update_projection.emit(True)

    def set_save_directory(self, data_directory: Path):
        if self.data_directory != data_directory:
            self.data_directory = data_directory
            self.hand_eye_pose_widget.set_yaml_path_and_save(self.data_directory / "hand_eye_transform.yaml")
            self.robot_pose_widget.set_yaml_path_and_save(self.data_directory / "robot_pose.yaml")
            self.calibration_board_in_camera_frame_pose_widget.set_yaml_path_and_save(
                self.data_directory / "calibration_object_in_camera_frame_pose.yaml"
            )
            self.calibration_board_in_robot_base_frame_pose_widget.set_yaml_path_and_save(
                self.data_directory / "calibration_object_in_robot_base_frame_pose.yaml"
            )

    def set_load_directory(self, data_directory: Path):
        self.data_directory = Path(data_directory)
        self.hand_eye_pose_widget.set_yaml_path_and_load(self.data_directory / "hand_eye_transform.yaml")
        self.robot_pose_widget.set_yaml_path_and_load(self.data_directory / "robot_pose.yaml")
        self.calibration_board_in_camera_frame_pose_widget.set_yaml_path_and_load(
            self.data_directory / "calibration_object_in_camera_frame_pose.yaml"
        )
        self.calibration_board_in_robot_base_frame_pose_widget.set_yaml_path_and_load(
            self.data_directory / "calibration_object_in_robot_base_frame_pose.yaml"
        )

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        widgets: List[QWidget] = []
        widgets.extend(self.robot_pose_widget.get_tab_widgets_in_order())
        widgets.append(self.confirm_robot_pose_button)
        widgets.extend(self.hand_eye_pose_widget.get_tab_widgets_in_order())
        return widgets
