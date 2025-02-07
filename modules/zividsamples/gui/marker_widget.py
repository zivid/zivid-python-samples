import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from nptyping import Float32, NDArray, Shape, UInt8
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QImage, QPixmap, QValidator
from PyQt5.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QSpinBox, QVBoxLayout, QWidget
from scipy.spatial.transform import Rotation
from zivid.calibration import MarkerDictionary, MarkerShape
from zivid.experimental import PixelMapping
from zividsamples.gui.cv2_handler import CV2Handler
from zividsamples.gui.image_viewer import ImageViewer
from zividsamples.gui.qt_application import ZividQtApplication


def generate_marker_dictionary(markers: List[MarkerShape]) -> Dict[str, MarkerShape]:
    marker_dict = {}
    for marker in markers:
        key = str(marker.identifier)
        if key in marker_dict:
            keys_with_same_id = len([k for k in marker_dict if k.startswith(key)])
            key = f"{key}({keys_with_same_id})"
        marker_dict[key] = marker
    return marker_dict


def marker_angle(rotation_matrix: NDArray[Shape["3, 3"], Float32]) -> float:  # type: ignore
    rotation = Rotation.from_matrix(rotation_matrix)
    rotvec = rotation.as_rotvec()
    return np.degrees(np.linalg.norm(rotvec))


class TouchMarkerWidget(QWidget):
    marker_id: int = 1
    marker_dictionary: str = MarkerDictionary.aruco4x4_50

    def __init__(self, parent=None):
        super().__init__(parent)

        self.marker_id_selection = QSpinBox()
        self.marker_id_selection.setRange(0, MarkerDictionary.marker_count(self.marker_dictionary) - 1)
        self.marker_id_selection.setValue(self.marker_id)
        self.marker_id_selection.setObjectName("Touch-marker_id_selection")
        self.marker_dictionary_selection = QComboBox()
        self.marker_dictionary_selection.addItems(MarkerDictionary.valid_values())
        self.marker_dictionary_selection.setCurrentText(self.marker_dictionary)
        self.marker_dictionary_selection.setObjectName("Touch-marker_dictionary_selection")
        self.z_offset = QSpinBox()
        self.z_offset.setRange(0, 400)
        self.z_offset.setValue(300)
        self.z_offset.setObjectName("Touch-z_offset")

        marker_list_layout = QFormLayout()
        marker_list_layout.addRow("Marker to touch:", self.marker_id_selection)
        marker_list_layout.addRow("Marker dictionary:", self.marker_dictionary_selection)
        marker_list_layout.addRow("Touch tool length (mm):", self.z_offset)

        self.setLayout(marker_list_layout)

        self.marker_id_selection.valueChanged.connect(self.on_marker_id_changed)
        self.marker_dictionary_selection.currentIndexChanged.connect(self.on_marker_dictionary_changed)

    def on_marker_id_changed(self):
        self.marker_id = self.marker_id_selection.value()

    def on_marker_dictionary_changed(self):
        self.marker_dictionary = self.marker_dictionary_selection.currentText()
        self.marker_id = self.marker_id_selection.value()
        if self.marker_id > MarkerDictionary.marker_count(self.marker_dictionary):
            self.marker_id = 0
            self.marker_id_selection.setValue(self.marker_id)
        self.marker_id_selection.setRange(0, MarkerDictionary.marker_count(self.marker_dictionary) - 1)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        return [self.marker_id_selection, self.marker_dictionary_selection, self.z_offset]


class MarkerListValidator(QValidator):

    def validate(self, text_to_validate, pos):
        # Allow partial matches while typing, including ranges
        partial_regex = QRegExp(r"^\s*\d*(\s*-\s*\d*)?(\s*,\s*\d*(\s*-\s*\d*)?)*$")
        complete_regex = QRegExp(r"^\s*\d+\s*(\s*-\s*\d+)?(\s*,\s*\d+\s*(\s*-\s*\d+)?)*$")

        if complete_regex.exactMatch(text_to_validate):
            return QValidator.Acceptable, text_to_validate, pos
        if partial_regex.exactMatch(text_to_validate):
            return QValidator.Intermediate, text_to_validate, pos
        return QValidator.Invalid, text_to_validate, pos

    def fixup(self, text_to_fix):
        # Allow digits, commas, and dashes, remove duplicates and sort
        fixed_input = "".join(c for c in text_to_fix if c.isdigit() or c in ",-")
        fixed_input = re.sub(r"([,-])(?:[,-])+", r"\1", fixed_input).strip(",").strip("-")
        ranges = fixed_input.split(",")
        ids = set()
        for r in ranges:
            if "-" in r:
                start, end = map(int, r.split("-"))
                ids.update(range(start, end + 1))
            else:
                ids.add(int(r))
        sorted_ids = sorted(ids)
        merged_ranges = []
        if sorted_ids:
            start = end = sorted_ids[0]
            for num in sorted_ids[1:]:
                if num == end + 1:
                    end = num
                else:
                    if start == end:
                        merged_ranges.append(f"{start}")
                    elif end - start + 1 < 6:
                        merged_ranges.extend(map(str, range(start, end + 1)))
                    else:
                        merged_ranges.append(f"{start}-{end}")
                    start = end = num
            if start == end:
                merged_ranges.append(f"{start}")
            elif end - start + 1 < 6:
                merged_ranges.extend(map(str, range(start, end + 1)))
            else:
                merged_ranges.append(f"{start}-{end}")
        fixed_input = ", ".join(merged_ranges)
        return fixed_input


@dataclass
class MarkerConfiguration:
    id_list: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    dictionary: str = MarkerDictionary.aruco4x4_50


class MarkersWidget(QWidget):
    marker_configuration: MarkerConfiguration
    marker_qimage: Optional[QImage] = None

    def __init__(
        self,
        initial_marker_configuration: MarkerConfiguration = MarkerConfiguration(),
        show_marker_image: bool = True,
        parent=None,
    ):
        super().__init__(parent)

        self.marker_configuration = initial_marker_configuration
        if show_marker_image:
            self.cv2_handler = CV2Handler()

        self.marker_list_line_edit = QLineEdit()
        self.marker_list_line_edit.setText(
            ", ".join([f"{marker_id}" for marker_id in self.marker_configuration.id_list])
        )
        self.marker_list_line_edit.setValidator(MarkerListValidator())
        self.marker_dictionary_selection = QComboBox()
        self.marker_dictionary_selection.addItems(MarkerDictionary.valid_values())
        self.marker_dictionary_selection.setCurrentText(self.marker_configuration.dictionary)
        self.marker_image = ImageViewer()

        self.marker_list_line_edit.editingFinished.connect(self.on_marker_list_edited)
        self.marker_dictionary_selection.currentIndexChanged.connect(self.on_marker_dictionary_changed)

        overall_layout = QVBoxLayout()
        self.marker_list_layout = QFormLayout()
        self.marker_list_layout.addRow("Marker identifiers:", self.marker_list_line_edit)
        self.marker_list_layout.addRow("Marker dictionary:", self.marker_dictionary_selection)
        overall_layout.addLayout(self.marker_list_layout)

        if show_marker_image:
            overall_layout.addWidget(self.marker_image)
        self.setLayout(overall_layout)

    def on_marker_list_edited(self):
        validator = self.marker_list_line_edit.validator()
        text = self.marker_list_line_edit.text()
        fixed_text = validator.fixup(text)
        self.marker_list_line_edit.setText(fixed_text)
        self.marker_configuration.id_list = self.expand_ranges(fixed_text)

    def on_marker_dictionary_changed(self):
        self.marker_configuration.dictionary = self.marker_dictionary_selection.currentText()

    def set_pixmap(self, pixmap: QPixmap, reset_zoom: bool = False) -> None:
        self.marker_image.set_pixmap(pixmap, reset_zoom)

    def set_image(self, qimage_rgba: QImage, reset_zoom: bool = False) -> None:
        self.marker_qimage = qimage_rgba
        self.marker_image.set_pixmap(QPixmap.fromImage(qimage_rgba), reset_zoom)

    def set_markers(
        self,
        markers: List[MarkerShape],
        rgba: NDArray[Shape["N, M, 4"], UInt8],  # type: ignore
        pixel_mapping: PixelMapping,
        reset_zoom: bool = False,
    ):
        rgb = rgba[:, :, :3].copy().astype(np.uint8)
        rgba[:, :, :3] = self.cv2_handler.draw_detected_markers(markers, rgb, pixel_mapping)
        qimage_rgba = QImage(
            rgba.data,
            rgba.shape[1],
            rgba.shape[0],
            QImage.Format_RGBA8888,
        )
        self.set_image(qimage_rgba, reset_zoom)

    def setVisible(self, visible: bool):
        super().setVisible(visible)
        self.marker_list_line_edit.setVisible(visible)
        self.marker_dictionary_selection.setVisible(visible)

    @staticmethod
    def expand_ranges(range_text: str) -> List[int]:
        """Expand ranges in the form of '1, 2-4, 6' into [1, 2, 3, 4, 6].

        Args:
            range_text: A string containing comma-separated ranges of integers.

        Returns:
            A list of integers.
        """
        parts = range_text.split(",")
        ids = set()
        for part in parts:
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                ids.update(range(start, end + 1))
            else:
                ids.add(int(part))
        return sorted(ids)


class MarkerConfigurationSelection(QDialog):

    def __init__(
        self,
        initial_marker_configuration: MarkerConfiguration = MarkerConfiguration(),
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Select Hand-Eye Configuration")

        self.marker_configuration = initial_marker_configuration
        self.marker_widget = MarkersWidget(
            initial_marker_configuration=initial_marker_configuration, show_marker_image=False
        )

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.marker_widget)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def accept(self):
        self.marker_configuration = self.marker_widget.marker_configuration
        super().accept()


def select_marker_configuration(
    initial_marker_configuration: MarkerConfiguration = MarkerConfiguration(),
) -> MarkerConfiguration:
    dialog = MarkerConfigurationSelection(initial_marker_configuration)
    dialog.exec_()
    return dialog.marker_configuration


if __name__ == "__main__":  # NOLINT
    with ZividQtApplication(use_zivid_app=False) as qtApp:
        widget = MarkersWidget()
        widget.show()
        qtApp.exec_()
