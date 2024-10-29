"""
Hand-Eye Settings Tester GUI

Note: This script requires PyQt5 to be installed.

"""

from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import zivid
from nptyping import NDArray, Shape, UInt8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QAction, QCheckBox, QFileDialog, QGroupBox, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget
from zivid.calibration import DetectionResult, DetectionResultFiducialMarkers, MarkerShape
from zivid.experimental import PixelMapping
from zividsamples.gui.buttons_widget import CameraButtonsWidget
from zividsamples.gui.camera_selection import select_camera
from zividsamples.gui.cv2_handler import CV2Handler
from zividsamples.gui.hand_eye_configuration import CalibrationObject, HandEyeButtonsWidget, HandEyeConfiguration
from zividsamples.gui.image_viewer import ImageViewer, ImageViewerDialog
from zividsamples.gui.live_2d_widget import Live2DWidget
from zividsamples.gui.marker_widget import MarkersWidget
from zividsamples.gui.pointcloud_visualizer import show_open3d_visualizer
from zividsamples.gui.qt_application import ZividQtApplication
from zividsamples.gui.settings_selector import Settings, select_settings_for_hand_eye
from zividsamples.transformation_matrix import TransformationMatrix


class CalibrationObjectWidget(QWidget):
    hand_eye_configuration: HandEyeConfiguration
    previously_showed_error_message: bool = True

    def __init__(self, hand_eye_configuration: HandEyeConfiguration, parent=None):
        super().__init__(parent)

        self.hand_eye_configuration = hand_eye_configuration

        self.group_box = QGroupBox()
        self.markers_widget = MarkersWidget()
        self.calibration_object_image = ImageViewer()
        self.calibration_object_image.setMinimumHeight(400)
        self.calibration_object_image.setMinimumWidth(400)

        checkerboard_layout = QHBoxLayout()
        checkerboard_layout.addWidget(self.markers_widget)
        checkerboard_layout.addWidget(self.calibration_object_image)

        self.group_box.setLayout(checkerboard_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.group_box)
        self.setLayout(layout)
        self.update_layout()

    def update_layout(self):
        self.group_box.setTitle(f"{self.hand_eye_configuration.calibration_object.name} in Camera Frame")
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Markers:
            self.calibration_object_image.hide()
            self.markers_widget.show()
        else:
            self.markers_widget.hide()
            self.calibration_object_image.show()

    def on_hand_eye_configuration_updated(self, hand_eye_configuration: HandEyeConfiguration):
        self.hand_eye_configuration = hand_eye_configuration
        self.update_layout()

    def set_markers(
        self,
        markers: List[MarkerShape],
        rgba: NDArray[Shape["N, M, 4"], UInt8],  # type: ignore
        pixel_mapping: PixelMapping,
    ):
        self.markers_widget.set_markers(markers, rgba, pixel_mapping, reset_zoom=self.previously_showed_error_message)
        self.previously_showed_error_message = False

    def set_checkerboard_image(self, rgba: NDArray[Shape["N, M, 4"], UInt8]) -> None:  # type: ignore
        qpixmap = QPixmap.fromImage(QImage(rgba.data, rgba.shape[1], rgba.shape[0], QImage.Format_RGBA8888))
        painter = QPainter(qpixmap)
        font = painter.font()
        font.setPixelSize(128)
        painter.setFont(font)
        painter.setPen(QColor(Qt.green))
        painter.drawText(qpixmap.rect(), Qt.AlignHCenter | Qt.AlignBottom, "Success!")
        painter.end()
        self.calibration_object_image.set_pixmap(qpixmap, reset_zoom=self.previously_showed_error_message)
        self.previously_showed_error_message = False

    def set_error_message(self, error_message: str):
        error_pixmap = QPixmap(400, 400)
        error_pixmap.fill(Qt.gray)  # Set background color
        painter = QPainter(error_pixmap)
        painter.setPen(QColor(Qt.red))
        painter.drawText(error_pixmap.rect(), Qt.AlignCenter, error_message)
        painter.end()
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            self.calibration_object_image.set_pixmap(error_pixmap, reset_zoom=True)
        else:
            self.markers_widget.set_pixmap(error_pixmap, reset_zoom=True)
        self.previously_showed_error_message = True


class TestHandEyeCaptureSettings(QMainWindow):
    hand_eye_configuration: HandEyeConfiguration = HandEyeConfiguration()
    settings: Settings = Settings()
    camera: Optional[zivid.Camera] = None
    last_frame: zivid.Frame

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HandEyeSettingsTester")

        self.cv2_handler = CV2Handler()

        self.setup_camera()
        self.setup_settings()
        self.create_widgets()
        self.setup_layout()
        self.create_toolbar()
        self.connect_signals()

        if self.camera is None:
            self.camera_buttons.set_connection_status(False)
        else:
            self.camera_buttons.set_connection_status(self.camera.state.connected)

        self.live2d_widget.start_live_2d()

    def setup_camera(self):
        self.zividApp = zivid.Application()
        cameras = self.zividApp.cameras()
        if len(cameras) > 0:
            self.camera = select_camera(cameras)
        if self.camera is not None:
            self.camera.connect()

    def setup_settings(self):
        if self.camera:
            self.settings = select_settings_for_hand_eye(self.camera)
            self.live2d_widget.settings_2d = self.settings.settings_2d

    def create_widgets(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        capture_function = None if self.camera is None or self.camera.state.connected is False else self.camera.capture
        self.calibration_object_widget = CalibrationObjectWidget(hand_eye_configuration=self.hand_eye_configuration)
        self.live2d_widget = Live2DWidget(capture_function=capture_function, settings_2d=self.settings.settings_2d)
        self.live2d_widget.setFixedHeight(self.calibration_object_widget.height())
        self.live2d_widget.setFixedWidth(self.calibration_object_widget.height())
        self.hand_eye_configuration_buttons = HandEyeButtonsWidget(
            initial_hand_eye_configuration=HandEyeConfiguration(),
            show_calibration_object_selection=True,
            show_eye_in_hand_selection=False,
        )
        already_connected = False if self.camera is None else self.camera.state.connected
        self.camera_buttons = CameraButtonsWidget(already_connected=already_connected, capture_button_text="Capture")
        self.capture_with_hand_eye_settings = QCheckBox("Use settings optimized for Hand Eye")
        self.capture_with_hand_eye_settings.setChecked(True)

    def setup_layout(self):
        layout = QVBoxLayout(self.central_widget)
        left_panel = QVBoxLayout()
        left_panel_buttons = QHBoxLayout()
        right_panel = QVBoxLayout()
        center_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        left_panel.addWidget(self.calibration_object_widget)
        left_panel.addLayout(left_panel_buttons)
        right_panel.addWidget(self.live2d_widget)
        center_layout.addLayout(left_panel)
        center_layout.addLayout(right_panel)
        layout.addLayout(center_layout)

        if self.camera is None:
            self.live2d_widget.hide()

        bottom_layout.addWidget(self.hand_eye_configuration_buttons)
        bottom_layout.addWidget(self.camera_buttons)
        self.camera_buttons.buttons_layout.addWidget(self.capture_with_hand_eye_settings)
        layout.addLayout(bottom_layout)

    def create_toolbar(self):
        file_menu = self.menuBar().addMenu("File")
        self.save_frame_action = QAction("Save", self)
        self.save_frame_action.triggered.connect(self.on_save_last_frame_action_triggered)
        self.save_frame_action.setEnabled(False)
        file_menu.addAction(self.save_frame_action)
        self.save_settings_action = QAction("Save Settings", self)
        self.save_settings_action.triggered.connect(self.on_save_settings_action_triggered)
        self.save_settings_action.setEnabled(True)
        file_menu.addAction(self.save_settings_action)
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        view_menu = self.menuBar().addMenu("View")
        self.visualize_frame_action = QAction("Visualize", self)
        self.visualize_frame_action.triggered.connect(self.on_visualize_last_frame_action_triggered)
        self.visualize_frame_action.setEnabled(False)
        view_menu.addAction(self.visualize_frame_action)

        select_hand_eye_settings_action = QAction("Select Settings", self)
        select_hand_eye_settings_action.triggered.connect(self.on_select_settings_action_triggered)
        self.menuBar().addAction(select_hand_eye_settings_action)

    def connect_signals(self):
        self.camera_buttons.capture_button_clicked.connect(self.on_capture_button_clicked)
        self.camera_buttons.connect_button_clicked.connect(self.on_connect_button_clicked)
        self.hand_eye_configuration_buttons.hand_eye_configuration_updated.connect(
            self.on_hand_eye_configuration_updated
        )

    def on_capture_button_clicked(self):
        assert self.camera is not None
        self.live2d_widget.stop_live_2d()
        try:
            frame = self.camera.capture(
                self.settings.settings_3d_for_hand_eye
                if self.capture_with_hand_eye_settings.isChecked()
                else self.settings.settings_3d
            )
            self.last_frame = frame
            self.visualize_frame_action.setEnabled(True)
            self.save_frame_action.setEnabled(True)
            frame_2d = self.camera.capture(self.settings.settings_2d)
            rgba = frame_2d.image_srgb().copy_data()
            self.live2d_widget.start_live_2d()
            detection_result = (
                zivid.calibration.detect_calibration_board(frame)
                if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard
                else zivid.calibration.detect_markers(
                    frame,
                    self.calibration_object_widget.markers_widget.marker_configuration.id_list,
                    self.calibration_object_widget.markers_widget.marker_configuration.dictionary,
                )
            )
            if not detection_result.valid():
                calibration_object_text = (
                    "checkerboard"
                    if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard
                    else "markers"
                )
                raise RuntimeError(f"Failed to detect {calibration_object_text}")
            self.log_detection_result(detection_result)
            if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
                self.calibration_object_widget.set_checkerboard_image(rgba)
            else:
                detected_markers = detection_result.detected_markers()
                self.calibration_object_widget.set_markers(detected_markers, rgba, self.settings.pixel_mapping)
        except RuntimeError as ex:
            print(f"Failed to capture: {ex}")
            self.calibration_object_widget.set_error_message(f"Failed to capture:\n{ex}")
            self.live2d_widget.start_live_2d()

    def on_hand_eye_configuration_updated(self, hand_eye_configuration: HandEyeConfiguration):
        self.hand_eye_configuration = hand_eye_configuration
        self.calibration_object_widget.on_hand_eye_configuration_updated(self.hand_eye_configuration)

    def on_connect_button_clicked(self):
        if self.camera is not None and self.camera.state.connected:
            self.live2d_widget.stop_live_2d()
            self.live2d_widget.hide()
            self.camera.disconnect()
            self.camera_buttons.set_connection_status(False)
        else:
            self.camera = select_camera(self.zividApp.cameras())
            if self.camera is None:
                self.camera_buttons.set_connection_status(False)
            else:
                self.camera.connect()
                self.camera_buttons.set_connection_status(self.camera.state.connected)
                self.setup_settings()
                if self.camera.state.connected:
                    self.live2d_widget.capture_function = self.camera.capture
                    self.live2d_widget.show()
                    self.live2d_widget.start_live_2d()

    def on_select_settings_action_triggered(self):
        self.setup_settings()

    def on_save_settings_action_triggered(self):
        assert self.settings.settings_3d is not None
        assert self.settings.settings_3d_for_hand_eye is not None
        file_name = Path(QFileDialog.getSaveFileName(self, "Save Settings", "", "Zivid Settings (*.yml)")[0])
        self.settings.settings_3d.save(file_name.with_suffix(".yml"))
        self.settings.settings_3d_for_hand_eye.save(
            file_name.with_stem(f"{file_name.stem}_for_hand_eye").with_suffix(".yml")
        )

    def on_visualize_last_frame_action_triggered(self):
        point_cloud = self.last_frame.point_cloud()
        rgba = point_cloud.copy_data("srgb")
        qimage = QImage(
            rgba.data,
            rgba.shape[1],
            rgba.shape[0],
            QImage.Format_RGBA8888,
        )
        ImageViewerDialog(qimage, title="Sample Capture - RGB").exec_()
        depth_map = point_cloud.copy_data("z")
        depth_map[np.isnan(depth_map)[:, :]] = np.nanmin(depth_map)
        depth_map_uint8 = (
            (depth_map - np.nanmin(depth_map)) / (np.nanmax(depth_map) - np.nanmin(depth_map)) * 255
        ).astype(np.uint8)
        depth_map_color_map = self.cv2_handler.apply_colormap(depth_map_uint8)
        qimage_depthmap = QImage(
            depth_map_color_map.data,
            depth_map_color_map.shape[1],
            depth_map_color_map.shape[0],
            QImage.Format_RGB888,
        )
        ImageViewerDialog(qimage_depthmap, title="Sample Capture - DepthMap").exec_()
        show_open3d_visualizer(
            self.last_frame.point_cloud().copy_data("xyz").reshape([-1, 3]), rgba[:, :, :3].reshape([-1, 3])
        )

    def on_save_last_frame_action_triggered(self):
        if self.last_frame is not None:
            file_name = QFileDialog.getSaveFileName(self, "Save Capture", "", "Zivid Frame (*.zdf)")[0]
            self.last_frame.save(file_name)

    def log_detection_result(
        self,
        detection_result: Union[DetectionResult, DetectionResultFiducialMarkers],
    ):
        assert self.settings.settings_3d is not None
        log_message = ""
        if self.hand_eye_configuration.calibration_object == CalibrationObject.Checkerboard:
            pose = detection_result.pose()
            checkerboard_pose_in_camera_frame = TransformationMatrix.from_matrix(np.asarray(pose.to_matrix()))
            translation = checkerboard_pose_in_camera_frame.translation
            log_message += (
                f"Calibration board: [{translation[0]:>8.2f}, {translation[1]:>8.2f}, {translation[2]:>8.2f}]"
            )
        else:
            detected_markers = detection_result.detected_markers()
            log_message += "Marker - " if len(detected_markers) < 2 else "Markers - "
            for marker in detected_markers:
                marker_pose_in_camera_frame = TransformationMatrix.from_matrix(np.asarray(marker.pose.to_matrix()))
                translation = marker_pose_in_camera_frame.translation
                log_message += (
                    f"{marker.identifier:>3}: [{translation[0]:>8.2f}, {translation[1]:>8.2f}, {translation[2]:>8.2f}]"
                )
        log_message += f" (Engine: {self.settings.settings_3d.engine:>8}, Sampling: {self.settings.settings_3d.sampling.pixel:>20})"
        print(log_message)


if __name__ == "__main__":  # NOLINT
    qtApp = ZividQtApplication()
    qtApp.run(TestHandEyeCaptureSettings(), "Test Hand Eye Settings")
