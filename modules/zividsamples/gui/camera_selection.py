"""
Camera Selection

Note: This script requires PyQt5 to be installed.

"""

from typing import Optional

import zivid
from PyQt5.QtCore import QObject, QSize, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout
from zividsamples.gui.qt_application import ZividQtApplication

CAMERA_ROLE = 1


class FirmwareUpdateWorker(QObject):
    progress = pyqtSignal(float, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, camera):
        super().__init__()
        self.camera = camera

    @pyqtSlot()
    def run(self):
        try:
            zivid.firmware.update(self.camera, self._progress_callback)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _progress_callback(self, progress: float, description: str):
        self.progress.emit(progress, description)


class CameraSelectionDialog(QDialog):

    def __init__(self, zivid_app: zivid.Application, connect: bool):
        super().__init__()
        self.selected_camera: Optional[zivid.Camera] = None
        self.firmware_updater_worker: Optional[FirmwareUpdateWorker] = None
        self.firmware_updater_thread: QThread = QThread()
        self.zivid_app = zivid_app
        self.connect = connect
        self.init_ui()

        QTimer.singleShot(0, self.find_cameras)

    def init_ui(self):
        self.setWindowTitle("Select a Camera")
        layout = QVBoxLayout(self)

        self.camera_list_widget = QListWidget(self)
        layout.addWidget(self.camera_list_widget)

        self.select_button = QPushButton("Select", self)
        self.select_button.clicked.connect(self.on_select)
        self.select_button.setEnabled(False)
        layout.addWidget(self.select_button)

        self.setLayout(layout)

    def find_cameras(self):
        self.camera_list_widget.addItem("Finding cameras...")
        QTimer.singleShot(100, self.update_camera_list)

    def update_camera_list(self):
        cameras = self.zivid_app.cameras()
        self.camera_list_widget.clear()
        camera_selected = False
        for camera in cameras:
            camera_item = QListWidgetItem(
                f"{camera.info.model_name} ({camera.info.serial_number} - {camera.state.status})",
                self.camera_list_widget,
            )
            camera_item.setData(CAMERA_ROLE, camera)
            if camera.state.status == zivid.CameraState.Status.available and not camera_selected:
                camera_item.setSelected(True)
                camera_selected = True
        self.select_button.setEnabled(True)
        if len(cameras) == 0:
            self.camera_list_widget.addItem("No cameras found.")
            self.select_button.setText("Ok")
        elif not camera_selected:
            self.camera_list_widget.addItem("No available cameras found.")
            self.select_button.setText("Ok")
        QTimer.singleShot(0, self.adjust_dialog_size)

    def adjust_dialog_size(self):
        max_width = 0
        for index in range(self.camera_list_widget.count()):
            item = self.camera_list_widget.item(index)
            item_width = self.camera_list_widget.fontMetrics().boundingRect(item.text()).width()
            max_width = max(max_width, item_width)

        max_width += 40  # Adding padding
        self.camera_list_widget.setMinimumWidth(max_width)
        dialog_size = QSize(max_width, self.sizeHint().height())
        self.resize(dialog_size.expandedTo(QSize(300, 200)))

    def on_firmware_update_progress(self, progress: float, description: str):
        self.camera_list_widget.addItem(f"Firmware update progress: {progress}% ({description})")
        self.camera_list_widget.scrollToBottom()

    def on_firmware_update_finished(self):
        self.camera_list_widget.addItem("Firmware update complete.")
        self.camera_list_widget.addItem("Connecting...")
        QTimer.singleShot(100, lambda: self.connect_camera(self.selected_camera))

    def on_firmware_update_error(self, error_message: str):
        QMessageBox.critical(self, "Firmware Update Error", error_message)
        QTimer.singleShot(100, self.find_cameras)

    def setup_firmware_update_thread(self, camera: zivid.Camera):
        if not self.firmware_updater_thread:
            self.firmware_updater_thread = QThread()
        self.firmware_updater_worker = FirmwareUpdateWorker(camera)
        self.firmware_updater_worker.moveToThread(self.firmware_updater_thread)
        self.firmware_updater_thread.started.connect(self.firmware_updater_worker.run)
        self.firmware_updater_worker.progress.connect(self.on_firmware_update_progress)
        self.firmware_updater_worker.finished.connect(self.on_firmware_update_finished)
        self.firmware_updater_worker.error.connect(self.on_firmware_update_error)
        # Cleanup
        self.firmware_updater_worker.finished.connect(self.firmware_updater_thread.quit)
        self.firmware_updater_worker.finished.connect(self.firmware_updater_worker.deleteLater)
        self.firmware_updater_thread.finished.connect(self.firmware_updater_thread.deleteLater)
        self.firmware_updater_worker.error.connect(self.firmware_updater_thread.quit)
        self.firmware_updater_worker.error.connect(self.firmware_updater_worker.deleteLater)

    def update_firmware(self, camera: zivid.Camera):
        if camera is not None:
            try:
                self.camera_list_widget.clear()
                self.camera_list_widget.addItem("Updating firmware... Please wait.")
                self.setup_firmware_update_thread(camera)
                self.firmware_updater_thread.start()
            except RuntimeError as e:
                self.camera_list_widget.clear()
                QTimer.singleShot(100, self.find_cameras)
                QMessageBox.critical(
                    self, "Connection Error", f"Failed to connect to camera {camera.info.serial_number}: {str(e)}"
                )

    def connect_camera(self, camera: Optional[zivid.Camera]):
        if camera is not None:
            try:
                camera.connect()
                self.accept()
            except RuntimeError as e:
                self.camera_list_widget.clear()
                QTimer.singleShot(100, self.find_cameras)
                QMessageBox.critical(
                    self, "Connection Error", f"Failed to connect to camera {camera.info.serial_number}: {str(e)}"
                )

    def on_select(self):
        selected_items = self.camera_list_widget.selectedItems()
        if selected_items:
            self.selected_camera = selected_items[0].data(CAMERA_ROLE)
        if self.connect and self.selected_camera:
            if self.selected_camera.state.status == zivid.CameraState.Status.firmwareUpdateRequired:
                update_firmware = QMessageBox.question(
                    self,
                    "Firmware Update Required",
                    f"Camera {self.selected_camera.info.serial_number} requires a firmware update. Do you wish to upgrade?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if update_firmware == QMessageBox.Yes:
                    self.camera_list_widget.clear()
                    self.camera_list_widget.addItem("Connecting...")
                    QTimer.singleShot(100, lambda: self.update_firmware(self.selected_camera))
                else:
                    if self.connect:
                        self.selected_camera = None
                    self.accept()
            elif self.selected_camera.state.status != zivid.CameraState.Status.available:
                QMessageBox.info(
                    self,
                    "Camera Not Available",
                    f"Camera {self.selected_camera.info.serial_number} is still not available. Will not connect.",
                )
                if self.connect:
                    self.selected_camera = None
                self.accept()
            else:
                self.camera_list_widget.clear()
                self.camera_list_widget.addItem("Connecting...")
                QTimer.singleShot(100, lambda: self.connect_camera(self.selected_camera))
        else:
            self.accept()


def select_camera(zivid_app: zivid.Application, connect: bool) -> Optional[zivid.Camera]:
    dialog = CameraSelectionDialog(zivid_app, connect)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.selected_camera
    return None


if __name__ == "__main__":  # NOLINT
    with ZividQtApplication() as qtApp:
        selected_camera = select_camera(qtApp.zivid_app, connect=True)
        print(f"Selected camera: {selected_camera}")
