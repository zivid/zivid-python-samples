"""
Convert between different rotation formats with a GUI:

- AxisAngle
- Rotation Vector
- Roll-Pitch-Yaw (Euler angles)
- Quaternion

"""

from pathlib import Path

from PyQt5.QtWidgets import QAction, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget
from zividsamples.gui.pose_widget import PoseWidget, PoseWidgetDisplayMode
from zividsamples.gui.qt_application import ZividQtApplication
from zividsamples.gui.rotation_format_configuration import RotationInformation
from zividsamples.paths import get_image_file_path


class PoseConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("PoseConverter")

        display_mode = PoseWidgetDisplayMode.Basic

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        input_format = RotationInformation()
        output_format = RotationInformation()

        horizontal_layout = QHBoxLayout(central_widget)
        self.left_panel = QVBoxLayout()
        self.right_panel = QVBoxLayout()
        horizontal_layout.addLayout(self.left_panel)
        horizontal_layout.addLayout(self.right_panel)

        self.create_toolbar()

        robot_ee_pose_img_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-on-robot-robot-ee-pose-low-res.png"
        )
        rob_ee_pose_img_path = get_image_file_path("hand-eye-robot-and-calibration-board-rob-ee-pose-low-res.png")
        self.input_pose_widget = PoseWidget(
            title="Input Pose",
            initial_rotation_information=input_format,
            yaml_pose_path=Path("input_pose.yaml"),
            eye_in_hand=True,
            display_mode=display_mode,
            descriptive_image_paths=(robot_ee_pose_img_path, rob_ee_pose_img_path),
            parent=self,
        )
        self.output_pose_widget = PoseWidget(
            title="Output Pose",
            initial_rotation_information=output_format,
            yaml_pose_path=Path("output_pose.yaml"),
            eye_in_hand=True,
            display_mode=display_mode,
            descriptive_image_paths=(robot_ee_pose_img_path, rob_ee_pose_img_path),
            parent=self,
        )
        self.left_panel.addWidget(self.input_pose_widget)
        self.left_panel.addWidget(self.output_pose_widget)
        self.input_pose_widget.pose_updated.connect(self.on_input_pose_updated)

    def create_toolbar(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        view_menu = self.menuBar().addMenu("View")
        self.toggle_advanced_view_action = QAction("Advanced", self, checkable=True)
        self.toggle_advanced_view_action.triggered.connect(self.on_toggle_advanced_view_action_triggered)
        view_menu.addAction(self.toggle_advanced_view_action)

    def on_input_pose_updated(self) -> None:
        self.output_pose_widget.set_transformation_matrix(self.input_pose_widget.get_transformation_matrix())

    def on_toggle_advanced_view_action_triggered(self, checked: bool) -> None:
        self.input_pose_widget.toggle_advanced_section(checked)
        self.output_pose_widget.toggle_advanced_section(checked)


if __name__ == "__main__":  # NOLINT
    with ZividQtApplication() as qt_app:
        qt_app.run(PoseConverter(), "Pose Conversion")
