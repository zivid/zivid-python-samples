"""
Hand-Eye Calibration GUI

This script provides a graphical user interface for performing hand-eye calibration
and verification through various methods.

Note: This script requires the `zividsamples` package to be installed.
The `zividsamples` package is available in the /modules folder in the
`zivid-python-samples` repository. `pip install /path/to/zivid-python-samples/modules`

"""

import sys
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

import zivid
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from zividsamples.gui.buttons_widget import CameraButtonsWidget
from zividsamples.gui.camera_selection import select_camera
from zividsamples.gui.cv2_handler import CV2Handler
from zividsamples.gui.hand_eye_calibration_gui import HandEyeCalibrationGUI
from zividsamples.gui.hand_eye_configuration import CalibrationObject, select_hand_eye_configuration
from zividsamples.gui.hand_eye_verification_gui import HandEyeVerificationGUI
from zividsamples.gui.live_2d_widget import Live2DWidget
from zividsamples.gui.marker_widget import MarkerConfiguration, select_marker_configuration
from zividsamples.gui.qt_application import ZividQtApplication
from zividsamples.gui.robot_control import RobotTarget
from zividsamples.gui.robot_control_widget import RobotControlWidget
from zividsamples.gui.rotation_format_configuration import RotationInformation, select_rotation_format
from zividsamples.gui.settings_selector import Settings, select_settings_for_hand_eye
from zividsamples.gui.stitch_gui import StitchGUI
from zividsamples.gui.touch_gui import TouchGUI
from zividsamples.gui.tutorial_widget import TutorialWidget
from zividsamples.transformation_matrix import TransformationMatrix


class AutoRunState(Enum):
    INACTIVE = 0
    HOMING = 1
    RUNNING = 2
    CALIBRATING = 3
    STOPPING = 4


class HandEyeGUI(QMainWindow):  # pylint: disable=R0902, R0904
    camera: Optional[zivid.Camera] = None
    settings: Settings = Settings()
    use_robot: bool = False
    auto_run_state: AutoRunState = AutoRunState.INACTIVE
    robot_pose: TransformationMatrix = TransformationMatrix()
    projection_handle: Optional[zivid.projection.ProjectedImage] = None
    last_frame: Optional[zivid.Frame] = None
    marker_configuration: MarkerConfiguration = MarkerConfiguration()
    rotation_information: RotationInformation = RotationInformation()
    common_instructions: Dict[str, bool] = {}

    def __init__(self, parent=None):  # noqa: ANN001
        super().__init__(parent)

        self.setup_camera()
        self.setup_settings()
        self.create_widgets()
        self.setup_layout()
        self.create_toolbar()
        self.connect_signals()

        if self.camera:
            self.live2d_widget.settings_2d = self.settings.settings_2d
            self.live2d_widget.start_live_2d()

        QTimer.singleShot(0, self.update_tab_order)

    def setup_camera(self) -> None:
        self.zivid_app = zivid.Application()
        cameras = self.zivid_app.cameras()
        if len(cameras) > 0:
            self.camera = select_camera(cameras)
        if self.camera is not None:
            self.camera.connect()

    def setup_settings(self) -> None:
        if self.camera:
            self.settings = select_settings_for_hand_eye(self.camera)

    def create_widgets(self) -> None:
        self.central_widget = QWidget()
        self.hand_eye_configuration = select_hand_eye_configuration()
        self.marker_configuration = (
            select_marker_configuration()
            if self.hand_eye_configuration.calibration_object == CalibrationObject.Markers
            else MarkerConfiguration()
        )
        self.use_robot = (
            QMessageBox.question(
                None, "Robot Control", "Do you have a robot connected?", QMessageBox.Yes | QMessageBox.No
            )
            == QMessageBox.Yes
        )
        cv2_handler = CV2Handler()
        self.rotation_information = select_rotation_format(title="Select Robot Rotation Format")
        self.tab_widget = QTabWidget()

        self.hand_eye_calibration_gui = HandEyeCalibrationGUI(
            data_directory=Path(__file__).parent,
            use_robot=self.use_robot,
            hand_eye_configuration=self.hand_eye_configuration,
            marker_configuration=self.marker_configuration,
            cv2_handler=cv2_handler,
            initial_rotation_information=self.rotation_information,
        )
        self.tab_widget.addTab(self.hand_eye_calibration_gui, "CALIBRATE")
        self.touch_gui = TouchGUI(
            data_directory=Path(__file__).parent,
            hand_eye_configuration=self.hand_eye_configuration,
            initial_rotation_information=self.rotation_information,
        )
        self.tab_widget.addTab(self.touch_gui, "VERIFY by Touching")
        if not self.use_robot:
            self.tab_widget.removeTab(self.tab_widget.indexOf(self.touch_gui))
        self.hand_eye_verification_gui = HandEyeVerificationGUI(
            data_directory=Path(__file__).parent,
            use_robot=self.use_robot,
            hand_eye_configuration=self.hand_eye_configuration,
            marker_configuration=self.marker_configuration,
            cv2_handler=cv2_handler,
            initial_rotation_information=self.rotation_information,
        )
        self.tab_widget.addTab(self.hand_eye_verification_gui, "VERIFY with Projection")
        self.stitch_gui = StitchGUI(
            data_directory=Path(__file__).parent,
            use_robot=self.use_robot,
            hand_eye_configuration=self.hand_eye_configuration,
            initial_rotation_information=self.rotation_information,
        )
        self.tab_widget.addTab(self.stitch_gui, "VERIFY by Stitching")

        capture_function = None if self.camera is None or self.camera.state.connected is False else self.camera.capture
        self.live2d_widget = Live2DWidget(capture_function=capture_function, settings_2d=self.settings.settings_2d)
        if self.camera is not None:
            self.live2d_widget.setMinimumHeight(
                int(self.tab_widget.height() / 2),
                aspect_ratio=self.settings.intrinsics.camera_matrix.cx / self.settings.intrinsics.camera_matrix.cy,
            )

        self.robot_control_widget = RobotControlWidget(get_user_pose=self.get_transformation_matrix)
        self.robot_control_widget.show_buttons(auto_run=True, touch=False)
        already_connected = False if self.camera is None else self.camera.state.connected
        self.camera_buttons = CameraButtonsWidget(already_connected=already_connected)

        self.setup_instructions()
        self.tutorial_widget = TutorialWidget()
        self.tutorial_widget.setMinimumWidth(600)
        self.on_instructions_updated()

        self.setCentralWidget(self.central_widget)

    def setup_layout(self) -> None:
        layout = QVBoxLayout(self.central_widget)
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        center_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        left_panel.addWidget(self.tab_widget)
        right_panel.addWidget(self.tutorial_widget)
        right_panel.addWidget(self.live2d_widget)
        center_layout.addLayout(left_panel)
        center_layout.addLayout(right_panel)
        layout.addLayout(center_layout)

        bottom_layout.addWidget(self.camera_buttons)
        bottom_layout.addWidget(self.robot_control_widget)
        layout.addLayout(bottom_layout)

        self.live2d_widget.setVisible(self.camera is not None)
        self.robot_control_widget.setVisible(self.use_robot)

    def update_tab_order(self) -> None:
        tab_widgets = (
            self.tab_widget.currentWidget().get_tab_widgets_in_order()
            + self.camera_buttons.get_tab_widgets_in_order()
            + self.robot_control_widget.get_tab_widgets_in_order()
        )
        for i in range(len(tab_widgets) - 1):
            self.setTabOrder(tab_widgets[i], tab_widgets[i + 1])
        tab_widgets[0].setFocus()

    def create_toolbar(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        self.load_from_directory = QAction("Load data from directory", self)
        file_menu.addAction(self.load_from_directory)
        self.save_to_directory = QAction("Choose directory to save to", self)
        file_menu.addAction(self.save_to_directory)
        self.save_frame_action = QAction("Save last capture", self)
        self.save_frame_action.setEnabled(False)
        self.save_frame_action.setToolTip("Save the last captured frame")
        self.save_frame_action.setShortcut("Ctrl+S")
        file_menu.addAction(self.save_frame_action)
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        config_menu = self.menuBar().addMenu("Configuration")
        hand_eye_submenu = config_menu.addMenu("Hand-Eye")
        hand_eye_action_group = QActionGroup(self)
        hand_eye_action_group.setExclusive(True)
        self.select_eye_in_hand_action = QAction("Eye-in-Hand", self)
        self.select_eye_in_hand_action.setCheckable(True)
        self.select_eye_in_hand_action.setChecked(self.hand_eye_configuration.eye_in_hand)
        hand_eye_action_group.addAction(self.select_eye_in_hand_action)
        hand_eye_submenu.addAction(self.select_eye_in_hand_action)
        self.select_eye_to_hand_action = QAction("Eye-to-Hand", self)
        self.select_eye_to_hand_action.setCheckable(True)
        self.select_eye_to_hand_action.setChecked(not self.hand_eye_configuration.eye_in_hand)
        hand_eye_action_group.addAction(self.select_eye_to_hand_action)
        hand_eye_submenu.addAction(self.select_eye_to_hand_action)

        calibration_object_submenu = config_menu.addMenu("Calibration Object")
        calibration_object_action_group = QActionGroup(self)
        calibration_object_action_group.setExclusive(True)
        self.select_checkerboard_action = QAction(CalibrationObject.Checkerboard.name, self)
        self.select_checkerboard_action.setCheckable(True)
        self.select_checkerboard_action.setChecked(
            self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard
        )
        calibration_object_action_group.addAction(self.select_checkerboard_action)
        calibration_object_submenu.addAction(self.select_checkerboard_action)
        self.select_markers_action = QAction(CalibrationObject.Markers.name, self)
        self.select_markers_action.setCheckable(True)
        self.select_markers_action.setChecked(
            self.hand_eye_configuration.calibration_object == CalibrationObject.Markers
        )
        calibration_object_action_group.addAction(self.select_markers_action)
        calibration_object_submenu.addAction(self.select_markers_action)

        self.select_marker_configuration_action = QAction("Markers", self)
        config_menu.addAction(self.select_marker_configuration_action)
        self.select_hand_eye_settings_action = QAction("Camera Settings", self)
        config_menu.addAction(self.select_hand_eye_settings_action)
        self.select_rotation_format_action = QAction("Select Rotation Format", self)
        config_menu.addAction(self.select_rotation_format_action)

        view_menu = self.menuBar().addMenu("View")
        self.toggle_advanced_view_action = QAction("Advanced", self, checkable=True)
        self.toggle_advanced_view_action.setChecked(False)
        view_menu.addAction(self.toggle_advanced_view_action)

        robot_menu = self.menuBar().addMenu("Robot")
        self.toggle_use_robot_action = QAction("Use Robot", self)
        self.toggle_use_robot_action.setToolTip("Toggle robot control")
        self.toggle_use_robot_action.setCheckable(True)
        self.toggle_use_robot_action.setChecked(self.use_robot)
        robot_menu.addAction(self.toggle_use_robot_action)
        self.toggle_unsafe_move_action = QAction("Enable unsafe move", self)
        self.toggle_unsafe_move_action.setToolTip("Allow moving to 'Robot Pose' after modifying it")
        self.toggle_unsafe_move_action.setCheckable(True)
        self.toggle_unsafe_move_action.setChecked(False)
        robot_menu.addAction(self.toggle_unsafe_move_action)

    def connect_signals(self) -> None:
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.load_from_directory.triggered.connect(self.on_load_from_data_directory_action_triggered)
        self.save_to_directory.triggered.connect(self.on_save_to_data_directory_action_triggered)
        self.save_frame_action.triggered.connect(self.on_save_last_frame_action_triggered)
        self.select_eye_in_hand_action.triggered.connect(self.on_hand_eye_action_triggered)
        self.select_eye_to_hand_action.triggered.connect(self.on_hand_eye_action_triggered)
        self.select_checkerboard_action.triggered.connect(
            lambda: self.on_calibration_object_action_triggered(CalibrationObject.Checkerboard)
        )
        self.select_markers_action.triggered.connect(
            lambda: self.on_calibration_object_action_triggered(CalibrationObject.Markers)
        )
        self.select_marker_configuration_action.triggered.connect(self.on_select_marker_configuration)
        self.select_hand_eye_settings_action.triggered.connect(self.on_select_hand_eye_settings_action_triggered)
        self.select_rotation_format_action.triggered.connect(self.on_select_rotation_format)
        self.toggle_advanced_view_action.triggered.connect(self.on_toggle_advanced_view_action_triggered)
        self.toggle_use_robot_action.triggered.connect(self.on_toggle_use_robot_action_triggered)
        self.toggle_unsafe_move_action.triggered.connect(self.robot_control_widget.toggle_unsafe_move)
        self.camera_buttons.capture_button_clicked.connect(self.on_capture_button_clicked)
        self.camera_buttons.connect_button_clicked.connect(self.on_connect_button_clicked)
        self.hand_eye_calibration_gui.calibration_finished.connect(self.on_calibration_finished)
        self.hand_eye_calibration_gui.instructions_updated.connect(self.on_instructions_updated)
        self.hand_eye_verification_gui.update_projection.connect(self.update_projection)
        self.hand_eye_verification_gui.instructions_updated.connect(self.on_instructions_updated)
        self.stitch_gui.instructions_updated.connect(self.on_instructions_updated)
        self.touch_gui.instructions_updated.connect(self.on_instructions_updated)
        self.touch_gui.touch_pose_updated.connect(self.on_touch_pose_updated)
        self.robot_control_widget.robot_connected.connect(self.on_robot_connected)
        self.robot_control_widget.auto_run_toggled.connect(self.on_auto_run_toggled)
        self.robot_control_widget.target_pose_updated.connect(self.on_target_pose_updated)
        self.robot_control_widget.actual_pose_updated.connect(self.on_actual_pose_updated)

    def setup_instructions(self) -> None:
        self.common_instructions = {
            "Connect Camera": self.camera is not None and self.camera.state.connected,
        }
        if self.use_robot:
            self.common_instructions.update(
                {
                    "Connect Robot": self.robot_control_widget.connected,
                }
            )

    def on_capture_button_clicked(self) -> None:
        assert self.camera is not None
        self.live2d_widget.stop_live_2d()
        try:
            if self.use_robot:
                while self.robot_control_widget.robot_is_moving():
                    time.sleep(0.1)
            was_projecting = False
            if self.tab_widget.currentWidget() == self.hand_eye_verification_gui:
                if self.projection_handle and self.projection_handle.active():
                    self.projection_handle.stop()
                    was_projecting = True
            settings_3d = (
                self.settings.settings_3d_for_hand_eye
                if self.tab_widget.currentWidget() in [self.hand_eye_calibration_gui, self.hand_eye_verification_gui]
                else self.settings.settings_3d
            )
            frame = self.camera.capture(settings_3d)
            self.last_frame = frame
            self.save_frame_action.setEnabled(True)
            frame_2d = self.camera.capture(self.settings.settings_2d)
            rgba = frame_2d.image_srgb().copy_data()
            self.tab_widget.currentWidget().process_capture(frame, rgba, self.settings)
            if self.tab_widget.currentWidget() == self.hand_eye_verification_gui:
                if was_projecting:
                    self.update_projection()
                    rgba = self.live2d_widget.get_current_rgba()
                    self.tab_widget.currentWidget().process_capture(frame, rgba, self.settings)
            if not self.live2d_widget.is_active():
                self.live2d_widget.start_live_2d()
            if self.use_robot and self.auto_run_state == AutoRunState.RUNNING:
                QApplication.processEvents()
                self.robot_control_widget.on_move_to_next_target(blocking=False)
                if self.tab_widget.currentWidget() == self.hand_eye_calibration_gui:
                    self.hand_eye_calibration_gui.on_use_data_button_clicked()
        except RuntimeError as ex:
            QMessageBox.critical(self, "Capture Error", str(ex))
            if self.use_robot and self.auto_run_state != AutoRunState.INACTIVE:
                self.finish_auto_run()
        if not self.live2d_widget.is_active():
            self.live2d_widget.start_live_2d()

    def on_calibration_finished(self, transformation_matrix: TransformationMatrix) -> None:
        if self.use_robot and self.auto_run_state == AutoRunState.CALIBRATING:
            self.finish_auto_run()
        if not transformation_matrix.is_identity():
            if (
                QMessageBox.question(None, "Calibration", "Use in Verification?", QMessageBox.Yes | QMessageBox.No)
                == QMessageBox.Yes
            ):
                self.hand_eye_verification_gui.set_hand_eye_transformation_matrix(transformation_matrix)
                self.touch_gui.set_hand_eye_transformation_matrix(transformation_matrix)
                self.stitch_gui.set_hand_eye_transformation_matrix(transformation_matrix)

    def on_auto_run_toggled(self) -> None:
        if self.auto_run_state == AutoRunState.INACTIVE:
            self.start_auto_run()
        else:
            self.auto_run_state = AutoRunState.STOPPING

    def start_auto_run(self) -> None:
        self.camera_buttons.disable_buttons()
        self.robot_control_widget.set_auto_run_active(True)
        if self.robot_control_widget.robot_is_home():
            self.auto_run_state = AutoRunState.RUNNING
            if self.tab_widget.currentWidget() == self.hand_eye_calibration_gui:
                if self.hand_eye_calibration_gui.on_start_auto_run():
                    self.on_capture_button_clicked()
                else:
                    self.finish_auto_run()
            elif self.tab_widget.currentWidget() == self.hand_eye_verification_gui:
                self.robot_control_widget.on_move_to_next_target(blocking=False)
        else:
            self.auto_run_state = AutoRunState.HOMING
            self.robot_control_widget.on_move_home()

    def finish_auto_run(self) -> None:
        self.auto_run_state = AutoRunState.INACTIVE
        self.robot_control_widget.set_auto_run_active(False)
        self.camera_buttons.enable_buttons()

    def get_transformation_matrix(self) -> TransformationMatrix:
        return self.robot_pose

    def on_instructions_updated(self) -> None:
        self.tutorial_widget.set_title("Steps")
        self.tutorial_widget.clear_steps()
        self.tutorial_widget.add_steps(self.common_instructions)
        self.tutorial_widget.add_steps(self.tab_widget.currentWidget().instruction_steps)
        self.tutorial_widget.set_description(self.tab_widget.currentWidget().description)
        self.tutorial_widget.update_text()

    def on_robot_connected(self) -> None:
        self.setup_instructions()
        self.on_instructions_updated()

    def on_actual_pose_updated(self, robot_target: RobotTarget) -> None:
        self.robot_pose = robot_target.pose
        current_widget = self.tab_widget.currentWidget()
        if current_widget is not None:
            current_widget.on_actual_pose_updated(robot_target)
        if self.robot_control_widget.robot_is_home():
            if self.auto_run_state == AutoRunState.HOMING:
                self.auto_run_state = AutoRunState.RUNNING
            elif self.auto_run_state == AutoRunState.RUNNING:
                if current_widget == self.hand_eye_calibration_gui:
                    self.auto_run_state = AutoRunState.CALIBRATING
                    self.hand_eye_calibration_gui.on_calibrate_button_clicked()
                elif current_widget == self.hand_eye_verification_gui:
                    self.auto_run_state = AutoRunState.STOPPING
        if self.auto_run_state == AutoRunState.STOPPING:
            self.finish_auto_run()
        elif self.auto_run_state == AutoRunState.RUNNING:
            if current_widget == self.hand_eye_calibration_gui:
                self.on_capture_button_clicked()
            elif current_widget == self.hand_eye_verification_gui:
                time.sleep(2)
                self.robot_control_widget.on_move_to_next_target(blocking=False)
        elif self.auto_run_state != AutoRunState.INACTIVE:
            error_message = (
                f"Expected to be home now, but arrived at {robot_target.name} {robot_target.pose}"
                if self.auto_run_state == AutoRunState.HOMING
                else f"Invalid state {self.auto_run_state} when we got pose update from robot."
            )
            QMessageBox.critical(self, "Auto-Run Error", error_message)
            self.finish_auto_run()

    def on_target_pose_updated(self, robot_target: RobotTarget) -> None:
        if self.tab_widget.currentWidget() == self.hand_eye_calibration_gui:
            self.hand_eye_calibration_gui.on_target_pose_updated(robot_target)
        elif self.tab_widget.currentWidget() == self.hand_eye_verification_gui:
            self.hand_eye_verification_gui.on_target_pose_updated(robot_target)

    def on_touch_pose_updated(self, touch_target: TransformationMatrix) -> None:
        self.robot_control_widget.set_touch_target(touch_target)

    def update_projection(self) -> None:
        if (
            self.tab_widget.currentWidget() == self.hand_eye_verification_gui
            and self.camera is not None
            and self.camera.state.connected
        ):
            self.live2d_widget.stop_live_2d()
            self.robot_control_widget.enable_disable_buttons(auto_run=True, touch=False)
            error_msg = None
            try:
                if self.camera is None:
                    raise RuntimeError("No camera connected.")
                try:
                    projector_image = self.hand_eye_verification_gui.generate_projector_image(self.camera)
                except ValueError as ex:
                    error_msg = f"Failed to generate projector image: {ex}. Most likely the estimated position of the calibration object is out of view."
                    raise ValueError(ex) from ex
                self.projection_handle = zivid.projection.show_image_bgra(self.camera, projector_image)
                assert self.projection_handle is not None
                self.live2d_widget.capture_function = self.projection_handle.capture
            except (RuntimeError, ValueError, AssertionError) as ex:
                if not error_msg:
                    error_msg = f"Failed to project: {ex}"
                QMessageBox.critical(self, "Projection", error_msg)
                if self.camera is not None:
                    self.live2d_widget.capture_function = self.camera.capture
            self.live2d_widget.start_live_2d()

    def on_tab_changed(self, _: int) -> None:
        if self.auto_run_state != AutoRunState.INACTIVE:
            self.auto_run_state = AutoRunState.STOPPING
        current_widget = self.tab_widget.currentWidget()
        if current_widget != self.hand_eye_verification_gui:
            if self.projection_handle and self.projection_handle.active():
                self.live2d_widget.stop_live_2d()
                self.projection_handle.stop()
                if self.camera is not None:
                    self.live2d_widget.capture_function = self.camera.capture
                self.live2d_widget.start_live_2d()
        if current_widget == self.hand_eye_calibration_gui:
            self.robot_control_widget.enable_disable_buttons(auto_run=True, touch=False)
            self.robot_control_widget.show_buttons(auto_run=True, touch=False)
        elif current_widget == self.hand_eye_verification_gui:
            self.update_projection()
            if self.use_robot:
                self.robot_control_widget.enable_disable_buttons(auto_run=True, touch=False)
                self.robot_control_widget.show_buttons(auto_run=True, touch=False)
        elif current_widget == self.stitch_gui:
            self.robot_control_widget.enable_disable_buttons(auto_run=False, touch=False)
            self.robot_control_widget.show_buttons(auto_run=False, touch=False)
        elif current_widget == self.touch_gui:
            self.robot_control_widget.enable_disable_buttons(auto_run=False, touch=True)
            self.robot_control_widget.show_buttons(auto_run=False, touch=True)
        if current_widget == self.stitch_gui:
            self.stitch_gui.start_3d_visualizer()
        else:
            self.stitch_gui.stop_3d_visualizer()
        self.on_instructions_updated()
        self.update_tab_order()

    def on_load_from_data_directory_action_triggered(self) -> None:
        data_directory = QFileDialog.getExistingDirectory(
            self, "Select Data Directory", self.tab_widget.currentWidget().data_directory.resolve().as_posix()
        )
        if not data_directory:
            return
        self.tab_widget.currentWidget().set_load_directory(data_directory)

    def on_save_to_data_directory_action_triggered(self) -> None:
        data_directory = Path(
            QFileDialog.getExistingDirectory(
                self, "Select Data Directory", self.tab_widget.currentWidget().data_directory.resolve().as_posix()
            )
        )
        self.tab_widget.currentWidget().set_save_directory(data_directory)

    def on_save_last_frame_action_triggered(self) -> None:
        if self.last_frame is not None:
            file_name = QFileDialog.getSaveFileName(
                caption="Save Capture",
                directory=self.tab_widget.currentWidget()
                .data_directory.joinpath("last_capture.zdf")
                .resolve()
                .as_posix(),
                filter="Zivid Frame (*.zdf *.ply *.pcd *.xyz)",
            )[0]
            self.last_frame.save(file_name)
        else:
            QMessageBox.warning(self, "Save Capture", "No capture to save.")

    def on_select_hand_eye_settings_action_triggered(self) -> None:
        self.setup_settings()
        self.live2d_widget.settings_2d = self.settings.settings_2d

    def on_hand_eye_action_triggered(self, action: QAction) -> None:
        self.hand_eye_configuration.eye_in_hand = action == self.select_eye_in_hand_action
        self.hand_eye_calibration_gui.hand_eye_configuration_update(self.hand_eye_configuration)
        self.hand_eye_verification_gui.hand_eye_configuration_update(self.hand_eye_configuration)

    def on_calibration_object_action_triggered(self, calibration_object: CalibrationObject) -> None:
        self.hand_eye_configuration.calibration_object = calibration_object
        self.hand_eye_calibration_gui.hand_eye_configuration_update(self.hand_eye_configuration)
        self.hand_eye_verification_gui.hand_eye_configuration_update(self.hand_eye_configuration)

    def on_select_marker_configuration(self) -> None:
        self.marker_configuration = select_marker_configuration(self.marker_configuration)
        self.hand_eye_calibration_gui.marker_configuration_update(self.marker_configuration)
        self.hand_eye_verification_gui.marker_configuration_update(self.marker_configuration)

    def on_select_rotation_format(self) -> None:
        self.rotation_information = select_rotation_format(current_rotation_format=self.rotation_information)
        if self.rotation_information is not None:
            for i in range(self.tab_widget.count()):
                self.tab_widget.widget(i).rotation_format_update(self.rotation_information)

    def on_toggle_advanced_view_action_triggered(self, checked: bool) -> None:
        self.hand_eye_calibration_gui.toggle_advanced_view(checked)
        self.hand_eye_verification_gui.toggle_advanced_view(checked)

    def on_toggle_use_robot_action_triggered(self, checked: bool) -> None:
        self.use_robot = checked
        self.setup_instructions()
        self.on_instructions_updated()
        self.robot_control_widget.setVisible(self.use_robot)
        self.hand_eye_calibration_gui.toggle_use_robot(self.use_robot)
        if self.use_robot:
            self.tab_widget.addTab(self.touch_gui, "VERIFY by Touching")
        else:
            self.tab_widget.removeTab(self.tab_widget.indexOf(self.touch_gui))
        for i in range(self.tab_widget.count()):
            self.tab_widget.widget(i).toggle_use_robot(checked)

    def on_connect_button_clicked(self) -> None:
        if self.camera is not None and self.camera.state.connected:
            self.live2d_widget.stop_live_2d()
            self.live2d_widget.hide()
            self.camera.disconnect()
            self.camera_buttons.set_connection_status(False)
        else:
            self.camera = select_camera(self.zivid_app.cameras())
            if self.camera is None:
                self.camera_buttons.set_connection_status(False)
            else:
                self.camera.connect()
                self.camera_buttons.set_connection_status(self.camera.state.connected)
                self.setup_settings()
                self.live2d_widget.setMinimumHeight(
                    int(self.tab_widget.height() / 2),
                    aspect_ratio=self.settings.intrinsics.camera_matrix.cx / self.settings.intrinsics.camera_matrix.cy,
                )
                if self.camera.state.connected:
                    self.live2d_widget.capture_function = self.camera.capture
                    self.live2d_widget.settings_2d = self.settings.settings_2d
                    self.live2d_widget.show()
                    self.live2d_widget.start_live_2d()

    def closeEvent(self, event: QCloseEvent) -> None:  # pylint: disable=C0103
        self.live2d_widget.closeEvent(event)
        super().closeEvent(event)


def _main() -> None:
    qt_app = ZividQtApplication()

    sys.exit(qt_app.run(HandEyeGUI(), "Hand-Eye GUI"))


if __name__ == "__main__":  # NOLINT
    _main()
