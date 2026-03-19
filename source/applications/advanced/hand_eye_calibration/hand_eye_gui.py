"""
Hand-Eye Calibration GUI

This script provides a graphical user interface for performing hand-eye calibration
and verification through various methods.

The application is structured as:
  1. A configuration wizard (camera, hand-eye type, markers, robot, settings)
  2. Three main tabs:
     - PREPARE:    Warmup + Infield Correction
     - CALIBRATE:  Hand-Eye Calibration
     - VERIFY:     Touch, Projection, and Stitching
  3. Shared panels: live 2D preview, tutorial steps, camera/robot controls

All event handling, signal wiring, and business logic lives in HandEyeAppBase.
This script shows the high-level application structure.

Note: This script requires the `zividsamples` package to be installed.
The `zividsamples` package is available in the /modules folder in the
`zivid-python-samples` repository. `pip install /path/to/zivid-python-samples/modules`

"""

import sys
from typing import List, Optional

import zivid
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from zividsamples.gui.calibration.hand_eye_calibration_gui import HandEyeCalibrationGUI
from zividsamples.gui.hand_eye_app import HandEyeAppBase
from zividsamples.gui.preparation.infield_correction_gui import InfieldCorrectionGUI
from zividsamples.gui.preparation.warmup_gui import WarmUpGUI
from zividsamples.gui.qt_application import ZividQtApplication
from zividsamples.gui.robot.robot_control_widget import RobotControlWidget
from zividsamples.gui.verification.hand_eye_verification_gui import HandEyeVerificationGUI
from zividsamples.gui.verification.stitch_gui import StitchGUI
from zividsamples.gui.verification.touch_gui import TouchGUI
from zividsamples.gui.widgets.camera_buttons_widget import CameraButtonsWidget
from zividsamples.gui.widgets.cv2_handler import CV2Handler
from zividsamples.gui.widgets.live_2d_widget import Live2DWidget
from zividsamples.gui.widgets.tutorial_widget import TutorialWidget
from zividsamples.gui.wizard.camera_selection import select_camera
from zividsamples.gui.wizard.data_directory import DataDirectoryManager
from zividsamples.gui.wizard.hand_eye_configuration import (
    CalibrationObject,
    select_hand_eye_configuration,
)
from zividsamples.gui.wizard.marker_configuration import MarkerConfiguration, select_marker_configuration
from zividsamples.gui.wizard.robot_configuration import select_robot_configuration
from zividsamples.gui.wizard.rotation_format_configuration import select_rotation_format


class HandEyeGUI(HandEyeAppBase):  # pylint: disable=too-many-instance-attributes
    def __init__(self, zivid_app: zivid.Application, parent=None):  # noqa: ANN001
        super().__init__(parent)

        self.zivid_app = zivid_app
        self.previous_tab_widget: Optional[QWidget] = None

        self.configuration_wizard()
        self.create_widgets()
        self.setup_layout()
        self.initialize()

    # -- Configuration Wizard ----------------------------------------------------------

    def configuration_wizard(self) -> None:
        self.data_directory_manager = DataDirectoryManager()
        if self.data_directory_manager.show_on_startup():
            self.data_directory_manager.select_folder()
        else:
            self.data_directory_manager.start_new_session()

        self.camera = select_camera(self.zivid_app, connect=True)
        self.hand_eye_configuration = select_hand_eye_configuration()
        self.marker_configuration = (
            select_marker_configuration()
            if self.hand_eye_configuration.calibration_object == CalibrationObject.Markers
            else MarkerConfiguration()
        )
        self.robot_configuration = select_robot_configuration()
        self.rotation_information = select_rotation_format()
        self.configure_settings()

    # -- Widget & Tab Creation ---------------------------------------------------------

    def create_widgets(self) -> None:
        self.central_widget = QWidget()
        cv2_handler = CV2Handler()

        # --- PREPARE tab: Warmup + Infield Correction ---
        self.preparation_tab_widget = QTabWidget()
        self.preparation_tab_widget.setObjectName("preparation_tab_widget")

        self.warmup_gui = WarmUpGUI(data_directory=self.data_directory_manager.folder("Warmup"))
        self.warmup_gui.setObjectName("Warmup")
        self.preparation_tab_widget.addTab(self.warmup_gui, "Warmup")

        self.infield_correction_gui = InfieldCorrectionGUI(
            data_directory=self.data_directory_manager.folder("Infield"),
            hand_eye_configuration=self.hand_eye_configuration,
            cv2_handler=cv2_handler,
            get_camera=lambda: self.camera,
        )
        self.infield_correction_gui.setObjectName("Infield")
        self.preparation_tab_widget.addTab(self.infield_correction_gui, "Infield Correction")

        # --- CALIBRATE tab ---
        self.hand_eye_calibration_gui = HandEyeCalibrationGUI(
            data_directory=self.data_directory_manager.folder("Calibration"),
            robot_configuration=self.robot_configuration,
            hand_eye_configuration=self.hand_eye_configuration,
            marker_configuration=self.marker_configuration,
            cv2_handler=cv2_handler,
            initial_rotation_information=self.rotation_information,
        )
        self.hand_eye_calibration_gui.setObjectName("Calibration")

        # --- VERIFY tab: Touch + Projection + Stitching ---
        self.verification_tab_widget = QTabWidget()
        self.verification_tab_widget.setObjectName("verification_tab_widget")

        self.touch_gui = TouchGUI(
            data_directory=self.data_directory_manager.folder("Touch"),
            hand_eye_configuration=self.hand_eye_configuration,
            initial_rotation_information=self.rotation_information,
        )
        self.touch_gui.setObjectName("Touch")
        if self.robot_configuration.can_control():
            self.verification_tab_widget.addTab(self.touch_gui, "by Touching")

        self.hand_eye_verification_gui = HandEyeVerificationGUI(
            data_directory=self.data_directory_manager.folder("Projection"),
            robot_configuration=self.robot_configuration,
            hand_eye_configuration=self.hand_eye_configuration,
            marker_configuration=self.marker_configuration,
            cv2_handler=cv2_handler,
            initial_rotation_information=self.rotation_information,
        )
        self.hand_eye_verification_gui.setObjectName("Projection")
        self.verification_tab_widget.addTab(self.hand_eye_verification_gui, "with Projection")

        self.stitch_gui = StitchGUI(
            data_directory=self.data_directory_manager.folder("Stitching"),
            robot_configuration=self.robot_configuration,
            hand_eye_configuration=self.hand_eye_configuration,
            initial_rotation_information=self.rotation_information,
        )
        self.stitch_gui.setObjectName("Stitching")
        self.verification_tab_widget.addTab(self.stitch_gui, "by Stitching")

        # --- Main tab bar (PREPARE / CALIBRATE / VERIFY) ---
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setObjectName("main_tab_widget")
        self.main_tab_widget.addTab(self.preparation_tab_widget, "PREPARE")
        self.main_tab_widget.addTab(self.hand_eye_calibration_gui, "CALIBRATE")
        self.main_tab_widget.addTab(self.verification_tab_widget, "VERIFY")

        # --- Shared widgets ---
        if self.camera is None or self.camera.state.connected is False:
            self.live2d_widget = Live2DWidget()
        else:
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

        self.robot_control_widget = RobotControlWidget(
            get_user_pose=self.get_transformation_matrix, robot_configuration=self.robot_configuration
        )
        self.robot_control_widget.show_buttons(auto_run=True, touch=False)

        self.camera_buttons = CameraButtonsWidget(capture_button_text="Capture (F5)")
        self.camera_buttons.set_connection_status(self.camera)

        self.projection_error_dialog = QMessageBox(self)
        self.projection_error_dialog.setWindowTitle("Projection")
        self.projection_error_dialog.setIcon(QMessageBox.Critical)
        self.projection_error_dialog.setStandardButtons(QMessageBox.Ok)

        self.setup_instructions()
        self.tutorial_widget = TutorialWidget()
        self.tutorial_widget.setMinimumWidth(600)

        self.tab_widgets: List[QWidget] = [
            self.warmup_gui,
            self.infield_correction_gui,
            self.hand_eye_calibration_gui,
            self.hand_eye_verification_gui,
            self.stitch_gui,
            self.touch_gui,
        ]

        self.setCentralWidget(self.central_widget)

    # -- Layout ------------------------------------------------------------------------

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
        self.robot_control_widget.setVisible(self.robot_configuration.can_get_pose())


def _main() -> None:
    with ZividQtApplication() as qt_app:
        sys.exit(qt_app.run(HandEyeGUI(qt_app.zivid_app), "Hand-Eye GUI"))


if __name__ == "__main__":  # NOLINT
    _main()
