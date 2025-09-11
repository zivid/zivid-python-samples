"""
Robot Selection

Note: This script requires PyQt5 to be installed.

"""

from enum import Enum
from typing import Optional

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
)
from zividsamples.gui.qt_application import ZividQtApplication


class RobotEnum(Enum):
    NO_ROBOT = "No Robot"
    ROBODK = "RoboDK Station"
    UR_RTDE_READ_ONLY = "UR - RTDE (read-only)"


class RobotConfiguration:

    def __init__(self, *, robot_type: Optional[RobotEnum] = None, ip_addr: Optional[str] = None):
        qsettings = QSettings("Zivid", "HandEyeGUI")
        qsettings.beginGroup("robot_configuration")
        if robot_type is not None:
            self._robot_type = robot_type
        else:
            self._robot_type = RobotEnum(qsettings.value("robot_type", RobotEnum.NO_ROBOT.value))
        if ip_addr is not None:
            self.ip_addr = ip_addr
        else:
            self.ip_addr = qsettings.value("ip_addr", "172.28.60.23")
        self.allow_unsafe_move = qsettings.value("allow_unsafe_move", False, type=bool)
        self.show_dialog = qsettings.value("show_dialog", True, type=bool)
        qsettings.endGroup()

    @property
    def robot_type(self) -> RobotEnum:
        return self._robot_type

    @robot_type.setter
    def robot_type(self, value: RobotEnum):
        assert isinstance(value, RobotEnum)
        self._robot_type = value

    def has_no_robot(self) -> bool:
        return self.robot_type == RobotEnum.NO_ROBOT

    def has_robot(self) -> bool:
        return self.robot_type != RobotEnum.NO_ROBOT

    def can_get_pose(self) -> bool:
        return self.robot_type in [RobotEnum.UR_RTDE_READ_ONLY, RobotEnum.ROBODK]

    def can_control(self) -> bool:
        return self.robot_type in [RobotEnum.ROBODK]

    def save_choice(self):
        qsettings = QSettings("Zivid", "HandEyeGUI")
        qsettings.beginGroup("robot_configuration")
        qsettings.setValue("robot_type", self._robot_type.value if self._robot_type else None)
        qsettings.setValue("ip_addr", self.ip_addr)
        qsettings.setValue("show_dialog", self.show_dialog)
        qsettings.endGroup()

    def __str__(self):
        return (
            f"RobotConfiguration(robot_type={self._robot_type}, ip_addr={self.ip_addr}, show_dialog={self.show_dialog})"
        )


class RobotConfigurationDialog(QDialog):
    def __init__(self, initial_robot_configuration: RobotConfiguration = RobotConfiguration()):
        super().__init__()
        self.setWindowTitle("Select Robot Configuration")

        self.robot_configuration = initial_robot_configuration

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.robot_type_combo = QComboBox()
        self.robot_type_combo.addItems([robot.value for robot in RobotEnum])
        self.robot_type_combo.setCurrentText(self.robot_configuration._robot_type.value)
        form_layout.addRow("Robot Type:", self.robot_type_combo)

        self.ip_addr_edit = QLineEdit()
        self.ip_addr_edit.setText(self.robot_configuration.ip_addr)
        form_layout.addRow("IP Address:", self.ip_addr_edit)

        self.allow_unsafe_move_checkbox = QCheckBox("Allow Unsafe Move")
        self.allow_unsafe_move_checkbox.setChecked(self.robot_configuration.allow_unsafe_move)
        self.allow_unsafe_move_checkbox.setToolTip("Allow the robot to move through potentially unsafe configurations.")
        form_layout.addRow(self.allow_unsafe_move_checkbox)

        layout.addLayout(form_layout)

        horizontal_layout = QHBoxLayout()

        self.show_dialog_checkbox = QCheckBox("Show this dialog")
        self.show_dialog_checkbox.setChecked(self.robot_configuration.show_dialog)
        horizontal_layout.addWidget(self.show_dialog_checkbox)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        horizontal_layout.addWidget(self.button_box)

        layout.addLayout(horizontal_layout)

    def accept(self):
        self.robot_configuration.robot_type = RobotEnum(self.robot_type_combo.currentText())
        self.robot_configuration.ip_addr = self.ip_addr_edit.text()
        self.robot_configuration.show_dialog = self.show_dialog_checkbox.isChecked()
        self.robot_configuration.save_choice()
        super().accept()

    def get_robot_configuration(self) -> RobotConfiguration:
        return self.robot_configuration


def select_robot_configuration(
    initial_robot_configuration: RobotConfiguration = RobotConfiguration(), show_anyway: bool = False
) -> RobotConfiguration:
    if not initial_robot_configuration.show_dialog and not show_anyway:
        return initial_robot_configuration
    settings_selector = RobotConfigurationDialog(initial_robot_configuration)
    settings_selector.exec_()
    return settings_selector.get_robot_configuration()


if __name__ == "__main__":  # NOLINT
    with ZividQtApplication():
        robot_configuration = select_robot_configuration(show_anyway=True)
        print(f"Selected Robot Configuration: {robot_configuration}")
