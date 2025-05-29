from typing import Dict, List

from PyQt5.QtWidgets import QGroupBox, QTextBrowser, QVBoxLayout, QWidget


class TutorialWidget(QWidget):
    title: str = ""
    description: List[str] = []
    steps: Dict[str, bool] = {}

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.group_box = QGroupBox("Tutorial", self)

        self.text_area = QTextBrowser()
        self.text_area.setAcceptRichText(True)
        self.text_area.setReadOnly(True)
        self.text_area.setOpenExternalLinks(True)

        group_layout = QVBoxLayout()
        group_layout.addWidget(self.text_area)
        self.group_box.setLayout(group_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.group_box)
        self.setLayout(main_layout)

        self.set_text_margins(25, 25, 25, 25)

    def set_title(self, title: str):
        self.title = title
        self.update_text()

    def set_description(self, description: List[str]):
        self.description = description
        self.update_text()

    def clear_steps(self):
        self.steps.clear()
        self.update_text()

    def add_steps(self, steps: Dict[str, bool]):
        self.steps.update(steps)
        self.update_text()

    def update_text(self):
        self.text_area.clear()
        text = f"<h2>{self.title}</h2>"
        text += "<table cellpadding='5' style='border-collapse: collapse; width: 100%;; margin-top: 10px;'>"
        for step, completed in self.steps.items():
            checkmark = "&#x2705;" if completed else "&#x2610;"  # ✓ for checked, ☐ for unchecked
            text += f"<tr><td>{checkmark}</td><td>{step}</td></tr>"
        text += "</table>"
        text += "<p>" + "</p><p>".join(paragraph for paragraph in self.description) + "</p>"
        self.text_area.setHtml(text)

    def set_text_margins(self, left, top, right, bottom):
        document = self.text_area.document()
        document.setDocumentMargin(10)

        # For more specific control, use HTML/CSS for padding inside the QTextEdit content
        self.text_area.setStyleSheet(f"QTextEdit {{ padding: {top}px {right}px {bottom}px {left}px; }}")
