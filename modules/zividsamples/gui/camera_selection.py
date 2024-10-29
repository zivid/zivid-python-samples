"""
Camera Selection

Note: This script requires PyQt5 to be installed.

"""

from typing import List, Optional

import zivid
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtWidgets import QDialog, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout
from zividsamples.gui.qt_application import ZividQtApplication


class CameraSelectionDialog(QDialog):

    def __init__(self, cameras):
        super().__init__()
        self.selected_camera = None
        self.init_ui(cameras)

        QTimer.singleShot(0, self.adjust_dialog_size)

    def init_ui(self, cameras: List[zivid.Camera]):
        self.setWindowTitle("Select a Camera")
        layout = QVBoxLayout(self)

        self.camera_list_widget = QListWidget(self)
        layout.addWidget(self.camera_list_widget)

        self.select_button = QPushButton("Select", self)
        self.select_button.clicked.connect(self.on_select)
        layout.addWidget(self.select_button)

        self.setLayout(layout)

        camera_selected = False
        for camera in cameras:
            camera_item = QListWidgetItem(
                f"{camera.info.model_name} ({camera.info.serial_number} - {camera.state.status})",
                self.camera_list_widget,
            )
            camera_item.setData(1, camera)
            if camera.state.status == zivid.CameraState.Status.available and not camera_selected:
                camera_item.setSelected(True)
                camera_selected = True

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

    def on_select(self):
        selected_items = self.camera_list_widget.selectedItems()
        if selected_items:
            self.selected_camera = selected_items[0].data(1)
        self.accept()


def select_camera(cameras: List[zivid.Camera]) -> Optional[zivid.Camera]:
    dialog = CameraSelectionDialog(cameras)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.selected_camera
    return None


if __name__ == "__main__":  # NOLINT
    qtApp = ZividQtApplication()
    zividApp = zivid.Application()
    select_camera(zividApp.cameras())
    qtApp.exec_()
