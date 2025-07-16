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
from typing import Dict, List, Optional

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
from zividsamples.gui.infield_correction_gui import InfieldCorrectionGUI
from zividsamples.gui.live_2d_widget import Live2DWidget
from zividsamples.gui.marker_widget import MarkerConfiguration, select_marker_configuration
from zividsamples.gui.qt_application import ZividQtApplication
from zividsamples.gui.robot_control import RobotTarget
from zividsamples.gui.robot_control_widget import RobotControlWidget
from zividsamples.gui.rotation_format_configuration import RotationInformation, select_rotation_format
from zividsamples.gui.settings_selector import SettingsForHandEyeGUI, select_settings_for_hand_eye
from zividsamples.gui.stitch_gui import StitchGUI
from zividsamples.gui.touch_gui import TouchGUI
from zividsamples.gui.tutorial_widget import TutorialWidget
from zividsamples.gui.warmup_gui import WarmUpGUI
from zividsamples.transformation_matrix import TransformationMatrix


class AutoRunState(Enum):
    INACTIVE = 0
    HOMING = 1
    RUNNING = 2
    CALIBRATING = 3
    STOPPING = 4


class HandEyeGUI(QMainWindow):  # pylint: disable=R0902, R0904
    camera: Optional[zivid.Camera] = None
    settings: Optional[SettingsForHandEyeGUI] = None
    use_robot: bool = False
    auto_run_state: AutoRunState = AutoRunState.INACTIVE
    robot_pose: TransformationMatrix = TransformationMatrix()
    projection_handle: Optional[zivid.projection.ProjectedImage] = None
    last_frame: Optional[zivid.Frame] = None
    marker_configuration: MarkerConfiguration = MarkerConfiguration()
    rotation_information: RotationInformation = RotationInformation()
    common_instructions: Dict[str, bool] = {}

    def __init__(self, zivid_app: zivid.Application, parent=None):  # noqa: ANN001
        super().__init__(parent)

        self.zivid_app = zivid_app
        self.camera = select_camera(self.zivid_app, connect=True)
        self.previous_tab_widget: Optional[QWidget] = None
        self.setup_settings()
        self.create_widgets()
        self.setup_layout()
        self.create_toolbar()
        self.connect_signals()
        self.current_tab_widget = self.hand_eye_calibration_gui
        self.main_tab_widget.setCurrentWidget(self.hand_eye_calibration_gui)
        self.on_instructions_updated()

        if self.camera and self.settings:
            self.live2d_widget.update_settings_2d(self.settings.production.settings_2d3d.color, self.camera.info.model)
            self.live2d_widget.start_live_2d()

        QTimer.singleShot(0, self.update_tab_order)

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

        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setObjectName("main_tab_widget")

        self.preparation_tab_widget = QTabWidget()
        self.preparation_tab_widget.setObjectName("preparation_tab_widget")
        self.warmup_gui = WarmUpGUI()
        self.preparation_tab_widget.addTab(self.warmup_gui, "Warmup")
        self.infield_correction_gui = InfieldCorrectionGUI(
            data_directory=Path(__file__).parent,
            hand_eye_configuration=self.hand_eye_configuration,
            cv2_handler=cv2_handler,
            get_camera=lambda: self.camera,
        )
        self.preparation_tab_widget.addTab(self.infield_correction_gui, "Infield Correction")
        self.main_tab_widget.addTab(self.preparation_tab_widget, "PREPARE")

        self.hand_eye_calibration_gui = HandEyeCalibrationGUI(
            data_directory=Path(__file__).parent,
            use_robot=self.use_robot,
            hand_eye_configuration=self.hand_eye_configuration,
            marker_configuration=self.marker_configuration,
            cv2_handler=cv2_handler,
            initial_rotation_information=self.rotation_information,
        )
        self.main_tab_widget.addTab(self.hand_eye_calibration_gui, "CALIBRATE")

        self.verification_tab_widget = QTabWidget()
        self.verification_tab_widget.setObjectName("verification_tab_widget")
        self.touch_gui = TouchGUI(
            data_directory=Path(__file__).parent,
            hand_eye_configuration=self.hand_eye_configuration,
            initial_rotation_information=self.rotation_information,
        )
        if self.use_robot:
            self.verification_tab_widget.addTab(self.touch_gui, "by Touching")
        self.hand_eye_verification_gui = HandEyeVerificationGUI(
            data_directory=Path(__file__).parent,
            use_robot=self.use_robot,
            hand_eye_configuration=self.hand_eye_configuration,
            marker_configuration=self.marker_configuration,
            cv2_handler=cv2_handler,
            initial_rotation_information=self.rotation_information,
        )
        self.verification_tab_widget.addTab(self.hand_eye_verification_gui, "with Projection")
        self.stitch_gui = StitchGUI(
            data_directory=Path(__file__).parent,
            use_robot=self.use_robot,
            hand_eye_configuration=self.hand_eye_configuration,
            initial_rotation_information=self.rotation_information,
        )
        self.verification_tab_widget.addTab(self.stitch_gui, "by Stitching")
        self.main_tab_widget.addTab(self.verification_tab_widget, "VERIFY")

        if self.camera is None or self.camera.state.connected is False:
            self.live2d_widget = Live2DWidget()
        else:
            assert self.settings is not None
            self.live2d_widget = Live2DWidget(
                capture_function=self.camera.capture_2d,
                settings_2d=self.settings.production.settings_2d3d.color,
                camera=self.camera,
            )
            self.live2d_widget.setMinimumHeight(
                int(self.main_tab_widget.height() / 2),
                aspect_ratio=self.settings.production.intrinsics.camera_matrix.cx
                / self.settings.production.intrinsics.camera_matrix.cy,
            )

        self.robot_control_widget = RobotControlWidget(get_user_pose=self.get_transformation_matrix)
        self.robot_control_widget.show_buttons(auto_run=True, touch=False)
        self.camera_buttons = CameraButtonsWidget(capture_button_text="Capture")
        self.camera_buttons.set_connection_status(self.camera)

        self.setup_instructions()
        self.tutorial_widget = TutorialWidget()
        self.tutorial_widget.setMinimumWidth(600)

        self.setCentralWidget(self.central_widget)

    def setup_layout(self) -> None:
        layout = QVBoxLayout(self.central_widget)
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        center_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        left_panel.addWidget(self.main_tab_widget)
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
            self.current_tab_widget.get_tab_widgets_in_order()
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
        self.set_fixed_objects_action = QAction("Set Fixed Objects", self)
        config_menu.addAction(self.set_fixed_objects_action)

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
        self.live2d_widget.camera_disconnected.connect(self.on_camera_disconnected)
        self.main_tab_widget.currentChanged.connect(self.on_tab_changed)
        self.preparation_tab_widget.currentChanged.connect(self.on_tab_changed)
        self.verification_tab_widget.currentChanged.connect(self.on_tab_changed)
        self.load_from_directory.triggered.connect(self.on_load_from_data_directory_action_triggered)
        self.save_to_directory.triggered.connect(self.on_save_to_data_directory_action_triggered)
        self.save_frame_action.triggered.connect(self.on_save_last_frame_action_triggered)
        self.select_eye_in_hand_action.triggered.connect(lambda: self.on_hand_eye_action_triggered(True))
        self.select_eye_to_hand_action.triggered.connect(lambda: self.on_hand_eye_action_triggered(False))
        self.select_checkerboard_action.triggered.connect(
            lambda: self.on_calibration_object_action_triggered(CalibrationObject.Checkerboard)
        )
        self.select_markers_action.triggered.connect(
            lambda: self.on_calibration_object_action_triggered(CalibrationObject.Markers)
        )
        self.select_marker_configuration_action.triggered.connect(self.on_select_marker_configuration)
        self.select_hand_eye_settings_action.triggered.connect(self.on_select_hand_eye_settings_action_triggered)
        self.select_rotation_format_action.triggered.connect(self.on_select_rotation_format)
        self.set_fixed_objects_action.triggered.connect(self.on_select_fixed_objects_action_triggered)
        self.toggle_advanced_view_action.triggered.connect(self.on_toggle_advanced_view_action_triggered)
        self.toggle_use_robot_action.triggered.connect(self.on_toggle_use_robot_action_triggered)
        self.toggle_unsafe_move_action.triggered.connect(self.robot_control_widget.toggle_unsafe_move)
        self.camera_buttons.capture_button_clicked.connect(self.on_capture_button_clicked)
        self.camera_buttons.connect_button_clicked.connect(self.on_connect_button_clicked)
        self.warmup_gui.warmup_finished.connect(self.on_warmup_finished)
        self.warmup_gui.warmup_start_requested.connect(self.on_warmup_start_requested)
        self.warmup_gui.instructions_updated.connect(self.on_instructions_updated)
        self.infield_correction_gui.apply_correction_button_clicked.connect(self.on_apply_correction_button_clicked)
        self.infield_correction_gui.instructions_updated.connect(self.on_instructions_updated)
        self.infield_correction_gui.update_projection.connect(self.update_projection)
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

    def actual_widgets(self) -> List[QWidget]:
        return [
            self.warmup_gui,
            self.infield_correction_gui,
            self.hand_eye_calibration_gui,
            self.hand_eye_verification_gui,
            self.stitch_gui,
            self.touch_gui,
        ]

    def widgets_with_robot_support(self) -> List[QWidget]:
        return [
            self.infield_correction_gui,
            self.hand_eye_calibration_gui,
            self.hand_eye_verification_gui,
            self.stitch_gui,
            self.touch_gui,
        ]

    def get_currently_selected_tab_widget(self) -> QWidget:
        if self.main_tab_widget.currentWidget() == self.preparation_tab_widget:
            return self.preparation_tab_widget.currentWidget()
        if self.main_tab_widget.currentWidget() == self.verification_tab_widget:
            return self.verification_tab_widget.currentWidget()
        return self.main_tab_widget.currentWidget()

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
        assert self.settings is not None
        self.live2d_widget.stop_live_2d()
        try:
            if self.use_robot:
                while self.robot_control_widget.robot_is_moving():
                    time.sleep(0.1)
            was_projecting = False
            if self.current_tab_widget in [self.hand_eye_verification_gui, self.infield_correction_gui]:
                if self.projection_handle and self.projection_handle.active():
                    self.projection_handle.stop()
                    was_projecting = True
            settings = (
                self.settings.hand_eye
                if self.current_tab_widget in [self.hand_eye_calibration_gui, self.hand_eye_verification_gui]
                else (
                    self.settings.infield_correction
                    if self.current_tab_widget in [self.warmup_gui, self.infield_correction_gui]
                    else self.settings.production
                )
            )
            frame = (
                zivid.calibration.capture_calibration_board(self.camera)
                if self.current_tab_widget in [self.warmup_gui, self.infield_correction_gui]
                else self.camera.capture_2d_3d(settings.settings_2d3d)
            )
            self.last_frame = frame
            self.save_frame_action.setEnabled(True)
            frame_2d = frame.frame_2d()
            assert frame_2d
            rgba = frame_2d.image_srgb().copy_data()
            self.current_tab_widget.process_capture(frame, rgba, settings)
            if self.current_tab_widget in [self.hand_eye_verification_gui, self.infield_correction_gui]:
                if was_projecting:
                    self.update_projection(True)
                    if self.current_tab_widget == self.hand_eye_verification_gui:
                        rgba = self.live2d_widget.get_current_rgba()
                        self.current_tab_widget.process_capture(frame, rgba, self.settings.production)
            if not self.live2d_widget.is_active():
                self.live2d_widget.start_live_2d()
            if self.use_robot and self.auto_run_state == AutoRunState.RUNNING:
                QApplication.processEvents()
                self.robot_control_widget.on_move_to_next_target(blocking=False)
                if self.current_tab_widget == self.hand_eye_calibration_gui:
                    self.hand_eye_calibration_gui.on_use_data_button_clicked()
        except RuntimeError as ex:
            if self.camera.state.connected:
                if self.use_robot and self.auto_run_state != AutoRunState.INACTIVE:
                    self.finish_auto_run()
            else:
                self.on_camera_disconnected(str(ex))
        if not self.live2d_widget.is_active():
            self.live2d_widget.start_live_2d()

    def on_warmup_start_requested(self) -> None:
        self.camera_buttons.disable_buttons()
        self.live2d_widget.stop_live_2d()
        assert self.settings is not None
        self.warmup_gui.start_warmup(self.camera, self.settings.production.settings_2d3d)

    def on_warmup_finished(self, success: bool) -> None:
        self.camera_buttons.enable_buttons()
        self.live2d_widget.start_live_2d()
        if success:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Warmup Finished")
            warn_about_trueness_str = f"\n{self.warmup_gui.get_warn_about_trueness_str(self.camera)}"
            dialog.setText("Warmup is finished. What would you like to do next?" + warn_about_trueness_str)
            dialog.addButton("Stay in Warmup", QMessageBox.RejectRole)
            skip_to_calibration_button = dialog.addButton("Hand Eye Calibration", QMessageBox.AcceptRole)
            move_to_infield_button = dialog.addButton("Infield Correction", QMessageBox.YesRole)
            dialog.exec()
            if dialog.clickedButton() == move_to_infield_button:
                self.main_tab_widget.setCurrentWidget(self.preparation_tab_widget)
                self.preparation_tab_widget.setCurrentWidget(self.infield_correction_gui)
            elif dialog.clickedButton() == skip_to_calibration_button:
                self.main_tab_widget.setCurrentWidget(self.hand_eye_calibration_gui)

    def on_apply_correction_button_clicked(self) -> None:
        self.infield_correction_gui.apply_correction(self.camera)

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
            if self.current_tab_widget == self.hand_eye_calibration_gui:
                if self.hand_eye_calibration_gui.on_start_auto_run():
                    self.on_capture_button_clicked()
                else:
                    self.finish_auto_run()
            elif self.current_tab_widget == self.hand_eye_verification_gui:
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
        self.tutorial_widget.add_steps(self.current_tab_widget.instruction_steps)
        self.tutorial_widget.set_description(self.current_tab_widget.description)
        self.tutorial_widget.update_text()

    def on_robot_connected(self) -> None:
        self.setup_instructions()
        self.on_instructions_updated()

    def on_actual_pose_updated(self, robot_target: RobotTarget) -> None:
        self.robot_pose = robot_target.pose
        if self.current_tab_widget in self.widgets_with_robot_support():
            self.current_tab_widget.on_actual_pose_updated(robot_target)
        if self.robot_control_widget.robot_is_home():
            if self.auto_run_state == AutoRunState.HOMING:
                self.auto_run_state = AutoRunState.RUNNING
            elif self.auto_run_state == AutoRunState.RUNNING:
                if self.current_tab_widget == self.hand_eye_calibration_gui:
                    self.auto_run_state = AutoRunState.CALIBRATING
                    self.hand_eye_calibration_gui.on_calibrate_button_clicked()
                elif self.current_tab_widget == self.hand_eye_verification_gui:
                    self.auto_run_state = AutoRunState.STOPPING
        if self.auto_run_state == AutoRunState.STOPPING:
            self.finish_auto_run()
        elif self.auto_run_state == AutoRunState.RUNNING:
            if self.current_tab_widget == self.hand_eye_calibration_gui:
                self.on_capture_button_clicked()
            elif self.current_tab_widget == self.hand_eye_verification_gui:
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
        if self.current_tab_widget == self.hand_eye_calibration_gui:
            self.hand_eye_calibration_gui.on_target_pose_updated(robot_target)
        elif self.current_tab_widget == self.hand_eye_verification_gui:
            self.hand_eye_verification_gui.on_target_pose_updated(robot_target)

    def on_touch_pose_updated(self, touch_target: TransformationMatrix) -> None:
        self.robot_control_widget.set_touch_target(touch_target)

    def update_projection(self, project: bool = True) -> None:
        if (
            self.current_tab_widget in [self.hand_eye_verification_gui, self.infield_correction_gui]
            and self.camera is not None
            and self.camera.state.connected
        ):
            self.live2d_widget.stop_live_2d()
            if project and self.current_tab_widget.has_features_to_project():
                self.robot_control_widget.enable_disable_buttons(auto_run=True, touch=False)
                error_msg = None
                try:
                    if self.camera is None:
                        raise RuntimeError("No camera connected.")
                    try:
                        projector_image = self.current_tab_widget.generate_projector_image(self.camera)
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
                        self.live2d_widget.capture_function = self.camera.capture_2d
            elif self.camera is not None:
                self.live2d_widget.capture_function = self.camera.capture_2d
            self.live2d_widget.start_live_2d()

    def on_tab_changed(self, _: int) -> None:
        if self.auto_run_state != AutoRunState.INACTIVE:
            self.auto_run_state = AutoRunState.STOPPING
        self.previous_tab_widget = self.current_tab_widget
        self.current_tab_widget = self.get_currently_selected_tab_widget()
        if self.previous_tab_widget == self.warmup_gui:
            self.warmup_gui.stop_warmup()
            self.camera_buttons.enable_buttons()
        if (self.previous_tab_widget in [self.hand_eye_verification_gui, self.infield_correction_gui]) and (
            self.current_tab_widget not in [self.hand_eye_verification_gui, self.infield_correction_gui]
        ):
            if self.projection_handle and self.projection_handle.active():
                self.live2d_widget.stop_live_2d()
                self.projection_handle.stop()
                if self.camera is not None:
                    self.live2d_widget.capture_function = self.camera.capture_2d
                self.live2d_widget.start_live_2d()
        if self.current_tab_widget == self.infield_correction_gui:
            if self.infield_correction_gui.infield_correction_input_data is not None:
                self.update_projection(True)
            self.robot_control_widget.enable_disable_buttons(auto_run=False, touch=False)
            self.robot_control_widget.show_buttons(auto_run=False, touch=False)
            if self.camera is not None:
                self.infield_correction_gui.check_correction(self.camera)
        elif self.current_tab_widget == self.hand_eye_calibration_gui:
            self.robot_control_widget.enable_disable_buttons(auto_run=True, touch=False)
            self.robot_control_widget.show_buttons(auto_run=True, touch=False)
        elif self.current_tab_widget == self.hand_eye_verification_gui:
            self.update_projection(True)
            if self.use_robot:
                self.robot_control_widget.enable_disable_buttons(auto_run=True, touch=False)
                self.robot_control_widget.show_buttons(auto_run=True, touch=False)
        elif self.current_tab_widget == self.stitch_gui:
            self.robot_control_widget.enable_disable_buttons(auto_run=False, touch=False)
            self.robot_control_widget.show_buttons(auto_run=False, touch=False)
        elif self.current_tab_widget == self.touch_gui:
            self.robot_control_widget.enable_disable_buttons(auto_run=False, touch=True)
            self.robot_control_widget.show_buttons(auto_run=False, touch=True)
        if self.current_tab_widget == self.stitch_gui:
            self.stitch_gui.start_3d_visualizer()
        else:
            self.stitch_gui.stop_3d_visualizer()
        self.on_instructions_updated()
        self.update_tab_order()

    def on_load_from_data_directory_action_triggered(self) -> None:
        data_directory = QFileDialog.getExistingDirectory(
            self, "Select Data Directory", self.current_tab_widget.data_directory.resolve().as_posix()
        )
        if not data_directory:
            return
        self.current_tab_widget.set_load_directory(data_directory)

    def on_save_to_data_directory_action_triggered(self) -> None:
        data_directory = Path(
            QFileDialog.getExistingDirectory(
                self, "Select Data Directory", self.current_tab_widget.data_directory.resolve().as_posix()
            )
        )
        self.current_tab_widget.set_save_directory(data_directory)

    def on_save_last_frame_action_triggered(self) -> None:
        if self.last_frame is not None:
            file_name = QFileDialog.getSaveFileName(
                caption="Save Capture",
                directory=self.current_tab_widget.data_directory.joinpath("last_capture.zdf").resolve().as_posix(),
                filter="Zivid Frame (*.zdf *.ply *.pcd *.xyz)",
            )[0]
            self.last_frame.save(file_name)
        else:
            QMessageBox.warning(self, "Save Capture", "No capture to save.")

    def on_select_hand_eye_settings_action_triggered(self) -> None:
        self.setup_settings()
        if self.camera and self.settings:
            self.live2d_widget.update_settings_2d(self.settings.production.settings_2d3d.color, self.camera.info.model)

    def on_hand_eye_action_triggered(self, eye_in_hand: bool) -> None:
        self.hand_eye_configuration.eye_in_hand = eye_in_hand
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
            for widget in self.widgets_with_robot_support():
                widget.rotation_format_update(self.rotation_information)

    def on_select_fixed_objects_action_triggered(self) -> None:
        self.hand_eye_calibration_gui.on_select_fixed_objects_action_triggered()

    def on_toggle_advanced_view_action_triggered(self, checked: bool) -> None:
        self.hand_eye_calibration_gui.toggle_advanced_view(checked)
        self.hand_eye_verification_gui.toggle_advanced_view(checked)

    def on_toggle_use_robot_action_triggered(self, checked: bool) -> None:
        self.use_robot = checked
        self.setup_instructions()
        self.on_instructions_updated()
        self.robot_control_widget.setVisible(self.use_robot)
        if self.use_robot:
            self.verification_tab_widget.addTab(self.touch_gui, "by Touching")
        else:
            self.verification_tab_widget.removeTab(self.verification_tab_widget.indexOf(self.touch_gui))
        for widget in self.actual_widgets():
            widget.toggle_use_robot(checked)

    def on_connect_button_clicked(self) -> None:
        if self.camera is not None and self.camera.state.connected:
            self.live2d_widget.stop_live_2d()
            self.live2d_widget.hide()
            self.camera.disconnect()
            self.camera_buttons.set_connection_status(self.camera)
            self.live2d_widget.camera = None
        else:
            self.camera = select_camera(self.zivid_app, connect=True)
            self.live2d_widget.camera = self.camera
            self.camera_buttons.set_connection_status(self.camera)
            if self.camera:
                self.setup_settings()
                assert self.settings is not None
                self.live2d_widget.setMinimumHeight(
                    int(self.main_tab_widget.height() / 2),
                    aspect_ratio=self.settings.production.intrinsics.camera_matrix.cx
                    / self.settings.production.intrinsics.camera_matrix.cy,
                )
                if self.camera.state.connected:
                    self.live2d_widget.capture_function = self.camera.capture_2d
                    self.live2d_widget.update_settings_2d(
                        self.settings.production.settings_2d3d.color, self.camera.info.model
                    )
                    self.live2d_widget.show()
                    self.live2d_widget.start_live_2d()
        self.setup_instructions()
        self.on_instructions_updated()

    def on_camera_disconnected(self, error_message: str) -> None:
        print(f"Camera disconnected signal received {error_message}")
        if self.camera is not None:
            self.camera.disconnect()
            self.camera_buttons.set_connection_status(self.camera)
        self.live2d_widget.stop_live_2d()
        self.live2d_widget.hide()

        if self.use_robot and self.auto_run_state != AutoRunState.INACTIVE:
            self.finish_auto_run()
        if self.camera is not None:
            QMessageBox.critical(
                self,
                "Camera Disconnected",
                f"Camera disconnected unexpectedly ({self.camera.state.status})\n{error_message}",
            )
        self.camera = None
        self.setup_instructions()
        self.on_instructions_updated()

    def closeEvent(self, event: QCloseEvent) -> None:  # pylint: disable=C0103
        self.live2d_widget.closeEvent(event)
        super().closeEvent(event)


def _main() -> None:
    with ZividQtApplication() as qt_app:
        sys.exit(qt_app.run(HandEyeGUI(qt_app.zivid_app), "Hand-Eye GUI"))


if __name__ == "__main__":  # NOLINT
    _main()
