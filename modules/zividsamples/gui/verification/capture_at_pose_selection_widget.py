import threading
from collections import OrderedDict
from pathlib import Path
from typing import Optional

import numpy as np
import zivid
from nptyping import Float32, NDArray, Shape
from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)
from zividsamples.transformation_matrix import TransformationMatrix

UNIQUE_COLORS = [
    [255, 128, 192],  # Light Pink
    [128, 255, 192],  # Mint
    [192, 128, 255],  # Lavender
    [255, 255, 128],  # Light Lemon
    [128, 192, 255],  # Sky Blue
    [255, 192, 128],  # Peach
    [192, 255, 128],  # Pale Green
    [64, 255, 64],  # Light Green
    [64, 128, 255],  # Light Blue
    [255, 255, 64],  # Light Yellow
    [255, 64, 255],  # Light Magenta
    [64, 255, 255],  # Light Cyan
    [255, 64, 64],  # Light Red
    [255, 128, 0],  # Orange
    [128, 255, 0],  # Lime Green
    [255, 0, 128],  # Pink
    [128, 0, 255],  # Purple
    [0, 255, 128],  # Spring Green
    [255, 192, 64],  # Gold
    [192, 128, 64],  # Brown
]


class CaptureAtPose:

    def _translation_to_string(self, translation: NDArray[Shape["3"], Float32]) -> str:  # type: ignore
        return f"{translation[0]:.1f}, {translation[1]:.1f}, {translation[2]:.1f}"

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        poseID: int,
        directory: Path,
        robot_pose: TransformationMatrix,
        camera_frame: zivid.Frame,
        hand_eye_transform: TransformationMatrix,
        eye_in_hand: bool,
        optimize_for_speed: bool = True,
        from_disk: bool = False,
    ):

        self.poseID = poseID
        self.color = UNIQUE_COLORS[poseID % len(UNIQUE_COLORS)]
        self.directory = directory
        self.robot_pose_yaml_path: Path = self.directory / f"robot_pose_{self.poseID}.yaml"
        self.camera_frame_path: Path = self.directory / f"capture_{self.poseID}.zdf"
        self.robot_pose = robot_pose
        self.camera_frame = camera_frame

        if not from_disk:
            zivid.Matrix4x4(self.robot_pose.as_matrix()).save(self.robot_pose_yaml_path)
            self.camera_frame.save(self.camera_frame_path)

            if optimize_for_speed:
                self.camera_frame.point_cloud().downsample(zivid.PointCloud.Downsampling.by2x2)

            if eye_in_hand:
                transform_robot_base_to_camera = self.robot_pose * hand_eye_transform
                self.camera_frame.point_cloud().transform(zivid.Matrix4x4(transform_robot_base_to_camera.as_matrix()))
            else:
                transform_flange_to_camera = self.robot_pose.inv() * hand_eye_transform
                self.camera_frame.point_cloud().transform(zivid.Matrix4x4(transform_flange_to_camera.as_matrix()))

        self.selected_checkbox = QCheckBox("")
        self.selected_checkbox.setChecked(True)
        self.selected_checkbox.setStyleSheet(
            f"""
            QCheckBox::indicator:checked {{
            background-color: rgb({self.color[0]}, {self.color[1]}, {self.color[2]});
            }}
            QCheckBox::indicator:checked::hover {{
            background-color: rgb({min(self.color[0] + 30,255)}, {min(self.color[1] + 30,255)}, {min(self.color[2] + 30,255)});
            border: 2px solid rgb({self.color[0]}, {self.color[1]}, {self.color[2]});
            }}
        """
        )
        self.capture_pose_button = QPushButton(self._translation_to_string(self.robot_pose.translation))
        self.capture_pose_button.setCheckable(True)
        self.capture_pose_button.setChecked(False)
        self.capture_pose_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.remove_capture_at_pose_button = QPushButton()
        self.remove_capture_at_pose_button.setIcon(
            QApplication.instance().style().standardIcon(QStyle.SP_DialogDiscardButton)
        )

    def save_as_ply(self):
        self.camera_frame.save(self.directory / f"capture_{self.poseID}.ply")

    def robot_pose_yaml_text(self) -> str:
        return self.robot_pose_yaml_path.read_text(encoding="utf-8")


class _CaptureAtPoseLoadWorker(QObject):
    """Loads capture-at-pose data from disk in a background thread."""

    item_loaded = pyqtSignal(int, int, object, object)
    finished = pyqtSignal(int)

    # pylint: disable=too-many-positional-arguments
    def __init__(self, generation, directory, pose_ids, hand_eye_transform, eye_in_hand):
        super().__init__()
        self._generation = generation
        self._directory = directory
        self._pose_ids = pose_ids
        self._hand_eye_transform = hand_eye_transform
        self._eye_in_hand = eye_in_hand
        self._cancel_event = threading.Event()

    def cancel(self):
        self._cancel_event.set()

    def run(self):
        for poseID in self._pose_ids:
            if self._cancel_event.is_set():
                break
            try:
                robot_pose_yaml_path = self._directory / f"robot_pose_{poseID}.yaml"
                camera_frame_path = self._directory / f"capture_{poseID}.zdf"
                robot_pose = TransformationMatrix.from_matrix(np.asarray(zivid.Matrix4x4(robot_pose_yaml_path)))
                camera_frame = zivid.Frame(camera_frame_path)

                if self._cancel_event.is_set():
                    break

                camera_frame.point_cloud().downsample(zivid.PointCloud.Downsampling.by2x2)

                if self._eye_in_hand:
                    transform = robot_pose * self._hand_eye_transform
                else:
                    transform = robot_pose.inv() * self._hand_eye_transform
                camera_frame.point_cloud().transform(zivid.Matrix4x4(transform.as_matrix()))

                self.item_loaded.emit(self._generation, poseID, robot_pose, camera_frame)
            except FileNotFoundError:
                continue
        self.finished.emit(self._generation)


class CaptureAtPoseSelectionWidget(QWidget):
    directory: Path
    capture_at_pose_clicked = pyqtSignal(CaptureAtPose)
    capture_at_pose_remove_clicked = pyqtSignal(CaptureAtPose)
    selected_captures_updated = pyqtSignal()
    loading_finished = pyqtSignal()

    def __init__(self, directory: Path, parent=None):
        super().__init__(parent)

        self.directory = directory
        self._load_generation = 0
        self._loader_thread: Optional[QThread] = None
        self._loader_worker: Optional[_CaptureAtPoseLoadWorker] = None

        self.capture_at_poses: OrderedDict[int, CaptureAtPose] = OrderedDict()
        self.captures_group_box_layout = QVBoxLayout()
        self.captures_group_box_layout.setAlignment(Qt.AlignTop)
        self.captures_group_box = QGroupBox("Captures")
        self.captures_group_box.setMinimumWidth(500)
        self.captures_group_box.setLayout(self.captures_group_box_layout)
        self.captures_layout = QVBoxLayout()
        self.captures_layout.setAlignment(Qt.AlignTop)
        self.clear_button = QPushButton("Clear")
        self.clear_button.setEnabled(False)

        self.captures_group_box_layout.addLayout(self.captures_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.clear_button)
        self.captures_group_box_layout.addLayout(buttons_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.captures_group_box)
        self.setLayout(layout)

        self.clear_button.clicked.connect(self.on_clear_button_clicked)

    def set_directory(self, directory: Path):
        self.directory = directory

    def load_capture_at_poses(self, hand_eye_transform: TransformationMatrix, eye_in_hand: bool):
        if self.number_of_active_captures() > 0:
            reply = QMessageBox.question(
                self,
                "Clear Captures",
                "This will clear all current captures. Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.clear()
            else:
                return

        self.cancel_loading()

        pose_ids = [
            pid
            for pid in range(20)
            if (self.directory / f"robot_pose_{pid}.yaml").exists() and (self.directory / f"capture_{pid}.zdf").exists()
        ]
        if not pose_ids:
            return

        self._load_generation += 1
        generation = self._load_generation

        self.captures_group_box.setTitle(f"Loading from {self.directory}...")

        self._loader_thread = QThread()
        self._loader_worker = _CaptureAtPoseLoadWorker(
            generation=generation,
            directory=self.directory,
            pose_ids=pose_ids,
            hand_eye_transform=hand_eye_transform,
            eye_in_hand=eye_in_hand,
        )
        self._loader_worker.moveToThread(self._loader_thread)
        assert self._loader_thread is not None
        self._loader_thread.started.connect(self._loader_worker.run)
        self._loader_worker.item_loaded.connect(self._on_capture_loaded)
        self._loader_worker.finished.connect(self._on_loading_finished)
        self._loader_worker.finished.connect(self._loader_thread.quit)
        self._loader_thread.start()

    def cancel_loading(self):
        if self._loader_worker is not None:
            self._loader_worker.cancel()
        if self._loader_thread is not None and self._loader_thread.isRunning():
            self._loader_thread.quit()
            self._loader_thread.wait(10000)
        self._loader_worker = None
        self._loader_thread = None

    def _on_capture_loaded(
        self, generation: int, poseID: int, robot_pose: TransformationMatrix, camera_frame: zivid.Frame
    ):
        if generation != self._load_generation:
            return
        if poseID in self.capture_at_poses:
            return

        dummy_transform = TransformationMatrix()
        capture_at_pose = CaptureAtPose(
            poseID=poseID,
            directory=self.directory,
            robot_pose=robot_pose,
            camera_frame=camera_frame,
            hand_eye_transform=dummy_transform,
            eye_in_hand=True,
            from_disk=True,
        )
        capture_at_pose_layout = QHBoxLayout()
        capture_at_pose.capture_pose_button.clicked.connect(lambda: self.on_capture_at_pose_clicked(capture_at_pose))
        capture_at_pose.remove_capture_at_pose_button.clicked.connect(
            lambda: self.remove_capture_at_pose(capture_at_pose)
        )
        capture_at_pose.selected_checkbox.clicked.connect(self.selected_captures_updated.emit)

        capture_at_pose_layout.addWidget(QLabel(f"{capture_at_pose.poseID}"))
        capture_at_pose_layout.addWidget(capture_at_pose.selected_checkbox)
        capture_at_pose_layout.addWidget(capture_at_pose.capture_pose_button)
        capture_at_pose_layout.addWidget(capture_at_pose.remove_capture_at_pose_button)
        self.captures_layout.insertLayout(capture_at_pose.poseID, capture_at_pose_layout)
        self.capture_at_poses[poseID] = capture_at_pose
        self.clear_button.setEnabled(True)

    def _on_loading_finished(self, generation: int):
        if generation != self._load_generation:
            return
        self.captures_group_box.setTitle("Captures")
        self.loading_finished.emit()

    def get_selected_capture_at_poses(self):
        return [pose_pair for pose_pair in self.capture_at_poses.values() if pose_pair.selected_checkbox.isChecked()]

    def on_capture_at_pose_clicked(self, capture_at_pose: CaptureAtPose):
        for capture_pose_button in [p.capture_pose_button for p in self.capture_at_poses.values()]:
            if capture_pose_button is not capture_at_pose.capture_pose_button:
                capture_pose_button.setChecked(False)
                QApplication.processEvents()
        self.capture_at_pose_clicked.emit(capture_at_pose)

    def on_clear_button_clicked(self):
        self.clear()
        self.clear_button.setEnabled(False)

    def remove_capture_at_pose(self, capture_at_pose: CaptureAtPose):
        del self.capture_at_poses[capture_at_pose.poseID]
        self._clear_layout(self.captures_layout.itemAt(capture_at_pose.poseID))

    def is_loading(self) -> bool:
        return self._loader_thread is not None and self._loader_thread.isRunning()

    def add_capture_at_pose(
        self,
        robot_pose: TransformationMatrix,
        camera_frame: zivid.Frame,
        hand_eye_transform: TransformationMatrix,
        eye_in_hand: bool,
    ):
        if self.is_loading():
            return
        poseID = self.get_current_poseID()
        if poseID in self.capture_at_poses:
            reply = QMessageBox.question(
                self,
                "Replace Capture",
                "This will replace the selected capture. Do you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.remove_capture_at_pose(self.capture_at_poses[poseID])
            else:
                poseID = self._get_first_available_poseID()

        capture_at_pose = CaptureAtPose(
            poseID=poseID,
            directory=self.directory,
            robot_pose=robot_pose,
            camera_frame=camera_frame,
            hand_eye_transform=hand_eye_transform,
            eye_in_hand=eye_in_hand,
        )
        capture_at_pose_layout = QHBoxLayout()
        capture_at_pose.capture_pose_button.clicked.connect(lambda: self.on_capture_at_pose_clicked(capture_at_pose))
        capture_at_pose.remove_capture_at_pose_button.clicked.connect(
            lambda: self.remove_capture_at_pose(capture_at_pose)
        )
        capture_at_pose.selected_checkbox.clicked.connect(self.selected_captures_updated.emit)

        capture_at_pose_layout.addWidget(QLabel(f"{capture_at_pose.poseID}"))
        capture_at_pose_layout.addWidget(capture_at_pose.selected_checkbox)
        capture_at_pose_layout.addWidget(capture_at_pose.capture_pose_button)
        capture_at_pose_layout.addWidget(capture_at_pose.remove_capture_at_pose_button)
        self.captures_layout.insertLayout(capture_at_pose.poseID, capture_at_pose_layout)
        self.capture_at_poses[poseID] = capture_at_pose
        self.clear_button.setEnabled(True)

    def _get_first_available_poseID(self) -> int:
        for poseID in range(50):
            if poseID not in self.capture_at_poses:
                return poseID
        return 0

    def get_current_poseID(self) -> int:
        for pose_pair in self.capture_at_poses.values():
            if pose_pair.capture_pose_button.isChecked():
                return pose_pair.poseID
        return self._get_first_available_poseID()

    def number_of_active_captures(self) -> int:
        return len(
            [pose_pair for pose_pair in self.capture_at_poses.values() if pose_pair.selected_checkbox.isChecked()]
        )

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
        self._clear_layout(self.captures_layout)
        self.capture_at_poses.clear()
        self.selected_captures_updated.emit()
