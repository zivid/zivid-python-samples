"""
Camera Selection

Note: This script requires PyQt5 to be installed.

"""

from typing import Optional

import zivid
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtWidgets import QDialog, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout
from zividsamples.gui.qt_application import ZividQtApplication

CAMERA_ROLE = 1


class CameraSelectionDialog(QDialog):

    def __init__(self, zivid_app: zivid.Application, connect: bool):
        super().__init__()
        self.selected_camera: Optional[zivid.Camera] = None
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
        QTimer.singleShot(0, self.update_camera_list)

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
        self.select_button.setEnabled(camera_selected)
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

    def connect_camera(self, camera: Optional[zivid.Camera]):
        if camera is not None:
            camera.connect()
            self.accept()

    def on_select(self):
        selected_items = self.camera_list_widget.selectedItems()
        if selected_items:
            self.selected_camera = selected_items[0].data(CAMERA_ROLE)
        if self.connect and self.selected_camera:
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
