import ctypes
import os
import sys
from dataclasses import dataclass
from typing import Tuple

from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QFrame
from zividsamples.paths import get_image_file_path

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"


def _color_text(color: Tuple[int, int, int], opacity: float) -> str:
    return f"rgba({color[0]}, {color[1]}, {color[2]}, {opacity})"


def color_as_qcolor(color: Tuple[int, int, int], opacity: float) -> QColor:
    return QColor(color[0], color[1], color[2], int(opacity * 255))


def styled_link(text: str, href: str) -> str:
    return f'<a href={href} style="color: {_color_text(ZividColors.PINK, 0.9)};">{text}</a>'


def create_vertical_line() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.VLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setProperty("isVerticalLine", True)
    return line


def create_horizontal_line() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setProperty("isHorizontalLine", True)
    return line


@dataclass(frozen=True)
class ZividColors:
    BLACK: Tuple[int, int, int] = (0, 0, 0)
    DARK_GRAY: Tuple[int, int, int] = (36, 36, 36)
    MAIN_BACKGROUND: Tuple[int, int, int] = (48, 48, 48)
    MEDIUM_LIGHT_GRAY: Tuple[int, int, int] = (60, 60, 60)
    ITEM_BACKGROUND: Tuple[int, int, int] = (82, 82, 82)
    DISABLED_TEXT: Tuple[int, int, int] = (160, 160, 160)
    DARK_BLUE: Tuple[int, int, int] = (74, 143, 164)
    LIGHT_BLUE: Tuple[int, int, int] = (145, 210, 200)
    PINK: Tuple[int, int, int] = (237, 52, 114)


MAIN_STYLE = f"""
QWidget {{
    color: white;
    background-color: {_color_text(ZividColors.MAIN_BACKGROUND, 1)};
}}
"""

BUTTON_STYLE = f"""
QPushButton {{
    background-color: {_color_text(ZividColors.ITEM_BACKGROUND, 1)};
    color: white;
    border: none;
    padding: 10px;
    border-radius: 4px;
}}

QPushButton:pressed {{
    background-color: {_color_text(ZividColors.DARK_GRAY, 1)};
}}

QPushButton:checked {{
    background-color: {_color_text(ZividColors.DARK_GRAY, 1)};
    color: black;
}}

QPushButton:disabled {{
    background-color: {_color_text(ZividColors.ITEM_BACKGROUND, 0.5)};
    color: {_color_text(ZividColors.DISABLED_TEXT, 1)};
}}

QPushButton QLabel{{
    background-color: {_color_text(ZividColors.BLACK, 0)};
}}
"""

LABEL_STYLE = f"""
QTextEdit {{
    background-color: {_color_text(ZividColors.LIGHT_BLUE, 0.1)};
}}
"""

LINE_EDIT_STYLE = f"""
QLineEdit {{
    background-color: {_color_text(ZividColors.LIGHT_BLUE, 0.1)};
}}
QLineEdit:read-only {{
    background-color: {_color_text(ZividColors.ITEM_BACKGROUND, 0.5)};
    border: none;
}}
"""

GROUP_STYLE = f"""
QGroupBox {{
    border: 2px solid {_color_text(ZividColors.DARK_BLUE, 1)};
    border-radius: 4px;
    margin-top: 20px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}}
"""

TAB_STYLE = f"""
QTabWidget::pane {{
    border-top: 2px solid {_color_text(ZividColors.DARK_BLUE, 1)};
}}
QTabWidget#main_tab_widget::pane {{
    border-top: none;
}}
QTabWidget::tab-bar {{
    left: 15px;
}}
QTabWidget#preparation_tab_widget::tab-bar {{
    left: 5px;
    border: 2px solid {_color_text(ZividColors.DARK_BLUE, 1)};
}}
QTabWidget#verification_tab_widget::tab-bar {{
    left: 9.5em; /* Approximate offset by the width of "PREPARE" and "CALIBRATE" tabs */
    border: 2px solid {_color_text(ZividColors.DARK_BLUE, 1)};
}}
QTabBar::tab {{
    color: white;
    background-color: {_color_text(ZividColors.MEDIUM_LIGHT_GRAY, 1)};
    border: 2px solid {_color_text(ZividColors.DARK_BLUE, 1)};
    padding: 5px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {_color_text(ZividColors.DARK_BLUE, 1)};
}}
QTabBar::tab:!selected {{
    border: 2px solid {_color_text(ZividColors.MEDIUM_LIGHT_GRAY, 1)};
    margin-top: 2px;
}}
QTabWidget#preparation_tab_widget QTabBar::tab, QTabWidget#verification_tab_widget QTabBar::tab {{
    border-top-left-radius: 0px;
    border-top-right-radius: 0px;
    margin-right: 0px;
}}
QTabWidget#preparation_tab_widget QTabBar::tab::first, QTabWidget#verification_tab_widget QTabBar::tab::first {{
    border-left: 2px solid {_color_text(ZividColors.DARK_BLUE, 1)};
    border-top-left-radius: 4px;
}}
QTabWidget#preparation_tab_widget QTabBar::tab::last, QTabWidget#verification_tab_widget QTabBar::tab::last {{
    border-right: 2px solid {_color_text(ZividColors.DARK_BLUE, 1)};
    border-top-right-radius: 4px;
}}
QTabWidget#preparation_tab_widget QTabBar::tab:selected, QTabWidget#verification_tab_widget QTabBar::tab:selected {{
    border: 2px solid {_color_text(ZividColors.DARK_BLUE, 1)};
}}
QTabWidget#preparation_tab_widget QTabBar::tab:!selected, QTabWidget#verification_tab_widget QTabBar::tab:!selected {{
    border-top: 2px solid {_color_text(ZividColors.DARK_BLUE, 1)};
    margin-top: 0px;
}}
QTabBar::tab:hover {{
    background-color: {_color_text(ZividColors.ITEM_BACKGROUND, 1)};
}}
"""

TABLE_STYLE = f"""
QTableWidget {{
    gridline-color: transparent;
    background-color: {_color_text(ZividColors.ITEM_BACKGROUND, 1)};
    color: white;
}}
QTableWidget::item {{
    background-color: transparent;
    color: white;
    padding: 10px;
}}
QHeaderView::section {{
    background-color: {_color_text(ZividColors.DARK_GRAY, 1)};
    font-weight: bold;
    padding: 5px;
    color: white;
}}
QTableWidget::item:selected {{
    background-color: {_color_text(ZividColors.MEDIUM_LIGHT_GRAY, 1)};
}}
"""

MENU_BAR_STYLE = f"""
QMenuBar {{
    background-color: {_color_text(ZividColors.MEDIUM_LIGHT_GRAY, 1)};
    color: white;
}}
QMenuBar::item:selected {{
    background-color: {_color_text(ZividColors.ITEM_BACKGROUND, 1)};
}}
QMenu {{
    background-color: {_color_text(ZividColors.DARK_GRAY, 1)};
    color: white;
}}
QMenu::item:selected {{
    background-color: {_color_text(ZividColors.ITEM_BACKGROUND, 0.75)};
}}
QMenu::item:disabled {{
    color: {_color_text(ZividColors.DISABLED_TEXT, 1)};
}}
"""

MISC_STYLE = f"""
QFrame[isHorizontalLine="true"] {{
    border: 2px solid {_color_text(ZividColors.LIGHT_BLUE, 0.25)};
    border-radius: 4px;
}}
QFrame[isVerticalLine="true"] {{
    border: 1px solid {_color_text(ZividColors.LIGHT_BLUE, 0.25)};
    border-radius: 4px;
}}
"""


@dataclass(frozen=True)
class ZividFonts:
    large: QFont = QFont("Helvetica", 14)
    normal: QFont = QFont("Helvetica", 11)
    small: QFont = QFont("Helvetica", 10)


class ZividQtApplication(QApplication):

    def __init__(self, use_zivid_app: bool = True):
        if "cv2" in sys.modules:
            raise RuntimeError(
                "When using a ZividQtApplication you cannot directly load/import cv2. It has conflicting versions of Qt on some platforms. Instead, add functionality to zividsamples.cv2_handler"
            )
        super().__init__(sys.argv)
        self.setStyleSheet(
            MAIN_STYLE
            + GROUP_STYLE
            + LABEL_STYLE
            + LINE_EDIT_STYLE
            + BUTTON_STYLE
            + TAB_STYLE
            + TABLE_STYLE
            + MENU_BAR_STYLE
            + MISC_STYLE
        )
        self.setFont(ZividFonts.normal)

        if use_zivid_app:
            import zivid  # pylint: disable=import-outside-toplevel

            self.zivid_app = zivid.Application()

    def run(self, win, title: str = "Zivid Qt Application"):
        icon_path = get_image_file_path("LogoZBlue.ico")
        self.setWindowIcon(QIcon(icon_path.absolute().as_posix()))
        win.setWindowTitle(title)
        win.show()
        screen_geometry = QDesktopWidget().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        window_width = min(win.width(), screen_width - 100)
        window_height = min(win.height(), screen_height - 100)
        win.setGeometry(50, 50, window_width, window_height)
        win.resize(window_width, window_height)
        win.move((screen_width - window_width) // 2, (screen_height - window_height) // 2)
        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("zivid.app.qt_application")

        return self.exec_()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if hasattr(self, "zivid_app"):
            self.zivid_app.release()
