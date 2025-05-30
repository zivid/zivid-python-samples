import copy
from typing import Dict, Optional

from nptyping import NDArray, Shape, UInt8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from zividsamples.gui.hand_eye_configuration import CalibrationObject, HandEyeConfiguration
from zividsamples.gui.image_viewer import ImageViewer
from zividsamples.paths import get_image_file_path


class DetectionVisualizationWidget(QWidget):
    descriptive_image_eye_in_hand: QPixmap
    descriptive_image_eye_to_hand: QPixmap
    hand_eye_configuration: HandEyeConfiguration
    descriptive_image_width: int = 200
    calibration_object_pixmap: Dict[CalibrationObject, Optional[QPixmap]] = {}
    reset_zoom_on_next_calibration_object_image_update: bool = True

    def __init__(self, hand_eye_configuration: HandEyeConfiguration, hide_descriptive_image: bool = False, parent=None):
        super().__init__(parent)

        self.calibration_object_pixmap = {
            CalibrationObject.Checkerboard: None,
            CalibrationObject.Markers: None,
        }

        self.hand_eye_configuration = copy.deepcopy(hand_eye_configuration)
        object_pose_in_camera_frame_eye_in_hand_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-on-robot-camera-object-pose-low-res.png"
        )
        object_pose_in_camera_frame_eye_to_hand_path = get_image_file_path(
            "hand-eye-robot-and-calibration-board-camera-object-pose-low-res.png"
        )
        self.descriptive_image_eye_in_hand = QPixmap(object_pose_in_camera_frame_eye_in_hand_path.as_posix())
        self.descriptive_image_eye_to_hand = QPixmap(object_pose_in_camera_frame_eye_to_hand_path.as_posix())
        descriptive_image = (
            self.descriptive_image_eye_in_hand
            if self.hand_eye_configuration.eye_in_hand
            else self.descriptive_image_eye_to_hand
        )

        self.group_box = QGroupBox()
        self.calibration_object_image_viewer = ImageViewer()
        self.calibration_object_image_viewer.hide()
        self.error_message_label = QLabel("Waiting for capture")
        self.error_message_label.setAlignment(Qt.AlignCenter)
        self.error_message_label.setWordWrap(True)
        self.descriptive_image_label = QLabel()
        self.descriptive_image_label.setScaledContents(True)
        self.descriptive_image_label.setFixedWidth(self.descriptive_image_width)
        self.descriptive_image_label.setFixedHeight(
            int(self.descriptive_image_width * descriptive_image.height() / descriptive_image.width())
        )
        self.descriptive_image_label.setPixmap(descriptive_image)

        group_box_contents_layout = QHBoxLayout()
        group_box_contents_layout.addWidget(self.calibration_object_image_viewer)
        group_box_contents_layout.addWidget(self.error_message_label)
        group_box_contents_layout.addWidget(self.descriptive_image_label)

        self.group_box.setLayout(group_box_contents_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.group_box)
        self.setLayout(layout)
        self.update_layout()
        self.reset_zoom_on_next_calibration_object_image_update = True
        if hide_descriptive_image:
            self.descriptive_image_label.hide()

    def update_layout(self):
        self.group_box.setTitle(f"{self.hand_eye_configuration.calibration_object.name} in Camera Frame")
        self.update_calibration_object_image()
        descriptive_image = (
            self.descriptive_image_eye_in_hand
            if self.hand_eye_configuration.eye_in_hand
            else self.descriptive_image_eye_to_hand
        )
        self.descriptive_image_label.setPixmap(descriptive_image)
        self.descriptive_image_label.setFixedHeight(
            int(self.descriptive_image_width * descriptive_image.height() / descriptive_image.width())
        )

    def on_hand_eye_configuration_updated(self, hand_eye_configuration: HandEyeConfiguration):
        last_calibration_object = self.hand_eye_configuration.calibration_object
        self.hand_eye_configuration = copy.deepcopy(hand_eye_configuration)
        self.reset_zoom_on_next_calibration_object_image_update = (
            last_calibration_object != self.hand_eye_configuration.calibration_object
        )
        self.update_layout()

    def update_calibration_object_image(self, reset_zoom: bool = False):
        calibration_object_pixmap = self.calibration_object_pixmap[self.hand_eye_configuration.calibration_object]
        self.error_message_label.setVisible(calibration_object_pixmap is None)
        self.calibration_object_image_viewer.setVisible(calibration_object_pixmap is not None)
        if calibration_object_pixmap is None:
            self.error_message_label.setText("Waiting for capture")
            self.reset_zoom_on_next_calibration_object_image_update = True
            return
        self.calibration_object_image_viewer.set_pixmap(
            calibration_object_pixmap,
            reset_zoom or self.reset_zoom_on_next_calibration_object_image_update,
        )
        self.reset_zoom_on_next_calibration_object_image_update = reset_zoom

    def set_pixmap(self, pixmap: QPixmap, reset_zoom: bool = False) -> None:
        self.calibration_object_pixmap[self.hand_eye_configuration.calibration_object] = pixmap
        self.update_calibration_object_image(reset_zoom)

    def set_image(self, qimage_rgba: QImage, reset_zoom: bool = False) -> None:
        self.set_pixmap(QPixmap.fromImage(qimage_rgba), reset_zoom)

    def set_rgba_image(self, rgba: NDArray[Shape["N, M, 4"], UInt8], reset_zoom: bool = False) -> None:  # type: ignore
        self.set_image(QImage(rgba.data, rgba.shape[1], rgba.shape[0], QImage.Format_RGBA8888), reset_zoom)

    def set_error_message(self, error_message: str):
        self.error_message_label.setText(error_message)
        self.reset_zoom_on_next_calibration_object_image_update = True
        self.error_message_label.show()
        self.calibration_object_image_viewer.hide()

    def get_qimage(self, calibration_object: CalibrationObject) -> QImage:
        calibration_object_pixmap = self.calibration_object_pixmap[self.hand_eye_configuration.calibration_object]
        if calibration_object_pixmap is None:
            raise RuntimeError(f"No image available for {calibration_object.name}")
        return calibration_object_pixmap.toImage()
