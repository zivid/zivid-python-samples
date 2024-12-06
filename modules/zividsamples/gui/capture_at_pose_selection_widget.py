from collections import OrderedDict
from pathlib import Path

import numpy as np
import zivid
from nptyping import Float32, NDArray, Shape
from PyQt5.QtCore import Qt, pyqtSignal
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
    ):

        self.poseID = poseID
        self.directory = directory
        self.robot_pose_yaml_path: Path = self.directory / f"robot_pose_{self.poseID}.yaml"
        self.camera_frame_path: Path = self.directory / f"capture_{self.poseID}.zdf"
        self.robot_pose = robot_pose
        zivid.Matrix4x4(self.robot_pose.as_matrix()).save(self.robot_pose_yaml_path)
        self.camera_frame = camera_frame
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


class CaptureAtPoseSelectionWidget(QWidget):
    directory: Path
    capture_at_pose_clicked = pyqtSignal(CaptureAtPose)
    capture_at_pose_remove_clicked = pyqtSignal(CaptureAtPose)
    selected_captures_updated = pyqtSignal()

    def __init__(self, directory: Path, parent=None):
        super().__init__(parent)

        self.directory = directory

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
        self.captures_group_box.setTitle(f"Loading from {self.directory}...")
        QApplication.processEvents()
        for poseID in range(20):
            try:
                # Load from files
                try:
                    robot_pose_yaml_path: Path = self.directory / f"robot_pose_{poseID}.yaml"
                    camera_frame_path: Path = self.directory / f"capture_{poseID}.zdf"
                    robot_pose = TransformationMatrix.from_matrix(np.asarray(zivid.Matrix4x4(robot_pose_yaml_path)))
                    camera_frame = zivid.Frame(camera_frame_path)
                except (FileNotFoundError, RuntimeError) as ex:
                    raise FileNotFoundError(f"Failed to load pose pair from {self.directory}: {ex}") from ex
            except FileNotFoundError:
                continue
            self.add_capture_at_pose(
                robot_pose=robot_pose,
                camera_frame=camera_frame,
                hand_eye_transform=hand_eye_transform,
                eye_in_hand=eye_in_hand,
            )
            QApplication.processEvents()
        self.captures_group_box.setTitle("Captures")

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

    def add_capture_at_pose(
        self,
        robot_pose: TransformationMatrix,
        camera_frame: zivid.Frame,
        hand_eye_transform: TransformationMatrix,
        eye_in_hand: bool,
    ):
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
        self._clear_layout(self.captures_layout)
        self.capture_at_poses.clear()
        self.selected_captures_updated.emit()
