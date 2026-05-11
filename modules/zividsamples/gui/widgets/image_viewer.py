from PyQt5.QtCore import QRectF, Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QDialog, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QVBoxLayout


class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_first = True
        self.setScene(QGraphicsScene(self))
        self.setAlignment(Qt.AlignCenter)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._zoom = 0

    @pyqtSlot(QPixmap, bool)
    def set_pixmap(self, image: QPixmap, reset_zoom: bool = False):
        self.scene().clear()
        pixmap_item = QGraphicsPixmapItem(image)
        self.scene().addItem(pixmap_item)
        self.setSceneRect(QRectF(pixmap_item.pixmap().rect()))
        if reset_zoom or self.is_first:
            self.is_first = False
            self._zoom = 0
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1

        if self._zoom > 0:
            self.scale(factor, factor)
        elif self._zoom == 0:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        else:
            self._zoom = 0

    def resize(self, event):
        super().resize(event)
        print("Resizing image_viewer")
        self._zoom = 0
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)


class ImageViewerDialog(QDialog):
    def __init__(self, qimage: QImage, title: str = "Image Viewer", parent=None):
        super().__init__(parent)
        self.image_viewer = ImageViewer()
        self.image_viewer.set_pixmap(QPixmap.fromImage(qimage), reset_zoom=True)
        layout = QVBoxLayout()
        layout.addWidget(self.image_viewer)
        self.setLayout(layout)
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.show()
