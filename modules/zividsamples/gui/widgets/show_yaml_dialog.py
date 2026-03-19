from pathlib import Path

from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtWidgets import QDialog, QPushButton, QTextEdit, QVBoxLayout


def show_yaml_dialog(yaml_path: Path, title: str) -> None:
    dialog = QDialog()
    dialog.setWindowTitle(title)

    layout = QVBoxLayout()

    text_edit = QTextEdit()
    text_edit.setPlainText(yaml_path.read_text(encoding="utf-8"))
    text_edit.setReadOnly(True)
    text_edit.setLineWrapMode(QTextEdit.NoWrap)
    layout.addWidget(text_edit)

    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)

    dialog.setLayout(layout)

    def adjust_dialog_size():
        text_edit.document().adjustSize()
        document_size = text_edit.document().size().toSize()

        margin = 20
        button_height = close_button.sizeHint().height()
        document_size.setWidth(document_size.width() + 2 * margin)
        document_size.setHeight(document_size.height() + button_height + 3 * margin)

        dialog.resize(document_size.expandedTo(QSize(300, 200)))

    QTimer.singleShot(0, adjust_dialog_size)

    dialog.exec_()
