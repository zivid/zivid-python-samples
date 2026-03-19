"""Base class for the Hand-Eye Calibration GUI application.

Contains all event handling, signal wiring, toolbar creation, auto-run state machine,
projection logic, and camera management. Subclass this and implement the "essence"
methods (configuration_wizard, create_widgets, setup_layout) to build the GUI.
"""

import functools
import time
from enum import Enum
from typing import Dict, List, Optional

import zivid
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QWidget,
)
from zividsamples.gui.calibration.hand_eye_calibration_gui import HandEyeCalibrationGUI
from zividsamples.gui.preparation.infield_correction_gui import InfieldCorrectionGUI
from zividsamples.gui.preparation.warmup_gui import WarmUpGUI
from zividsamples.gui.robot.robot_control import RobotTarget
from zividsamples.gui.robot.robot_control_widget import RobotControlWidget
from zividsamples.gui.verification.hand_eye_verification_gui import HandEyeVerificationGUI
from zividsamples.gui.verification.stitch_gui import StitchGUI
from zividsamples.gui.verification.touch_gui import TouchGUI
from zividsamples.gui.widgets.camera_buttons_widget import CameraButtonsWidget
from zividsamples.gui.widgets.live_2d_widget import Live2DWidget
from zividsamples.gui.widgets.tutorial_widget import TutorialWidget
from zividsamples.gui.wizard.camera_selection import select_camera
from zividsamples.gui.wizard.data_directory import DataDirectoryManager
from zividsamples.gui.wizard.hand_eye_configuration import (
    HandEyeConfiguration,
    select_hand_eye_configuration,
)
from zividsamples.gui.wizard.marker_configuration import MarkerConfiguration, select_marker_configuration
from zividsamples.gui.wizard.robot_configuration import RobotConfiguration, select_robot_configuration
from zividsamples.gui.wizard.rotation_format_configuration import RotationInformation, select_rotation_format
from zividsamples.gui.wizard.settings_selector import SettingsForHandEyeGUI, select_settings_for_hand_eye
from zividsamples.transformation_matrix import TransformationMatrix


class AutoRunState(Enum):
    INACTIVE = 0
    HOMING = 1
    RUNNING = 2
    CALIBRATING = 3
    STOPPING = 4


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class HandEyeAppBase(QMainWindow):
    """Base class providing all event handling and business logic for the Hand-Eye GUI.

    Subclasses must implement:
      - configuration_wizard()  -- run startup configuration dialogs
      - create_widgets()        -- create tab widgets, live2d, robot control, etc.
      - setup_layout()          -- arrange widgets in the window
    """

    # Attributes set by subclass in create_widgets / configuration_wizard
    zivid_app: zivid.Application
    camera: Optional[zivid.Camera]
    data_directory_manager: DataDirectoryManager
    settings: SettingsForHandEyeGUI
    hand_eye_configuration: HandEyeConfiguration
    marker_configuration: MarkerConfiguration
    robot_configuration: RobotConfiguration
    rotation_information: RotationInformation
    auto_run_state: AutoRunState
    robot_pose: TransformationMatrix
    projection_handle: Optional[zivid.projection.ProjectedImage]
    last_frame: Optional[zivid.Frame]
    common_instructions: Dict[str, bool]
    projection_error_dialog: QMessageBox
    tab_widgets: List[QWidget]

    # Toolbar actions (created in create_toolbar)
    directory_load_session_action: QAction
    directory_new_session_action: QAction
    save_frame_action: QAction
    select_hand_eye_configuration_action: QAction
    select_marker_configuration_action: QAction
    set_fixed_objects_action: QAction
    select_hand_eye_settings_action: QAction
    select_robot_configuration_action: QAction
    select_rotation_format_action: QAction
    toggle_advanced_view_action: QAction

    _SESSION_DATA_LOADED_TOOLTIP = "Start a new session to capture new Hand Eye Calibration data"

    # Widgets (created by subclass)
    main_tab_widget: QTabWidget
    preparation_tab_widget: QTabWidget
    verification_tab_widget: QTabWidget
    warmup_gui: WarmUpGUI
    infield_correction_gui: InfieldCorrectionGUI
    hand_eye_calibration_gui: HandEyeCalibrationGUI
    hand_eye_verification_gui: HandEyeVerificationGUI
    touch_gui: TouchGUI
    stitch_gui: StitchGUI
    live2d_widget: Live2DWidget
    robot_control_widget: RobotControlWidget
    camera_buttons: CameraButtonsWidget
    tutorial_widget: TutorialWidget
    central_widget: QWidget
    current_tab_widget: QWidget
    previous_tab_widget: Optional[QWidget]

    def initialize(self) -> None:
        """Call after configuration_wizard, create_widgets, and setup_layout."""
        self.static_configuration()
        self.create_toolbar()
        self.connect_signals()
        self.current_tab_widget = self.hand_eye_calibration_gui
        self.on_instructions_updated()
        for widget in self.tab_widgets:
            self.data_directory_manager.register_tab_widget(widget, widget.objectName())

        if self.camera:
            self.live2d_widget.update_settings_2d(self.settings.production.settings_2d3d.color, self.camera.info.model)
            self.live2d_widget.start_live_2d()

        QTimer.singleShot(0, functools.partial(self.main_tab_widget.setCurrentWidget, self.hand_eye_calibration_gui))
        QTimer.singleShot(100, self.update_tab_order)

    def static_configuration(self) -> None:
        self.auto_run_state = AutoRunState.INACTIVE
        self.robot_pose = TransformationMatrix()
        self.projection_handle = None
        self.last_frame = None
        self.common_instructions = {}

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
        self.directory_load_session_action = QAction("Load Session", self)
        self.directory_new_session_action = QAction("New Session", self)
        file_menu.addAction(self.directory_load_session_action)
        file_menu.addAction(self.directory_new_session_action)
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
        self.select_hand_eye_configuration_action = QAction("Hand-Eye", self)
        hand_eye_submenu.addAction(self.select_hand_eye_configuration_action)
        self.select_marker_configuration_action = QAction("Markers", self)
        hand_eye_submenu.addAction(self.select_marker_configuration_action)
        self.set_fixed_objects_action = QAction("Fixed Objects", self)
        hand_eye_submenu.addAction(self.set_fixed_objects_action)

        camera_submenu = config_menu.addMenu("Camera")
        self.select_hand_eye_settings_action = QAction("Settings", self)
        camera_submenu.addAction(self.select_hand_eye_settings_action)

        robot_submenu = config_menu.addMenu("Robot")
        self.select_robot_configuration_action = QAction("Control Option", self)
        robot_submenu.addAction(self.select_robot_configuration_action)
        self.select_rotation_format_action = QAction("Rotation Format", self)
        robot_submenu.addAction(self.select_rotation_format_action)

        view_menu = self.menuBar().addMenu("View")
        self.toggle_advanced_view_action = QAction("Advanced", self, checkable=True)
        self.toggle_advanced_view_action.setChecked(False)
        view_menu.addAction(self.toggle_advanced_view_action)

    def connect_signals(self) -> None:
        self.live2d_widget.camera_disconnected.connect(self.on_camera_disconnected)
        self.main_tab_widget.currentChanged.connect(self.on_tab_changed)
        self.preparation_tab_widget.currentChanged.connect(self.on_tab_changed)
        self.verification_tab_widget.currentChanged.connect(self.on_tab_changed)
        self.directory_load_session_action.triggered.connect(self.on_data_directory_load_session_action_triggered)
        self.directory_new_session_action.triggered.connect(self.on_data_directory_new_session_action_triggered)
        self.save_frame_action.triggered.connect(self.on_save_last_frame_action_triggered)
        self.select_hand_eye_configuration_action.triggered.connect(self.hand_eye_configuration_action_triggered)
        self.select_marker_configuration_action.triggered.connect(self.on_select_marker_configuration)
        self.select_hand_eye_settings_action.triggered.connect(self.on_select_hand_eye_settings_action_triggered)
        self.select_rotation_format_action.triggered.connect(self.on_select_rotation_format)
        self.set_fixed_objects_action.triggered.connect(self.on_select_fixed_objects_action_triggered)
        self.toggle_advanced_view_action.triggered.connect(self.on_toggle_advanced_view_action_triggered)
        self.select_robot_configuration_action.triggered.connect(self.on_select_robot_configuration_action_triggered)
        self.camera_buttons.capture_button_clicked.connect(self.on_capture_button_clicked)
        self.camera_buttons.connect_button_clicked.connect(self.on_connect_button_clicked)
        self.warmup_gui.warmup_finished.connect(self.on_warmup_finished)
        self.warmup_gui.warmup_start_requested.connect(self.on_warmup_start_requested)
        self.warmup_gui.instructions_updated.connect(self.on_instructions_updated)
        self.infield_correction_gui.apply_correction_button_clicked.connect(self.on_apply_correction_button_clicked)
        self.infield_correction_gui.loading_finished.connect(self._on_tab_loading_finished)
        self.infield_correction_gui.instructions_updated.connect(self.on_instructions_updated)
        self.infield_correction_gui.update_projection.connect(self.update_projection)
        self.hand_eye_calibration_gui.calibration_finished.connect(self.on_calibration_finished)
        self.hand_eye_calibration_gui.loading_finished.connect(self._on_tab_loading_finished)
        self.hand_eye_calibration_gui.instructions_updated.connect(self.on_instructions_updated)
        self.hand_eye_verification_gui.update_projection.connect(self.update_projection)
        self.hand_eye_verification_gui.instructions_updated.connect(self.on_instructions_updated)
        self.stitch_gui.instructions_updated.connect(self.on_instructions_updated)
        self.stitch_gui.loading_finished.connect(self._on_tab_loading_finished)
        self.touch_gui.instructions_updated.connect(self.on_instructions_updated)
        self.touch_gui.touch_pose_updated.connect(self.on_touch_pose_updated)
        self.robot_control_widget.robot_connected.connect(self.on_robot_connected)
        self.robot_control_widget.auto_run_toggled.connect(self.on_auto_run_toggled)
        self.robot_control_widget.target_pose_updated.connect(self.on_target_pose_updated)
        self.robot_control_widget.actual_pose_updated.connect(self.on_actual_pose_updated)

    def tab_widgets_with_robot_support(self) -> List[QWidget]:
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

    def keyPressEvent(self, a0: QKeyEvent) -> None:  # pylint: disable=invalid-name
        if a0 is not None and a0.key() == Qt.Key_F5:
            if self.camera and self.camera.state.connected:
                self.camera_buttons.on_capture_button_clicked()
        else:
            super().keyPressEvent(a0)

    def configure_settings(self, show_anyway: bool = False) -> None:
        if self.camera:
            current_settings = self.settings if hasattr(self, "settings") else None
            self.settings = select_settings_for_hand_eye(self.camera, current_settings, show_anyway)

    def setup_instructions(self) -> None:
        self.common_instructions = {
            "Connect Camera": self.camera is not None and self.camera.state.connected,
        }
        if self.robot_configuration.can_get_pose():
            self.common_instructions.update(
                {
                    "Connect Robot": self.robot_control_widget.connected,
                }
            )

    def on_capture_button_clicked(self) -> None:
        assert self.camera is not None
        self.live2d_widget.stop_live_2d()
        try:
            if self.robot_configuration.can_control():
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
            if self.current_tab_widget in [self.hand_eye_verification_gui]:
                if was_projecting:
                    self.live2d_widget.set_capture_function(self.camera.capture_2d)
                    self.update_projection(True)
                    rgba = self.live2d_widget.get_current_rgba()
                    self.current_tab_widget.process_capture(frame, rgba, self.settings.production)
            if not self.live2d_widget.is_active():
                self.live2d_widget.start_live_2d()
            if self.robot_configuration.can_control() and self.auto_run_state == AutoRunState.RUNNING:
                QApplication.processEvents()
                self.robot_control_widget.on_move_to_next_target(blocking=False)
        except RuntimeError as ex:
            if self.camera.state.connected:
                if self.robot_configuration.can_control() and self.auto_run_state != AutoRunState.INACTIVE:
                    self.finish_auto_run()
            else:
                self.on_camera_disconnected(str(ex))
        if not self.live2d_widget.is_active():
            self.live2d_widget.start_live_2d()

    def on_warmup_start_requested(self) -> None:
        self.camera_buttons.disable_buttons()
        self.live2d_widget.stop_live_2d()
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
        if self.robot_configuration.can_control() and self.auto_run_state == AutoRunState.CALIBRATING:
            self.finish_auto_run()
        if not transformation_matrix.is_identity():
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
        if self.current_tab_widget in self.tab_widgets_with_robot_support():
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
                    self.live2d_widget.set_capture_function(self.projection_handle.capture)
                except (RuntimeError, ValueError, AssertionError) as ex:
                    if not error_msg:
                        error_msg = f"Failed to project: {ex}"
                    if not self.projection_error_dialog.isVisible():
                        self.projection_error_dialog.setText(error_msg)
                        self.projection_error_dialog.show()
                    if self.camera is not None:
                        self.live2d_widget.set_capture_function(self.camera.capture_2d)
            elif self.camera is not None:
                self.live2d_widget.set_capture_function(self.camera.capture_2d)
            self.live2d_widget.start_live_2d()

    def on_tab_changed(self, _: int) -> None:
        if self.auto_run_state != AutoRunState.INACTIVE:
            self.auto_run_state = AutoRunState.STOPPING
        self.previous_tab_widget = self.current_tab_widget
        self.current_tab_widget = self.get_currently_selected_tab_widget()
        if self.previous_tab_widget == self.warmup_gui:
            self.camera_buttons.enable_buttons()
        if (self.previous_tab_widget in [self.hand_eye_verification_gui, self.infield_correction_gui]) and (
            self.current_tab_widget not in [self.hand_eye_verification_gui, self.infield_correction_gui]
        ):
            if self.projection_handle and self.projection_handle.active():
                self.live2d_widget.stop_live_2d()
                self.projection_handle.stop()
                if self.camera is not None:
                    self.live2d_widget.set_capture_function(self.camera.capture_2d)
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
            if self.robot_configuration.can_control():
                self.robot_control_widget.enable_disable_buttons(auto_run=True, touch=False)
                self.robot_control_widget.show_buttons(auto_run=True, touch=False)
        elif self.current_tab_widget == self.stitch_gui:
            self.robot_control_widget.enable_disable_buttons(auto_run=False, touch=False)
            self.robot_control_widget.show_buttons(auto_run=False, touch=False)
        elif self.current_tab_widget == self.touch_gui:
            self.robot_control_widget.enable_disable_buttons(
                auto_run=False, touch=self.robot_configuration.can_control()
            )
            self.robot_control_widget.show_buttons(auto_run=False, touch=self.robot_configuration.can_control())
        self.robot_control_widget.set_get_pose_interval(
            fast=(self.current_tab_widget != self.hand_eye_verification_gui)
        )
        self.current_tab_widget.notify_current_tab(self.current_tab_widget)
        for widget in self.tab_widgets:
            if widget is not self.current_tab_widget:
                widget.notify_current_tab(self.current_tab_widget)
        if self.current_tab_widget.is_loading():
            self.camera_buttons.disable_buttons()
        elif self._calibration_tab_has_disk_data():
            self.camera_buttons.disable_buttons(capture_tooltip=self._SESSION_DATA_LOADED_TOOLTIP)
        else:
            self.camera_buttons.enable_buttons()
        self.on_instructions_updated()
        self.update_tab_order()

    def _calibration_tab_has_disk_data(self) -> bool:
        return (
            self.current_tab_widget == self.hand_eye_calibration_gui
            and self.hand_eye_calibration_gui.pose_pair_selection_widget.loaded_from_disk
        )

    def _on_tab_loading_finished(self) -> None:
        if self.auto_run_state != AutoRunState.INACTIVE:
            return
        if self._calibration_tab_has_disk_data():
            self.camera_buttons.disable_buttons(capture_tooltip=self._SESSION_DATA_LOADED_TOOLTIP)
        elif not self.current_tab_widget.is_loading():
            self.camera_buttons.enable_buttons()

    def on_data_directory_load_session_action_triggered(self) -> None:
        self.data_directory_manager.select_folder()
        self.current_tab_widget.notify_current_tab(self.current_tab_widget)
        for widget in self.tab_widgets:
            if widget is not self.current_tab_widget:
                widget.notify_current_tab(self.current_tab_widget)
        if self.current_tab_widget.is_loading():
            self.camera_buttons.disable_buttons()

    def on_data_directory_new_session_action_triggered(self) -> None:
        self.data_directory_manager.start_new_session()
        self.current_tab_widget.notify_current_tab(self.current_tab_widget)
        for widget in self.tab_widgets:
            if widget is not self.current_tab_widget:
                widget.notify_current_tab(self.current_tab_widget)
        if self.current_tab_widget.is_loading():
            self.camera_buttons.disable_buttons()

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
        self.configure_settings(show_anyway=True)
        if self.camera:
            self.live2d_widget.update_settings_2d(self.settings.production.settings_2d3d.color, self.camera.info.model)

    def hand_eye_configuration_action_triggered(self) -> None:
        self.hand_eye_configuration = select_hand_eye_configuration(self.hand_eye_configuration, show_anyway=True)
        self.hand_eye_calibration_gui.hand_eye_configuration_update(self.hand_eye_configuration)
        self.hand_eye_verification_gui.hand_eye_configuration_update(self.hand_eye_configuration)

    def on_select_marker_configuration(self) -> None:
        self.marker_configuration = select_marker_configuration(self.marker_configuration, show_anyway=True)
        self.hand_eye_calibration_gui.marker_configuration_update(self.marker_configuration)
        self.hand_eye_verification_gui.marker_configuration_update(self.marker_configuration)

    def on_select_rotation_format(self) -> None:
        self.rotation_information = select_rotation_format(
            current_rotation_information=self.rotation_information, show_anyway=True
        )
        if self.rotation_information is not None:
            for widget in self.tab_widgets_with_robot_support():
                widget.rotation_format_update(self.rotation_information)

    def on_select_fixed_objects_action_triggered(self) -> None:
        self.hand_eye_calibration_gui.on_select_fixed_objects_action_triggered()

    def on_toggle_advanced_view_action_triggered(self, checked: bool) -> None:
        self.hand_eye_calibration_gui.toggle_advanced_view(checked)
        self.hand_eye_verification_gui.toggle_advanced_view(checked)

    def on_select_robot_configuration_action_triggered(self) -> None:
        selected_robot = select_robot_configuration(self.robot_configuration, show_anyway=True)
        if self.robot_configuration.robot_type == selected_robot:
            return
        self.robot_configuration = selected_robot
        self.setup_instructions()
        self.on_instructions_updated()
        self.robot_control_widget.robot_configuration_update(self.robot_configuration)
        if self.robot_configuration.can_control():
            if self.verification_tab_widget.indexOf(self.touch_gui) == -1:
                self.verification_tab_widget.addTab(self.touch_gui, "by Touching")
        else:
            self.verification_tab_widget.removeTab(self.verification_tab_widget.indexOf(self.touch_gui))
        for widget in self.tab_widgets:
            widget.robot_configuration_update(self.robot_configuration)

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
                self.configure_settings()
                self.live2d_widget.setMinimumHeight(
                    int(self.main_tab_widget.height() / 2),
                    aspect_ratio=self.settings.production.intrinsics.camera_matrix.cx
                    / self.settings.production.intrinsics.camera_matrix.cy,
                )
                if self.camera.state.connected:
                    self.live2d_widget.set_capture_function(self.camera.capture_2d)
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

        if self.robot_configuration.can_control() and self.auto_run_state != AutoRunState.INACTIVE:
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
        for widget in self.tab_widgets:
            widget.closeEvent(event)
        self.live2d_widget.closeEvent(event)
        self.robot_control_widget.disconnect()
        self.data_directory_manager.close_session()
        self.stitch_gui.closeEvent(event)
        super().closeEvent(event)
