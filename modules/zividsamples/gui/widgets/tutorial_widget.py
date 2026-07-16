from typing import Dict, List, Optional

from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QTextBrowser, QVBoxLayout, QWidget


class TutorialWidget(QWidget):
    view_he_transform_requested = pyqtSignal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.title: str = ""
        self.description: List[str] = []
        self.steps: Dict[str, bool] = {}
        self._he_show: bool = False
        self._he_loaded: bool = False
        self._he_mandatory: bool = False

        self.group_box = QGroupBox("Tutorial", self)

        self.text_area = QTextBrowser()
        self.text_area.setAcceptRichText(True)
        self.text_area.setReadOnly(True)
        self.text_area.setOpenLinks(False)
        self.text_area.anchorClicked.connect(self._on_anchor_clicked)

        group_layout = QVBoxLayout()
        group_layout.addWidget(self.text_area)
        self.group_box.setLayout(group_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.group_box)
        self.setLayout(main_layout)

        self.set_text_margins(25, 25, 25, 25)

    def set_title(self, title: str) -> None:
        self.title = title
        self.update_text()

    def set_description(self, description: List[str]) -> None:
        self.description = description
        self.update_text()

    def clear_steps(self) -> None:
        self.steps.clear()
        self.update_text()

    def add_steps(self, steps: Dict[str, bool]) -> None:
        self.steps.update(steps)
        self.update_text()

    def set_he_transform_status(self, show: bool, loaded: bool, mandatory: bool) -> None:
        self._he_show = show
        self._he_loaded = loaded
        self._he_mandatory = mandatory
        self.update_text()

    def _on_anchor_clicked(self, url: QUrl) -> None:
        if url.toString() == "show_he_transform":
            self.view_he_transform_requested.emit()

    def update_text(self) -> None:
        self.text_area.clear()
        text = f"<h2>{self.title}</h2>"
        he_row = ""
        if self._he_show:
            if self._he_loaded:
                he_row = (
                    "<tr><td style='color: lime;'>&#x2611;</td><td>HE Transform: Loaded &nbsp;"
                    "<a href='show_he_transform' style='color:#7aaddb;'>[view]</a>"
                    "</td></tr>"
                )
            elif self._he_mandatory:
                he_row = (
                    "<tr><td>&#x2610; &#x26a0;</td>"
                    "<td>HE Transform: not loaded &mdash; use <i>File &gt; Load HE Transform</i></td></tr>"
                )
            else:
                he_row = "<tr><td>&#x2610;</td><td>HE Transform: will be set after calibration</td></tr>"
        text += "<table cellpadding='5' style='border-collapse: collapse; width: 100%; margin-top: 10px;'>"
        if self._he_show and self._he_mandatory:
            text += he_row
        for step, completed in self.steps.items():
            checkmark = "&#x2611;" if completed else "&#x2610;"
            style = "style='color: lime;'" if completed else ""
            text += f"<tr><td {style}>{checkmark}</td><td>{step}</td></tr>"
        if self._he_show and not self._he_mandatory:
            text += he_row
        text += "</table>"
        text += "<p>" + "</p><p>".join(paragraph for paragraph in self.description) + "</p>"
        self.text_area.setHtml(text)

    def set_text_margins(self, left: int, top: int, right: int, bottom: int) -> None:
        document = self.text_area.document()
        document.setDocumentMargin(10)

        # For more specific control, use HTML/CSS for padding inside the QTextEdit content
        self.text_area.setStyleSheet(f"QTextEdit {{ padding: {top}px {right}px {bottom}px {left}px; }}")
