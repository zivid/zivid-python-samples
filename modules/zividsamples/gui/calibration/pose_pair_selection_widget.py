import threading
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import zivid
from nptyping import Float32, NDArray, Shape
from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal
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
from zividsamples.gui.widgets.cv2_handler import CV2Handler
from zividsamples.gui.wizard.data_directory import SessionInfo
from zividsamples.gui.wizard.hand_eye_configuration import CalibrationObject
from zividsamples.gui.wizard.marker_configuration import MarkerConfiguration
from zividsamples.transformation_matrix import TransformationMatrix

_HE_CONFIG_KEY = "hand_eye_configuration"


def save_calibration_config(
    session_info: SessionInfo,
    calibration_object: CalibrationObject,
    eye_in_hand: bool,
    marker_configuration: Optional[MarkerConfiguration] = None,
) -> None:
    he_config: Dict[str, Any] = {
        "calibration_object": calibration_object.name,
        "eye_in_hand": eye_in_hand,
    }
    if marker_configuration is not None and calibration_object == CalibrationObject.Markers:
        he_config["marker_dictionary"] = marker_configuration.dictionary
        he_config["marker_ids"] = marker_configuration.id_list
    session_info.set_section(_HE_CONFIG_KEY, he_config)
    session_info.save()


@dataclass
class SessionCalibrationConfig:
    calibration_object: CalibrationObject
    eye_in_hand: bool
    marker_dictionary: Optional[str] = None
    marker_ids: Optional[List[int]] = None


def load_calibration_config(session_info: SessionInfo) -> Optional[SessionCalibrationConfig]:
    he_config = session_info.get_section(_HE_CONFIG_KEY)
    if he_config is None or "calibration_object" not in he_config:
        return None
    return SessionCalibrationConfig(
        calibration_object=CalibrationObject[he_config["calibration_object"]],
        eye_in_hand=he_config.get("eye_in_hand", True),
        marker_dictionary=he_config.get("marker_dictionary"),
        marker_ids=he_config.get("marker_ids"),
    )


def _label_width_vector(label: QLabel, size: int) -> int:
    font_metrics = QFontMetrics(label.font())
    return font_metrics.width(" -9999.9 " + ", -9999.9" * (size - 1))


def _residual_label_width(label: QLabel) -> int:
    font_metrics = QFontMetrics(label.font())
    return font_metrics.width(" -999.9 ( -359.9° )")


class ButtonWithLabels(QPushButton):
    def __init__(self, labels: List[QLabel], parent=None):
        super().__init__(parent)

        self.labels = labels

        layout = QHBoxLayout(self)
        for index, label in enumerate(self.labels):
            text_alignment = Qt.AlignCenter if index < 2 else Qt.AlignRight | Qt.AlignVCenter
            if index == 2:
                label.setMinimumWidth(_residual_label_width(label))
            else:
                label.setMinimumWidth(_label_width_vector(label=label, size=3))
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

    # pylint: disable=too-many-positional-arguments
    def __init__(self, poseID: int, directory: Path, pose_pair: PosePair, save_to_disk: bool = True, parent=None):
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

        self.update_information(pose_pair, save_to_disk=save_to_disk)

    def update_information(self, pose_pair: PosePair, save_to_disk: bool = True):
        self.pose_pair = pose_pair
        if save_to_disk:
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


class _PosePairLoadWorker(QObject):
    """Loads pose pair data from disk in a background thread."""

    pose_pair_loaded = pyqtSignal(int, int, object)
    finished = pyqtSignal(int)

    # pylint: disable=too-many-positional-arguments
    def __init__(self, generation, directory, pose_ids, calibration_object, marker_configuration):
        super().__init__()
        self._generation = generation
        self._directory = directory
        self._pose_ids = pose_ids
        self._calibration_object = calibration_object
        self._marker_configuration = marker_configuration
        self._cancel_event = threading.Event()
        self._cv2_handler = CV2Handler()

    def cancel(self):
        self._cancel_event.set()

    def run(self):
        for poseID in self._pose_ids:
            if self._cancel_event.is_set():
                break
            try:
                robot_pose_yaml_path = self._directory / f"robot_pose_{poseID}.yaml"
                camera_pose_yaml_path = self._directory / f"checkerboard_pose_in_camera_frame_{poseID}.yaml"
                camera_frame_path = self._directory / f"calibration_object_pose_{poseID}.zdf"
                camera_image_path = self._directory / f"calibration_object_pose_{poseID}.png"

                robot_pose = TransformationMatrix.from_matrix(np.asarray(zivid.Matrix4x4(robot_pose_yaml_path)))
                camera_frame = zivid.Frame(camera_frame_path)

                if self._cancel_event.is_set():
                    break

                detection_result = (
                    zivid.calibration.detect_feature_points(camera_frame.point_cloud())
                    if self._calibration_object == CalibrationObject.Checkerboard
                    else zivid.calibration.detect_markers(
                        camera_frame, self._marker_configuration.id_list, self._marker_configuration.dictionary
                    )
                )

                camera_pose = None
                if camera_pose_yaml_path.exists():
                    camera_pose = TransformationMatrix.from_matrix(np.asarray(zivid.Matrix4x4(camera_pose_yaml_path)))
                elif self._calibration_object == CalibrationObject.Checkerboard and detection_result.valid():
                    camera_pose_zivid = detection_result.pose().to_matrix()
                    zivid.Matrix4x4(camera_pose_zivid).save(camera_pose_yaml_path.as_posix())
                    camera_pose = TransformationMatrix.from_matrix(np.asarray(camera_pose_zivid))

                if camera_image_path.exists() and detection_result.valid():
                    qimage_rgba = QImage(str(camera_image_path))
                else:
                    rgba = camera_frame.point_cloud().copy_data("rgba_srgb")
                    rgb = rgba[:, :, :3].copy().astype(np.uint8)
                    if self._calibration_object == CalibrationObject.Markers and detection_result.valid():
                        rgba[:, :, :3] = self._cv2_handler.draw_detected_markers(
                            detection_result.detected_markers(), rgb, PixelMapping()
                        )
                    elif camera_pose is not None:
                        intrinsics = calibration.estimate_intrinsics(camera_frame)
                        rgba[:, :, :3] = self._cv2_handler.draw_projected_axis_cross(intrinsics, rgb, camera_pose)
                    qimage_rgba = QImage(rgba.data, rgba.shape[1], rgba.shape[0], QImage.Format_RGBA8888).copy()

                pose_pair = PosePair(
                    robot_pose=robot_pose,
                    camera_frame=camera_frame,
                    qimage_rgba=qimage_rgba,
                    camera_pose=camera_pose,
                    detection_result=detection_result,
                )
                self.pose_pair_loaded.emit(self._generation, poseID, pose_pair)
            except FileNotFoundError:
                continue
        self.finished.emit(self._generation)


class _PosePairReprocessWorker(QObject):
    """Recomputes detection results from in-memory frames in a background thread."""

    pose_pair_reprocessed = pyqtSignal(int, int, object)
    finished = pyqtSignal(int)

    def __init__(self, generation, frames, calibration_object, marker_configuration):
        super().__init__()
        self._generation = generation
        self._frames = frames
        self._calibration_object = calibration_object
        self._marker_configuration = marker_configuration
        self._cancel_event = threading.Event()
        self._cv2_handler = CV2Handler()

    def cancel(self):
        self._cancel_event.set()

    def run(self):
        for poseID, camera_frame in self._frames:
            if self._cancel_event.is_set():
                break

            detection_result = (
                zivid.calibration.detect_feature_points(camera_frame.point_cloud())
                if self._calibration_object == CalibrationObject.Checkerboard
                else zivid.calibration.detect_markers(
                    camera_frame, self._marker_configuration.id_list, self._marker_configuration.dictionary
                )
            )

            camera_pose = None
            if self._calibration_object == CalibrationObject.Checkerboard and detection_result.valid():
                camera_pose = TransformationMatrix.from_matrix(np.asarray(detection_result.pose().to_matrix()))

            rgba = camera_frame.point_cloud().copy_data("rgba_srgb")
            rgb = rgba[:, :, :3].copy().astype(np.uint8)
            if self._calibration_object == CalibrationObject.Markers and detection_result.valid():
                rgba[:, :, :3] = self._cv2_handler.draw_detected_markers(
                    detection_result.detected_markers(), rgb, PixelMapping()
                )
            elif camera_pose is not None:
                intrinsics = calibration.estimate_intrinsics(camera_frame)
                rgba[:, :, :3] = self._cv2_handler.draw_projected_axis_cross(intrinsics, rgb, camera_pose)
            qimage_rgba = QImage(rgba.data, rgba.shape[1], rgba.shape[0], QImage.Format_RGBA8888).copy()

            self.pose_pair_reprocessed.emit(self._generation, poseID, (detection_result, camera_pose, qimage_rgba))
        self.finished.emit(self._generation)


class PosePairSelectionWidget(QWidget):
    directory: Path
    pose_pair_clicked = pyqtSignal(PosePair)
    pose_pairs_updated = pyqtSignal(int)
    loading_finished = pyqtSignal()

    def __init__(self, directory: Path, parent=None):
        super().__init__(parent)

        self.cv2_handler = CV2Handler()
        self._load_generation = 0
        self._loader_thread: Optional[QThread] = None
        self._loader_worker: Optional[_PosePairLoadWorker] = None
        self._reprocess_thread: Optional[QThread] = None
        self._reprocess_worker: Optional[_PosePairReprocessWorker] = None
        self._last_operation_was_reprocess = False
        self._loaded_from_disk = False

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

        self.cancel_loading()
        self._last_operation_was_reprocess = False
        self._set_loaded_from_disk(False)
        self._clear_layout(self.pose_pairs_layout)
        self.pose_pair_widgets.clear()
        self.pose_pairs_updated.emit(0)

        pose_ids = [
            pid
            for pid in range(20)
            if (self.directory / f"robot_pose_{pid}.yaml").exists()
            and (self.directory / f"calibration_object_pose_{pid}.zdf").exists()
        ]
        if not pose_ids:
            return

        self._set_loaded_from_disk(True)

        self._load_generation += 1
        generation = self._load_generation

        self.pose_pairs_group_box.setStyleSheet(r"QGroupBox {border: 2px solid yellow;}")
        self.pose_pairs_group_box.setTitle("Pose Pairs (loading...)")
        self.pose_pairs_group_box.setVisible(True)

        thread = QThread()
        worker = _PosePairLoadWorker(
            generation=generation,
            directory=self.directory,
            pose_ids=pose_ids,
            calibration_object=calibration_object,
            marker_configuration=marker_configuration,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.pose_pair_loaded.connect(self._on_pose_pair_loaded)
        worker.finished.connect(self._on_loading_finished)
        worker.finished.connect(thread.quit)
        self._loader_thread = thread
        self._loader_worker = worker
        thread.start()

    def cancel_loading(self):
        if self._loader_worker is not None:
            self._loader_worker.cancel()
        if self._loader_thread is not None and self._loader_thread.isRunning():
            self._loader_thread.quit()
            self._loader_thread.wait(10000)
        self._loader_worker = None
        self._loader_thread = None
        self._cancel_reprocessing()

    def _cancel_reprocessing(self):
        if self._reprocess_worker is not None:
            self._reprocess_worker.cancel()
        if self._reprocess_thread is not None and self._reprocess_thread.isRunning():
            self._reprocess_thread.quit()
            self._reprocess_thread.wait(10000)
        self._reprocess_worker = None
        self._reprocess_thread = None

    def _on_pose_pair_loaded(self, generation: int, poseID: int, pose_pair: PosePair):
        if generation != self._load_generation:
            return
        if poseID in self.pose_pair_widgets:
            return
        pose_pair_widget = PosePairWidget(
            poseID=poseID, directory=self.directory, pose_pair=pose_pair, save_to_disk=False
        )
        pose_pair_widget.clickable_labels.clicked.connect(lambda: self.on_pose_pair_widget_clicked(pose_pair_widget))
        self.pose_pairs_layout.insertWidget(pose_pair_widget.poseID, pose_pair_widget)
        self.pose_pair_widgets[poseID] = pose_pair_widget
        self.pose_pairs_updated.emit(len(self.pose_pair_widgets))
        self.pose_pair_clicked.emit(pose_pair_widget.pose_pair)

    def _on_loading_finished(self, generation: int):
        if generation != self._load_generation:
            return
        self.pose_pairs_group_box.setStyleSheet("")
        self.pose_pairs_group_box.setTitle("Pose Pairs")
        self.loading_finished.emit()

    def reprocess_pose_pairs(
        self, calibration_object: CalibrationObject, marker_configuration: MarkerConfiguration
    ) -> None:
        if not self.pose_pair_widgets:
            return
        self._cancel_reprocessing()
        self._last_operation_was_reprocess = True

        frames = [(poseID, widget.pose_pair.camera_frame) for poseID, widget in self.pose_pair_widgets.items()]

        self._load_generation += 1
        generation = self._load_generation

        self.pose_pairs_group_box.setStyleSheet(r"QGroupBox {border: 2px solid yellow;}")
        self.pose_pairs_group_box.setTitle("Pose Pairs (reprocessing...)")

        thread = QThread()
        worker = _PosePairReprocessWorker(
            generation=generation,
            frames=frames,
            calibration_object=calibration_object,
            marker_configuration=marker_configuration,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.pose_pair_reprocessed.connect(self._on_pose_pair_reprocessed)
        worker.finished.connect(self._on_reprocessing_finished)
        worker.finished.connect(thread.quit)
        self._reprocess_thread = thread
        self._reprocess_worker = worker
        thread.start()

    def _on_pose_pair_reprocessed(self, generation: int, poseID: int, result: object) -> None:
        if generation != self._load_generation:
            return
        if poseID not in self.pose_pair_widgets:
            return
        assert isinstance(result, tuple)
        detection_result, camera_pose, qimage_rgba = result
        widget = self.pose_pair_widgets[poseID]
        widget.pose_pair.detection_result = detection_result
        widget.pose_pair.camera_pose = camera_pose
        widget.pose_pair.qimage_rgba = qimage_rgba
        widget.update_information(widget.pose_pair, save_to_disk=False)
        widget.clickable_labels.labels[2].setText("NA")

    def _on_reprocessing_finished(self, generation: int) -> None:
        if generation != self._load_generation:
            return
        self.pose_pairs_group_box.setStyleSheet("")
        self.pose_pairs_group_box.setTitle("Pose Pairs")
        self.loading_finished.emit()

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

    def is_loading(self) -> bool:
        if self._loader_thread is not None and self._loader_thread.isRunning():
            return True
        if self._reprocess_thread is not None and self._reprocess_thread.isRunning():
            return True
        return False

    @property
    def last_operation_was_reprocess(self) -> bool:
        return self._last_operation_was_reprocess

    @property
    def loaded_from_disk(self) -> bool:
        return self._loaded_from_disk

    def _set_loaded_from_disk(self, value: bool) -> None:
        self._loaded_from_disk = value
        self.clear_pose_pairs_button.setVisible(not value)

    def add_pose_pair(self, pose_pair) -> Optional[PosePairWidget]:
        if self.is_loading():
            return None
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
        self.cancel_loading()
        self._set_loaded_from_disk(False)
        self._clear_layout(self.pose_pairs_layout)
        self.pose_pair_widgets.clear()
        self.pose_pairs_updated.emit(0)
