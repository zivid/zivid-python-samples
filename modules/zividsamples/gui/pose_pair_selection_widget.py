from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
import zivid
from nptyping import Float32, NDArray, Shape
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics, QImage
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from zivid.experimental import PixelMapping, calibration
from zividsamples.gui.cv2_handler import CV2Handler
from zividsamples.gui.hand_eye_configuration import CalibrationObject
from zividsamples.gui.marker_widget import MarkerConfiguration
from zividsamples.transformation_matrix import TransformationMatrix


def _label_width(label: QLabel, numbers: int) -> int:
    font_metrics = QFontMetrics(label.font())
    return (
        font_metrics.width(" -9999.9 ")
        if numbers == 1
        else font_metrics.width(" -9999.9 " + ", -9999.9" * (numbers - 1))
    )


class ButtonWithLabels(QPushButton):
    def __init__(self, labels: List[QLabel], parent=None):
        super().__init__(parent)

        self.labels = labels

        layout = QHBoxLayout(self)
        for index, label in enumerate(self.labels):
            num_numbers = 3 if index < 2 else 1
            text_alignment = Qt.AlignCenter if index < 2 else Qt.AlignRight | Qt.AlignVCenter
            label.setMinimumWidth(_label_width(label, num_numbers))
            label.setAlignment(text_alignment)
            layout.addWidget(label)
        combined_width = sum(label.sizeHint().width() for label in self.labels)
        self.setMinimumWidth(combined_width)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


@dataclass
class PosePair:
    robot_pose: TransformationMatrix
    camera_frame: zivid.Frame
    qimage_rgba: QImage
    detection_result: zivid.calibration.DetectionResult
    camera_pose: Optional[TransformationMatrix] = None


class PosePairWidget(QWidget):
    pose_pair: PosePair

    def __init__(self, poseID: int, directory: Path, pose_pair: PosePair, parent=None):
        super().__init__(parent)

        self.poseID = poseID
        self.directory = directory
        self.robot_pose_yaml_path: Path = self.directory / f"robot_pose_{self.poseID}.yaml"
        self.camera_pose_yaml_path: Path = self.directory / f"checkerboard_pose_in_camera_frame_{self.poseID}.yaml"
        self.camera_frame_path: Path = self.directory / f"calibration_object_pose_{self.poseID}.zdf"
        self.camera_image_path: Path = self.directory / f"calibration_object_pose_{self.poseID}.png"
        self.pose_pair = pose_pair

        self.selected_checkbox = QCheckBox(f"{self.poseID:>2}")
        self.selected_checkbox.setLayoutDirection(Qt.RightToLeft)
        self.selected_checkbox.setChecked(True)
        self.camera_pose_label = QLabel()
        self.robot_pose_label = QLabel()
        self.clickable_labels = ButtonWithLabels(
            [
                self.robot_pose_label,
                self.camera_pose_label,
                QLabel("NA"),
            ]
        )
        self.clickable_labels.setCheckable(True)
        self.clickable_labels.setChecked(False)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        pose_pair_layout = QHBoxLayout()
        pose_pair_layout.addWidget(self.selected_checkbox)
        pose_pair_layout.addWidget(self.clickable_labels)  # , stretch=1)
        self.setLayout(pose_pair_layout)

        self.update_information(pose_pair)

    def update_information(self, pose_pair: PosePair):
        self.pose_pair = pose_pair
        zivid.Matrix4x4(self.pose_pair.robot_pose.as_matrix()).save(self.robot_pose_yaml_path)
        self.pose_pair.camera_frame.save(self.camera_frame_path)
        if self.pose_pair.camera_pose is not None:
            zivid.Matrix4x4(self.pose_pair.camera_pose.as_matrix()).save(self.camera_pose_yaml_path)
        self.pose_pair.qimage_rgba.save(str(self.camera_image_path))
        self.camera_pose_label.setText(
            "NA"
            if self.pose_pair.camera_pose is None
            else self._translation_to_string(self.pose_pair.camera_pose.translation)
        )
        self.robot_pose_label.setText(self._translation_to_string(self.pose_pair.robot_pose.translation))

    def camera_pose_yaml_text(self) -> str:
        if self.pose_pair.camera_pose is None:
            return ""
        return self.camera_pose_yaml_path.read_text(encoding="utf-8")

    def robot_pose_yaml_text(self) -> str:
        return self.robot_pose_yaml_path.read_text(encoding="utf-8")

    def _translation_to_string(self, translation: NDArray[Shape["3"], Float32]) -> str:  # type: ignore
        return f"{translation[0]:>8.1f}, {translation[1]:>8.1f}, {translation[2]:.1f}"


def directory_has_pose_pair_data(directory: Path) -> bool:
    return (
        len(list(directory.glob("robot_pose_*.yaml"))) > 0
        and len(list(directory.glob("calibration_object_pose_*.zdf"))) > 0
    )


class PosePairSelectionWidget(QWidget):
    directory: Path
    pose_pair_clicked = pyqtSignal(PosePair)
    pose_pairs_updated = pyqtSignal(int)

    def __init__(self, directory: Path, parent=None):
        super().__init__(parent)

        self.cv2_handler = CV2Handler()

        self.pose_pair_widgets: OrderedDict[int, PosePairWidget] = OrderedDict()

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

        self.set_directory(directory)

    def create_widgets(self):
        self.pose_pair_container = QWidget()

        self.pose_pairs_group_box = QGroupBox("Pose Pairs")
        self.pose_pair_scrollable_area = QScrollArea()
        self.pose_pair_scrollable_area.setWidgetResizable(True)
        self.pose_pair_scrollable_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pose_pair_scrollable_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.pose_pair_scrollable_area.setWidget(self.pose_pair_container)

        self.clear_pose_pairs_button = QPushButton("Clear")

    def setup_layout(self):
        self.pose_pairs_group_box_layout = QVBoxLayout()
        self.pose_pairs_group_box_layout.setAlignment(Qt.AlignTop)
        self.pose_pairs_group_box.setLayout(self.pose_pairs_group_box_layout)

        self.pose_pairs_layout = QVBoxLayout(self.pose_pair_container)
        self.pose_pairs_layout.setAlignment(Qt.AlignTop)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.clear_pose_pairs_button)

        self.pose_pairs_group_box_layout.addLayout(self.create_title_row())
        self.pose_pairs_group_box_layout.addWidget(self.pose_pair_scrollable_area)
        self.pose_pairs_group_box_layout.addLayout(button_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.pose_pairs_group_box)
        self.setLayout(layout)

    def connect_signals(self):
        self.clear_pose_pairs_button.clicked.connect(self.on_clear_button_clicked)

    def set_directory(self, directory: Path):
        self.directory = directory

    def load_pose_pairs(self, calibration_object: CalibrationObject, marker_configuration: MarkerConfiguration):
        if len(self.pose_pair_widgets) > 0:
            message_box = QMessageBox()
            message_box.setText(
                """\
Overwrite collected data?

Note! This will not remove files from disk, but potentially reload them, and analyze with new Hand Eye configuration."
"""
            )
            message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            message_box.setDefaultButton(QMessageBox.No)
            if message_box.exec() == QMessageBox.No:
                return
        self.pose_pair_widgets.clear()
        self.pose_pairs_group_box.setStyleSheet(r"QGroupBox {border: 2px solid yellow;}")
        self.pose_pairs_group_box.setTitle("Pose Pairs (loading...)")
        self.pose_pairs_group_box.setVisible(True)
        QApplication.processEvents()
        for poseID in range(20):
            try:
                # Load from files
                try:
                    robot_pose_yaml_path: Path = self.directory / f"robot_pose_{poseID}.yaml"
                    camera_pose_yaml_path: Path = self.directory / f"checkerboard_pose_in_camera_frame_{poseID}.yaml"
                    camera_frame_path: Path = self.directory / f"calibration_object_pose_{poseID}.zdf"
                    camera_image_path: Path = self.directory / f"calibration_object_pose_{poseID}.png"
                    robot_pose = TransformationMatrix.from_matrix(np.asarray(zivid.Matrix4x4(robot_pose_yaml_path)))
                    camera_frame = zivid.Frame(camera_frame_path)
                    detection_result = (
                        zivid.calibration.detect_feature_points(camera_frame.point_cloud())
                        if calibration_object == CalibrationObject.Checkerboard
                        else zivid.calibration.detect_markers(
                            camera_frame, marker_configuration.id_list, marker_configuration.dictionary
                        )
                    )
                    if camera_pose_yaml_path.exists():
                        camera_pose = TransformationMatrix.from_matrix(
                            np.asarray(zivid.Matrix4x4(camera_pose_yaml_path))
                        )
                    elif calibration_object == CalibrationObject.Checkerboard and detection_result.valid():
                        camera_pose_zivid = detection_result.pose().to_matrix()
                        zivid.Matrix4x4(camera_pose_zivid).save(camera_pose_yaml_path.as_posix())
                        camera_pose = TransformationMatrix.from_matrix(np.asarray(camera_pose_zivid))
                    else:
                        camera_pose = None
                    if camera_image_path.exists() and detection_result.valid():
                        qimage_rgba = QImage(str(camera_image_path))
                    else:
                        rgba = camera_frame.point_cloud().copy_data("rgba_srgb")
                        rgb = rgba[:, :, :3].copy().astype(np.uint8)
                        if calibration_object == CalibrationObject.Markers and detection_result.valid():
                            rgba[:, :, :3] = self.cv2_handler.draw_detected_markers(
                                detection_result.detected_markers(), rgb, PixelMapping()
                            )
                        elif camera_pose is not None:
                            intrinsics = calibration.estimate_intrinsics(camera_frame)
                            rgba[:, :, :3] = self.cv2_handler.draw_projected_axis_cross(intrinsics, rgb, camera_pose)
                        qimage_rgba = QImage(
                            rgba.data,
                            rgba.shape[1],
                            rgba.shape[0],
                            QImage.Format_RGBA8888,
                        )
                    pose_pair_widget = self.add_pose_pair(
                        pose_pair=PosePair(
                            robot_pose=robot_pose,
                            camera_frame=camera_frame,
                            qimage_rgba=qimage_rgba,
                            camera_pose=camera_pose,
                            detection_result=detection_result,
                        )
                    )
                    if pose_pair_widget is not None:
                        self.pose_pair_clicked.emit(pose_pair_widget.pose_pair)

                except (FileNotFoundError, RuntimeError) as ex:
                    raise FileNotFoundError(f"Failed to load pose pair from {self.directory}: {ex}") from ex
            except FileNotFoundError:
                continue
            QApplication.processEvents()
        self.pose_pairs_group_box.setStyleSheet("")
        self.pose_pairs_group_box.setTitle("Pose Pairs")

    def on_pose_pair_widget_clicked(self, pose_pair_widget: PosePairWidget):
        for clickable_area in [p.clickable_labels for p in self.pose_pair_widgets.values()]:
            if clickable_area is not pose_pair_widget.clickable_labels:
                clickable_area.setChecked(False)
                QApplication.processEvents()
        self.pose_pair_clicked.emit(pose_pair_widget.pose_pair)

    def on_clear_button_clicked(self):
        self.clear()

    def create_title_row(self) -> QHBoxLayout:
        checkbox_and_poseID_spacer = QSpacerItem(75, 40, QSizePolicy.Fixed, QSizePolicy.Minimum)
        title_labels = ButtonWithLabels([QLabel("Robot"), QLabel("Camera"), QLabel("Residual")])
        title_layout = QHBoxLayout()
        title_layout.addItem(checkbox_and_poseID_spacer)
        title_layout.addWidget(title_labels)
        return title_layout

    def add_pose_pair(self, pose_pair) -> Optional[PosePairWidget]:
        poseID = self.get_current_poseID()
        if poseID in self.pose_pair_widgets:
            reply = QMessageBox.question(
                self,
                "Replace Pose Pair",
                "This will replace the selected Pose Pair. Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.pose_pair_widgets[poseID].update_information(pose_pair)
                return self.pose_pair_widgets[poseID]
            return None

        pose_pair_widget = PosePairWidget(poseID=poseID, directory=self.directory, pose_pair=pose_pair)
        pose_pair_widget.clickable_labels.clicked.connect(lambda: self.on_pose_pair_widget_clicked(pose_pair_widget))

        self.pose_pairs_layout.insertWidget(pose_pair_widget.poseID, pose_pair_widget)
        self.pose_pair_widgets[poseID] = pose_pair_widget
        self.pose_pairs_updated.emit(len(self.pose_pair_widgets))
        return pose_pair_widget

    def get_current_poseID(self) -> int:
        for pose_pair_widget in self.pose_pair_widgets.values():
            if pose_pair_widget.clickable_labels.isChecked():
                return pose_pair_widget.poseID
        return len(self.pose_pair_widgets)

    def number_of_active_pose_pairs(self) -> int:
        return len(
            [
                pose_pair_widget
                for pose_pair_widget in self.pose_pair_widgets.values()
                if pose_pair_widget.selected_checkbox.isChecked()
            ]
        )

    def get_detection_results(self) -> List[zivid.calibration.HandEyeInput]:
        return [
            zivid.calibration.HandEyeInput(
                zivid.calibration.Pose(pose_pair_widget.pose_pair.robot_pose.as_matrix()),
                pose_pair_widget.pose_pair.detection_result,
            )
            for pose_pair_widget in self.pose_pair_widgets.values()
            if pose_pair_widget.selected_checkbox.isChecked()
        ]

    def set_residuals(self, residuals: List[Any]):
        checked_pose_pairs = [
            pose_pair_widget
            for pose_pair_widget in self.pose_pair_widgets.values()
            if pose_pair_widget.selected_checkbox.isChecked()
        ]
        for pose_pair_widget, residual in zip(checked_pose_pairs, residuals):  # noqa: B905
            pose_pair_widget.clickable_labels.labels[2].setText(
                f"{residual.translation():.2f} ({residual.rotation():.2f}°)"
            )
        unchecked_pose_pairs = [
            pose_pair_widget
            for pose_pair_widget in self.pose_pair_widgets.values()
            if not pose_pair_widget.selected_checkbox.isChecked()
        ]
        for pose_pair_widget in unchecked_pose_pairs:
            pose_pair_widget.clickable_labels.labels[2].setText("NA")

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            sublayout = item.layout()
            if sublayout:
                self._clear_layout(sublayout)

    def clear(self):
        self._clear_layout(self.pose_pairs_layout)
        self.pose_pair_widgets.clear()
        self.pose_pairs_updated.emit(0)
