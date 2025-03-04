from dataclasses import dataclass, fields
from typing import List, Tuple

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHeaderView,
    QLabel,
    QRadioButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from zividsamples.gui.qt_application import ZividQtApplication


@dataclass(frozen=True)
class RotationFormat:
    name: str
    number_of_parameters: int


@dataclass(frozen=True)
class RotationFormats:
    euler: RotationFormat = RotationFormat("Euler", 3)
    angle_axis: RotationFormat = RotationFormat("Angle-Axis", 4)
    rotation_vector: RotationFormat = RotationFormat("Rotation Vector", 3)
    quaternion: RotationFormat = RotationFormat("Quaternion", 4)
    rotation_matrix: RotationFormat = RotationFormat("Rotation Matrix", 9)

    @classmethod
    def as_list(cls) -> List[RotationFormat]:
        fields_default = []
        for field in fields(cls):
            assert isinstance(field.default, RotationFormat), f"Field {field} does not have {RotationFormat} type."
            fields_default.append(field.default)
        return fields_default


@dataclass
class RotationInformation:
    format: RotationFormat = RotationFormats.euler
    euler_variant: str = "XYZ"
    extrinsic: bool = False
    use_degrees: bool = True


@dataclass(frozen=True)
class EulerVariants:
    ProperEulerAngles: Tuple[str, ...] = ("ZXZ", "XYX", "YZY", "ZYZ", "XZX", "YXY")
    TaitBryanEulerAngles: Tuple[str, ...] = ("XYZ", "YZX", "ZXY", "XZY", "ZYX", "YXZ")
    Euler: Tuple[str, ...] = TaitBryanEulerAngles + ProperEulerAngles


class RotationFormatSelectionWidget(QWidget):
    rotation_format: RotationInformation
    rotation_format_update = pyqtSignal(RotationInformation)

    def __init__(self, initial_rotation_information: RotationInformation, parent=None):
        super().__init__(parent)

        self.rotation_format = initial_rotation_information

        self.setup_widgets()
        self.setup_layout()
        self.setup_connections()

        self.show_euler_format_selector(self.rotation_format.format == RotationFormats.euler)

    def setup_widgets(self):
        self.format_selector_label = QLabel()
        self.format_selector_label.setText("Select Rotation Format")
        self.format_selector = QComboBox()
        for rotation_format in RotationFormats.as_list():
            self.format_selector.addItem(rotation_format.name, rotation_format)
        self.format_selector.setCurrentIndex(0)
        self.euler_format_label = QLabel()
        self.euler_format_label.setText("Select Euler Format")
        self.euler_format_selector = QComboBox()
        self.euler_format_selector.addItems(list(EulerVariants.Euler))
        self.euler_format_selector.setCurrentText(self.rotation_format.euler_variant)

        self.extrinsic_radio_button = QRadioButton("Extrinsic")
        self.intrinsic_radio_button = QRadioButton("Intrinsic")
        intrinsic_extrinsic_radio_button_group = QButtonGroup(self)
        intrinsic_extrinsic_radio_button_group.addButton(self.extrinsic_radio_button)
        intrinsic_extrinsic_radio_button_group.addButton(self.intrinsic_radio_button)
        self.extrinsic_radio_button.setChecked(self.rotation_format.extrinsic)
        self.intrinsic_radio_button.setChecked(not self.rotation_format.extrinsic)

        self.degrees_radians_label = QLabel("Degrees/Radians")
        self.radians_radio_button = QRadioButton("Radians")
        self.degrees_radio_button = QRadioButton("Degrees")
        rad_deg_radio_button_group = QButtonGroup(self)
        rad_deg_radio_button_group.addButton(self.radians_radio_button)
        rad_deg_radio_button_group.addButton(self.degrees_radio_button)
        self.radians_radio_button.setChecked(not self.rotation_format.use_degrees)
        self.degrees_radio_button.setChecked(self.rotation_format.use_degrees)

    def setup_layout(self):
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.format_selector_label, 0, 0)
        self.grid_layout.addWidget(self.format_selector, 0, 1, 1, 3)
        self.grid_layout.addWidget(self.euler_format_label, 1, 0)
        self.grid_layout.addWidget(self.euler_format_selector, 1, 1)
        self.grid_layout.addWidget(self.extrinsic_radio_button, 1, 2)
        self.grid_layout.addWidget(self.intrinsic_radio_button, 1, 3)
        self.grid_layout.addWidget(self.degrees_radians_label, 2, 0)
        self.grid_layout.addWidget(self.degrees_radio_button, 2, 2)
        self.grid_layout.addWidget(self.radians_radio_button, 2, 3)

        self.setLayout(self.grid_layout)

    def setup_connections(self):
        self.format_selector.currentIndexChanged.connect(self.on_transform_format_changed)
        self.euler_format_selector.currentIndexChanged.connect(self.on_transform_format_changed)
        self.extrinsic_radio_button.toggled.connect(self.on_transform_format_changed)
        self.degrees_radio_button.toggled.connect(self.on_transform_format_changed)

    def show_euler_format_selector(self, show: bool):
        self.euler_format_label.setVisible(show)
        self.euler_format_selector.setVisible(show)
        self.extrinsic_radio_button.setVisible(show)
        self.intrinsic_radio_button.setVisible(show)

    def on_transform_format_changed(self):
        self.rotation_format.format = self.format_selector.currentData()
        self.rotation_format.extrinsic = self.extrinsic_radio_button.isChecked()
        text = self.euler_format_selector.currentText()
        self.rotation_format.euler_variant = text.lower() if self.rotation_format.extrinsic else text.upper()
        self.rotation_format.use_degrees = self.degrees_radio_button.isChecked()
        self.show_euler_format_selector(self.format_selector.currentData() == RotationFormats.euler)
        self.radians_radio_button.setHidden(
            self.format_selector.currentData() in [RotationFormats.quaternion, RotationFormats.rotation_matrix]
        )
        self.degrees_radio_button.setHidden(
            self.format_selector.currentData() in [RotationFormats.quaternion, RotationFormats.rotation_matrix]
        )
        self.degrees_radians_label.setHidden(
            self.format_selector.currentData() in [RotationFormats.quaternion, RotationFormats.rotation_matrix]
        )
        self.rotation_format_update.emit(self.rotation_format)

    def set_rotation_format(self, rotation_information: RotationInformation):
        for i in range(self.format_selector.count()):
            if self.format_selector.itemData(i) == rotation_information.format:
                self.format_selector.setCurrentIndex(i)
                break
        self.euler_format_selector.setCurrentText(rotation_information.euler_variant)
        if rotation_information.format == RotationFormats.euler:
            self.show_euler_format_selector(True)
            self.euler_format_selector.setCurrentText(rotation_information.euler_variant.upper())
            self.extrinsic_radio_button.setChecked(rotation_information.extrinsic)
            self.intrinsic_radio_button.setChecked(not rotation_information.extrinsic)
        else:
            self.show_euler_format_selector(False)
        self.degrees_radio_button.setChecked(rotation_information.use_degrees)
        self.radians_radio_button.setChecked(not rotation_information.use_degrees)
        self.on_transform_format_changed()


@dataclass
class RobotInfo:
    vendor: str
    robot: str
    rotation_information: RotationInformation


ListOfRobotFormats = [
    RobotInfo(
        "Universal Robots", "UR5e", RotationInformation(RotationFormats.euler, "XYZ", extrinsic=True, use_degrees=True)
    ),
    RobotInfo("Universal Robots", "UR5e", RotationInformation(RotationFormats.rotation_vector, use_degrees=True)),
    RobotInfo(
        "Fanuc", "R-0iB, R-30iB", RotationInformation(RotationFormats.euler, "XYZ", extrinsic=True, use_degrees=True)
    ),
    RobotInfo(
        "Fanuc",
        "M10iD12, CRX-10iA/L",
        RotationInformation(RotationFormats.euler, "XYZ", extrinsic=True, use_degrees=True),
    ),
    RobotInfo(
        "Yaskawa", "Motoman GP225", RotationInformation(RotationFormats.euler, "XYZ", extrinsic=True, use_degrees=True)
    ),
    RobotInfo("ABB", "CRB 15000", RotationInformation(RotationFormats.euler, "ZYX", extrinsic=False, use_degrees=True)),
    RobotInfo(
        "Kawasaki", "CX210L", RotationInformation(RotationFormats.euler, "ZYZ", extrinsic=False, use_degrees=True)
    ),
    RobotInfo(
        "KUKA", "KR 210 R2700", RotationInformation(RotationFormats.euler, "ZYX", extrinsic=False, use_degrees=True)
    ),
    RobotInfo("Doosan", "M1013", RotationInformation(RotationFormats.euler, "ZYZ", extrinsic=False, use_degrees=True)),
    RobotInfo(
        "Hyundai", "HA006B", RotationInformation(RotationFormats.euler, "XYZ", extrinsic=False, use_degrees=True)
    ),
    RobotInfo("Robostar", "RA007", RotationInformation(RotationFormats.euler, "XYZ", extrinsic=True, use_degrees=True)),
    RobotInfo(
        "Nachi", "MZ04D-01", RotationInformation(RotationFormats.euler, "ZYX", extrinsic=False, use_degrees=True)
    ),
]


class RotationFormatSelectionDialog(QDialog):

    def __init__(
        self, initial_rotation_information: RotationInformation, title: str = "Select Rotation Format", parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.rotation_format_selection_widget = RotationFormatSelectionWidget(initial_rotation_information)

        table = QTableWidget()
        table.setRowCount(len(ListOfRobotFormats))
        table.setColumnCount(4)

        table.setHorizontalHeaderLabels(["Vendor", "Robot", "Format", "Notes"])

        for i, robot_format in enumerate(ListOfRobotFormats):
            table.setItem(i, 0, QTableWidgetItem(robot_format.vendor))
            table.setItem(i, 1, QTableWidgetItem(robot_format.robot))
            format_text = robot_format.rotation_information.format.name
            if robot_format.rotation_information.format == RotationFormats.euler:
                format_text += f" {robot_format.rotation_information.euler_variant}"
            table.setItem(i, 2, QTableWidgetItem(format_text))
            notes = "Degrees" if robot_format.rotation_information.use_degrees else "Radians"
            if robot_format.rotation_information.format == RotationFormats.euler:
                notes += ", "
                notes += "Extrinsic" if robot_format.rotation_information.extrinsic else "Intrinsic"
            table.setItem(i, 3, QTableWidgetItem(notes))

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(table)
        layout.addWidget(self.rotation_format_selection_widget)
        layout.addWidget(button_box)
        self.setLayout(layout)
        self.setMinimumSize(1100, 500)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        table.cellClicked.connect(self.on_row_selected)

    def on_row_selected(self, row: int):
        self.rotation_format_selection_widget.set_rotation_format(ListOfRobotFormats[row].rotation_information)

    def rotation_format(self) -> RotationInformation:
        return self.rotation_format_selection_widget.rotation_format


def select_rotation_format(
    current_rotation_format: RotationInformation = RotationInformation(), title: str = "Select Rotation Format"
) -> RotationInformation:
    dialog = RotationFormatSelectionDialog(current_rotation_format, title)
    dialog.exec_()
    return dialog.rotation_format()


if __name__ == "__main__":  # NOLINT
    with ZividQtApplication(use_zivid_app=False):
        selected_rotation_format = select_rotation_format(
            current_rotation_format=ListOfRobotFormats[0].rotation_information
        )
        print(f"Selected format: {selected_rotation_format}")
