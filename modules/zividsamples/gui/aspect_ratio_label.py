from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout


class AspectRatioLabel(QLabel):

    def __init__(self, title: str, pixmap, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.original_pixmap = pixmap
        self.title = title
        self.setPixmap()

    def set_original_pixmap(self, pixmap):
        self.original_pixmap = pixmap
        self.setPixmap()

    def setPixmap(self):
        super().setPixmap(self.scaledPixmap())

    def resizeEvent(self, _):
        if self.original_pixmap:
            self.setPixmap()

    def scaledPixmap(self):
        size = self.size()
        return self.original_pixmap.scaledToHeight(size.height(), Qt.SmoothTransformation)

    def setFixedHeight(self, height):
        constrained_height = min(max(self.minimumHeight(), height), self.maximumHeight())
        super().setFixedHeight(constrained_height)

    # pylint: disable=too-many-positional-arguments
    def setHeightFromGrid(self, grid_layout, row_start, row_span, col_start, col_span):
        max_height = 0 if row_start > 0 else grid_layout.verticalSpacing()
        for row in range(row_start, row_start + row_span):
            max_height += grid_layout.verticalSpacing()
            max_height_within_row = 0
            for col in range(col_start, col_start + col_span):
                item = grid_layout.itemAtPosition(row, col)
                if item:
                    widget = item.widget()
                    if widget:
                        widget_height = widget.sizeHint().height()
                        max_height_within_row = max(max_height_within_row, widget_height)
            max_height += max_height_within_row
        max_height += grid_layout.verticalSpacing()

        self.setFixedHeight(max_height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.show_original_pixmap()

    def show_original_pixmap(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.title)
        dialog.setModal(True)

        pixmap_label = QLabel()
        pixmap_label.setPixmap(self.original_pixmap)
        pixmap_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(pixmap_label)
        dialog.setLayout(layout)

        dialog.resize(self.original_pixmap.size())

        dialog.exec_()
