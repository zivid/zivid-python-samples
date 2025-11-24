import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5 import sip
from PyQt5.QtCore import QSettings, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QVBoxLayout,
)
from zividsamples.gui.qt_application import ZividQtApplication, create_horizontal_line

DATE_FORMAT = "%Y%m%d_%H%M%S"


def is_session_folder(session_path: Path) -> bool:
    return (session_path / "session_info.json").is_file()


SESSION_FOLDER_STRUCTURE = {
    "Warmup": "Warmup",
    "Infield": "Infield",
    "Calibration": "Calibration",
    "Touch": "Calibration/Verification-Touch",
    "Projection": "Calibration/Verification-Projection",
    "Stitching": "Calibration/Verification-Stitching",
}


@dataclass
class SessionInfo:
    last_modified_date: str
    created_date: str
    name: str
    root_folder: Path

    def __post_init__(self):
        self._ensure_structure()

    def _ensure_structure(self):
        for sub in SESSION_FOLDER_STRUCTURE.values():
            (self.root_folder / self.name / sub).mkdir(parents=True, exist_ok=True)

    def update_last_modified_date(self):
        self.last_modified_date = datetime.now().strftime(DATE_FORMAT)

    def has_any_data(self) -> bool:
        for sub in SESSION_FOLDER_STRUCTURE.values():
            sub_folder_path = self.root_folder / self.name / sub
            if any(entry.is_file() for entry in sub_folder_path.iterdir()):
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "last_modified_date": self.last_modified_date,
            "created_date": self.created_date,
            "name": self.name,
        }

    def save(self, root_path: Path) -> None:
        json_path = root_path / self.name / "session_info.json"
        with open(json_path, "w", encoding="utf-8") as session_file:
            json.dump(self.to_dict(), session_file)

    @classmethod
    def from_existing(cls, root_folder: Path, session_name: str) -> "SessionInfo":
        with open(root_folder / session_name / "session_info.json", "r", encoding="utf-8") as session_file:
            session_data = json.load(session_file)
            return cls(
                last_modified_date=session_data["last_modified_date"],
                created_date=session_data["created_date"],
                name=session_name,
                root_folder=root_folder,
            )

    @classmethod
    def new(cls, root_folder: Path) -> "SessionInfo":
        date_string = datetime.now().strftime(DATE_FORMAT)
        return cls(
            last_modified_date=date_string,
            created_date=date_string,
            name=date_string,
            root_folder=root_folder,
        )


class DataDirectory:
    root_folder: Path
    session: Optional[SessionInfo]

    def __init__(self):
        qsettings = QSettings("Zivid", "HandEyeGUI")
        qsettings.beginGroup("data_directory")
        self.root_folder = Path(qsettings.value("root_folder", str(Path.cwd()), type=str))
        session_name = qsettings.value("session_name", "", type=str)
        if session_name and (self.root_folder / session_name).exists():
            self.session = SessionInfo.from_existing(self.root_folder, session_name)
        else:
            self.session = SessionInfo.new(self.root_folder)
        self.show_on_startup = qsettings.value("show_on_startup", True, type=bool)
        qsettings.endGroup()

    def existing_sessions(self) -> Dict[str, SessionInfo]:
        if not self.root_folder.exists():
            return {}
        sessions = {
            d.name: SessionInfo.from_existing(self.root_folder, d.name)
            for d in self.root_folder.iterdir()
            if d.is_dir() and is_session_folder(d)
        }
        sessions = dict(
            sorted(
                sessions.items(),
                key=lambda item: item[1].last_modified_date,
                reverse=True,
            )
        )
        return sessions

    def widget_names_with_data_in_session(self, session: SessionInfo) -> List[str]:
        widget_names = []
        for name, sub in SESSION_FOLDER_STRUCTURE.items():
            sub_folder_path = self.root_folder / session.name / sub
            if any(entry.is_file() for entry in sub_folder_path.iterdir()):
                widget_names.append(name)
        return widget_names

    def __str__(self):
        return f"DataDirectory(root_folder={self.root_folder}, session={self.session}, show_on_startup={self.show_on_startup})"

    def save_choice(self):
        qsettings = QSettings("Zivid", "HandEyeGUI")
        qsettings.beginGroup("data_directory")
        qsettings.setValue("root_folder", str(self.root_folder))
        if self.session is not None:
            self.session.update_last_modified_date()
            self.session.save(self.root_folder)
            qsettings.setValue("session_name", self.session.name)
        else:
            qsettings.setValue("session_name", "")
        qsettings.setValue("show_on_startup", self.show_on_startup)
        qsettings.endGroup()


class ClickableLineEdit(QLineEdit):
    clicked = pyqtSignal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setReadOnly(True)

    def mousePressEvent(self, a0):
        # Handle click (e.g., open folder dialog)
        self.clicked.emit()
        super().mousePressEvent(a0)


class DirectoryAndSessionDialog(QDialog):
    SESSION_UNMODIFIED = 1

    def __init__(self, current_data_directory: DataDirectory, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Data Directory and Session")
        self.selected_session = None
        self.data_directory = current_data_directory

        self.setup_widgets()
        self.setup_layout()
        self.connect_signals()

    def setup_widgets(self):
        self.directory_edit = ClickableLineEdit(str(self.data_directory.root_folder), self)
        self.directory_edit.setMinimumWidth(400)
        self.directory_icon = QPushButton(self)
        self.directory_icon.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.directory_icon.setFixedHeight(self.directory_edit.sizeHint().height())

        self.session_list_label = QLabel("Select Session:", self)
        self.list_widget = QListWidget(self)
        # Expand dialog width to fit the widest entry in the list
        self.list_widget.setMinimumHeight(200)
        self.list_widget.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # connect once, covers both insert + reset
        list_widget_model = self.list_widget.model()
        assert list_widget_model is not None
        list_widget_model.rowsInserted.connect(self.adjust_dialog_width)
        list_widget_model.modelReset.connect(self.adjust_dialog_width)
        self.set_session_list()

        self.show_dialog_checkbox = QCheckBox(
            "Show on startup (Note! Will default to new session if not selected)", self
        )
        self.show_dialog_checkbox.setChecked(self.data_directory.show_on_startup)

        self.load_session_button = QPushButton("Load Session", self)
        self.load_session_button.setEnabled(self.list_widget.count() > 0)
        self.new_session_button = QPushButton("New Session", self)

    def setup_layout(self):
        layout = QVBoxLayout(self)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Data Directory:", self))
        path_layout.addWidget(self.directory_edit)
        path_layout.addWidget(self.directory_icon)
        layout.addLayout(path_layout)
        layout.addWidget(create_horizontal_line())

        layout.addWidget(self.session_list_label)
        layout.addWidget(self.list_widget)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.show_dialog_checkbox)
        button_layout.addWidget(self.load_session_button)
        button_layout.addWidget(self.new_session_button)
        layout.addLayout(button_layout)

    def connect_signals(self):
        self.directory_edit.clicked.connect(self._choose_folder)
        self.directory_icon.clicked.connect(self._choose_folder)
        self.load_session_button.clicked.connect(self._choose_session)
        self.new_session_button.clicked.connect(self.accept)

    def adjust_dialog_width(self):
        if not self.list_widget or sip.isdeleted(self.list_widget):
            return
        max_width = self.list_widget.sizeHintForColumn(0) + 2 * self.list_widget.frameWidth()
        min_width = max(max_width, 400)
        self.setMinimumWidth(min_width + 60)  # dialog
        self.list_widget.setMinimumWidth(min_width)

    def root_folder(self) -> Path:
        return Path(self.directory_edit.text())

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Data Directory", self.directory_edit.text())
        if folder:
            self.directory_edit.setText(folder)
            self.selected_session = None  # Reset selected session on folder change
            self.list_widget.clear()
            self.data_directory.root_folder = Path(folder)
            self.set_session_list()
            self.load_session_button.setEnabled(self.list_widget.count() > 0)

    def set_session_list(self):
        self.list_widget.clear()
        current_item = None
        for session in self.data_directory.existing_sessions().values():
            if not session.has_any_data() and session != self.data_directory.session:
                continue
            widget_names = self.data_directory.widget_names_with_data_in_session(session)
            item_name = session.name
            if len(widget_names) > 0:
                item_name += f" ({', '.join(widget_names)})"
            item = QListWidgetItem(item_name)
            item.setData(self.SESSION_UNMODIFIED, session)
            self.list_widget.addItem(item)
            if session == self.data_directory.session:
                current_item = item
                current_item.setText(f"{item_name} (current)")
        if current_item is not None:
            self.list_widget.setCurrentItem(current_item)
            self.list_widget.scrollToItem(current_item, QListWidget.PositionAtCenter)
        else:
            self.list_widget.setCurrentRow(0)

    def _choose_session(self):
        current_item = self.list_widget.currentItem()
        if current_item is not None:
            self.selected_session = current_item.data(self.SESSION_UNMODIFIED)
        self.accept()

    def done(self, a0):
        model = self.list_widget.model()
        try:
            model.rowsInserted.disconnect(self.adjust_dialog_width)
            model.modelReset.disconnect(self.adjust_dialog_width)
        except TypeError:
            pass  # already disconnected
        super().done(a0)


class DataDirectoryManager:

    def __init__(self):
        self.data_directory = DataDirectory()
        self.tab_widgets = {}

    def register_tab_widget(self, widget, name: str):
        assert name not in self.tab_widgets, f"Widget with name {name} already registered."
        assert (
            name in SESSION_FOLDER_STRUCTURE
        ), f"Unexpected widget directory name. Got {name}, expected one of {list(SESSION_FOLDER_STRUCTURE)}."
        self.tab_widgets[name] = widget

    def start_new_session(self):
        self.close_session()
        self.data_directory.session = SessionInfo.new(self.data_directory.root_folder)
        self.data_directory.save_choice()
        self._notify_tab_widgets()

    def _notify_tab_widgets(self):
        for widget in self.tab_widgets.values():
            if hasattr(widget, "update_data_directory"):
                widget.update_data_directory(self.folder(widget.objectName()))

    def select_folder(self):
        dialog = DirectoryAndSessionDialog(self.data_directory)
        if dialog.exec_() == QDialog.Accepted:
            self.data_directory.root_folder = dialog.root_folder()
            self.data_directory.show_on_startup = dialog.show_dialog_checkbox.isChecked()
            if dialog.selected_session != self.data_directory.session:
                self.close_session()
            if dialog.selected_session is None:
                self.start_new_session()
            else:
                self.data_directory.session = dialog.selected_session
                self.data_directory.save_choice()
                self._notify_tab_widgets()

    def folder(self, widget_name) -> Path:
        if not self.data_directory.session:
            raise RuntimeError("No session selected. Did you forget to call start_new_session() or select_folder()?")
        path = (
            self.data_directory.root_folder
            / self.data_directory.session.name
            / SESSION_FOLDER_STRUCTURE.get(widget_name, "")
        )
        if not path.exists():
            raise RuntimeError(f"Folder {path} does not exist. The widget {widget_name} is not registered.")
        return path

    def show_on_startup(self) -> bool:
        return self.data_directory.show_on_startup

    def close_session(self):
        if self.data_directory.session and not self.data_directory.session.has_any_data():
            shutil.rmtree(self.data_directory.root_folder / self.data_directory.session.name, ignore_errors=True)
            self.data_directory.session = None

        self.data_directory.save_choice()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close_session()


if __name__ == "__main__":
    with ZividQtApplication():
        print(f"Before session: {DataDirectory()}")
        with DataDirectoryManager() as manager:
            manager.select_folder()
            print(f"In session, after first choice: {DataDirectory()}, (actual session: {manager.data_directory})")
            manager.start_new_session()
            print(f"In session, after new session: {DataDirectory()} (actual session: {manager.data_directory})")
            manager.select_folder()
            print(f"In session, before exit: {DataDirectory()} (actual session: {manager.data_directory})")
        print(f"After session: {DataDirectory()}")
