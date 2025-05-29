import datetime
import threading
import time
from typing import Callable, Optional

import numpy as np
import zivid
from nptyping import NDArray, Shape, UInt8
from PyQt5.QtCore import Q_ARG, QMetaObject, Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QColor, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication, QGroupBox, QVBoxLayout, QWidget
from zividsamples.gui.image_viewer import ImageViewer


class Live2DWidget(QWidget):
    camera_disconnected = pyqtSignal(str)
    is_first: bool = True
    live_active: bool = False
    live_thread: Optional[threading.Thread] = None
    current_rgba: Optional[NDArray[Shape["H, W, 4"], UInt8]] = None  # type: ignore

    def __init__(
        self,
        capture_function: Optional[Callable[[zivid.Settings2D], zivid.Frame2D]] = None,
        settings_2d: Optional[zivid.Settings2D] = None,
        camera: Optional[zivid.Camera] = None,
        parent=None,
    ):
        super().__init__(parent)

        self.capture_function = capture_function
        self.camera = camera
        self.settings_2d = settings_2d
        if settings_2d is not None and self.camera is not None:
            if self.camera.info.model:
                self.update_settings_2d(settings_2d, self.camera.info.model)

        self.group_box = QGroupBox()
        self.group_box.setTitle("Live 2D")
        self.live_2d_image = ImageViewer()

        live_2d_layout = QVBoxLayout()
        live_2d_layout.addWidget(self.live_2d_image)
        self.group_box.setLayout(live_2d_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.group_box)
        self.setLayout(layout)

    def setMinimumHeight(self, height, aspect_ratio: float = 4 / 3):
        self.live_2d_image.setMinimumHeight(height)
        self.live_2d_image.setMinimumWidth(int(height * aspect_ratio))

    def rgb_to_grayscale(self, rgba_image):
        return np.dot(rgba_image[..., :3], [0.299, 0.587, 0.114])

    def update_exposure_based_on_relative_brightness(self, settings_2d: zivid.Settings2D) -> zivid.Settings2D:
        if settings_2d.acquisitions[0].brightness == 0.0:
            return settings_2d
        assert self.capture_function is not None
        rgba_with_projector = self.capture_function(settings_2d).image_srgb().copy_data()
        grayscale_with_projector = self.rgb_to_grayscale(rgba_with_projector)
        for acquisition in settings_2d.acquisitions:
            acquisition.brightness = 0.0
        rgba_without_projector = self.capture_function(settings_2d).image_srgb().copy_data()
        grayscale_without_projector = self.rgb_to_grayscale(rgba_without_projector)
        grayscale_without_projector[grayscale_without_projector == 0] = np.nan
        # Assuming that more pixels are not in shadow than in shadow, we can use median
        # to get a good estimate of the brightness difference.
        relative_brightness = np.nanmedian(grayscale_with_projector / grayscale_without_projector)
        for acquisition in settings_2d.acquisitions:
            max_exposure_time = datetime.timedelta(microseconds=20000)
            current_exposure_time = acquisition.exposure_time
            exposure_increase = min(
                max_exposure_time - current_exposure_time, current_exposure_time * relative_brightness
            )
            acquisition.exposure_time += exposure_increase
            remaining_relative_brightness = relative_brightness / (exposure_increase / current_exposure_time)
            acquisition.gain *= remaining_relative_brightness
            acquisition.brightness = 0.0
        return settings_2d

    def update_settings_2d(self, settings_2d: zivid.Settings2D, camera_model: str):
        if camera_model in [
            zivid.CameraInfo.Model.zivid2PlusMR60,
            zivid.CameraInfo.Model.zivid2PlusMR130,
            zivid.CameraInfo.Model.zivid2PlusLR110,
        ]:
            settings_2d.sampling.color = zivid.Settings2D.Sampling.Color.grayscale
        self.settings_2d = self.update_exposure_based_on_relative_brightness(
            zivid.Settings2D.from_serialized(zivid.Settings2D.serialize(settings_2d))
        )
        if camera_model in [
            zivid.CameraInfo.Model.zivid2PlusMR60,
            zivid.CameraInfo.Model.zivid2PlusMR130,
            zivid.CameraInfo.Model.zivid2PlusLR110,
        ]:
            self.settings_2d.sampling.pixel = zivid.Settings2D.Sampling.Pixel.by2x2
            # To match the projector frequency of 120 Hz we set it to 8333. This could
            # be dynamically adjusted based on use case (with and without looking at a
            # projected image). In other words, this only matters if you the projector
            # if projecting an image.
            self.settings_2d.acquisitions[0].exposure_time = datetime.timedelta(microseconds=8333)
            self.settings_2d.acquisitions[0].aperture = 4
            self.settings_2d.acquisitions[0].gain = 2.0

    def start_live_2d(self):
        if self.live_thread:
            if self.live_thread.is_alive():
                return
        if self.capture_function is None:
            self.show_error_message("No camera connected")
        else:
            self.live_thread = threading.Thread(target=self.live_2d)
            self.live_thread.daemon = True  # Daemonize the thread to close it when the main program exits
            self.live_thread.start()

    def stop_live_2d(self) -> bool:
        if not self.live_thread:
            raise RuntimeError("There is no Live2D thread")
        if self.live_thread.is_alive():
            self.live_active = False
            self.current_rgba = None
            self.live_thread.join()
            return True
        self.current_rgba = None
        return False

    def live_2d(self):
        self.live_active = True
        while self.live_active:
            if not self.capture():
                self.live_active = False
            time.sleep(0.05)

    def is_active(self) -> bool:
        return self.live_active

    def show_error_message(self, error_message: str):
        error_pixmap = QPixmap(self.live_2d_image.size())
        error_pixmap.fill(Qt.gray)  # Set background color
        painter = QPainter(error_pixmap)
        painter.setPen(QColor(Qt.red))
        painter.drawText(error_pixmap.rect(), Qt.AlignCenter, error_message)
        painter.end()
        QMetaObject.invokeMethod(
            self.live_2d_image, "set_pixmap", Qt.QueuedConnection, Q_ARG(QPixmap, error_pixmap), Q_ARG(bool, True)
        )

    def capture(self) -> bool:
        try:
            if self.camera is None:
                raise RuntimeError("No camera connected.")
            if not self.camera.state.connected:
                raise RuntimeError(
                    f"{self.camera.info.model_name} ({self.camera.info.serial_number}): ({self.camera.state.status}"
                )
            assert self.capture_function is not None
            assert self.settings_2d is not None
            frame_2d = self.capture_function(self.settings_2d)
            self.current_rgba = frame_2d.image_srgb().copy_data()
            if self.current_rgba is None:
                raise RuntimeError("No image returned.")
            qpixmap = QPixmap.fromImage(
                QImage(
                    self.current_rgba.data,
                    self.current_rgba.shape[1],
                    self.current_rgba.shape[0],
                    QImage.Format_RGBA8888,
                )
            )
            QMetaObject.invokeMethod(
                self.live_2d_image,
                "set_pixmap",
                Qt.QueuedConnection,
                Q_ARG(QPixmap, qpixmap),
                Q_ARG(bool, self.is_first),
            )
            QApplication.processEvents()
            self.is_first = False
        except RuntimeError as ex:
            error_message = f"Failed to capture image:\n{ex}"
            self.show_error_message(error_message)
            self.current_rgba = None
            self.is_first = True
            self.camera_disconnected.emit(error_message)
            return False
        return True

    def get_current_rgba(self) -> NDArray[Shape["H, W, 4"], UInt8]:  # type: ignore
        if self.current_rgba is None:
            self.capture()
        if self.current_rgba is None:
            return np.zeros([10, 10, 4], dtype=UInt8)
        return self.current_rgba

    def closeEvent(self, event: QCloseEvent) -> None:  # pylint: disable=C0103
        if self.live_thread:
            print("Waiting for Live 2D to stop... ", end="")
            self.stop_live_2d()
            print("done!")
        super().closeEvent(event)
