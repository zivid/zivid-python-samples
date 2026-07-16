from pathlib import Path

from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


def show_yaml_dialog(yaml_path: Path, title: str, close_button_label: str = "Close") -> None:
    dialog = QDialog()
    dialog.setWindowTitle(title)

    layout = QVBoxLayout()

    path_label = QLabel(f"<b>Saved to</b><br>{yaml_path}")
    path_label.setWordWrap(True)
    layout.addWidget(path_label)

    text_edit = QTextEdit()
    try:
        contents = yaml_path.read_text(encoding="utf-8")
    except OSError as ex:
        contents = f"(Error reading file: {ex})"
    text_edit.setPlainText(contents)
    text_edit.setReadOnly(True)
    text_edit.setLineWrapMode(QTextEdit.NoWrap)
    layout.addWidget(text_edit)

    button_layout = QHBoxLayout()

    copy_button = QPushButton("Copy")
    copy_button.clicked.connect(lambda: QApplication.clipboard().setText(contents))
    button_layout.addWidget(copy_button)

    save_as_button = QPushButton("Save As...")
    save_as_button.clicked.connect(lambda: _save_as(dialog, contents, yaml_path))
    button_layout.addWidget(save_as_button)

    close_button = QPushButton(close_button_label)
    close_button.clicked.connect(dialog.accept)
    button_layout.addWidget(close_button)

    layout.addLayout(button_layout)

    dialog.setLayout(layout)

    def adjust_dialog_size() -> None:
        text_edit.document().adjustSize()
        document_size = text_edit.document().size().toSize()

        margin = 20
        button_height = close_button.sizeHint().height()
        path_label_height = path_label.sizeHint().height()
        document_size.setWidth(document_size.width() + 2 * margin)
        document_size.setHeight(document_size.height() + button_height + path_label_height + 4 * margin)

        dialog.resize(document_size.expandedTo(QSize(600, 450)))

    QTimer.singleShot(0, adjust_dialog_size)

    dialog.exec_()


def _save_as(parent: QDialog, contents: str, default_path: Path) -> None:
    file_path = QFileDialog.getSaveFileName(
        parent,
        "Save As",
        str(default_path),
        "YAML Files (*.yaml);;All Files (*)",
    )[0]
    if file_path:
        try:
            Path(file_path).write_text(contents, encoding="utf-8")
        except OSError as ex:
            QMessageBox.critical(parent, "Save failed", str(ex))
