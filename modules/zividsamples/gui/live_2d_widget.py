import threading
import time
from typing import Callable, Optional

import numpy as np
import zivid
from nptyping import NDArray, Shape, UInt8
from PyQt5.QtCore import Q_ARG, QMetaObject, Qt
from PyQt5.QtGui import QCloseEvent, QColor, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication, QGroupBox, QVBoxLayout, QWidget
from zividsamples.gui.image_viewer import ImageViewer


class Live2DWidget(QWidget):
    is_first: bool = True
    live_active: bool = False
    live_thread: Optional[threading.Thread] = None
    current_rgba: Optional[NDArray[Shape["H, W, 4"], UInt8]] = None  # type: ignore

    def __init__(
        self,
        capture_function: Optional[Callable[[zivid.Settings2D], zivid.Frame2D]],
        settings_2d: zivid.Settings2D,
        parent=None,
    ):
        super().__init__(parent)

        self.capture_function = capture_function
        self.settings_2d = settings_2d

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
            if self.capture_function is None:
                raise RuntimeError("No camera connected.")
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
