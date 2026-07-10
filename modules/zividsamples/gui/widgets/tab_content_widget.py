from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QWidget
from zividsamples.gui.wizard.data_directory import SessionInfo


class TabContentWidget(QWidget):
    data_directory: Path
    has_pending_changes: bool
    _is_current_tab: bool

    def __init__(self, data_directory: Path, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._is_current_tab = False
        self.data_directory = data_directory
        self.session_info = None
        self.has_pending_changes = True

    def update_data_directory(self, data_directory: Path, session_info: Optional[SessionInfo] = None) -> None:
        self.session_info = session_info
        if self.data_directory != data_directory:
            self.data_directory = data_directory
            self.has_pending_changes = True

    def data_directory_has_data(self) -> bool:
        return any(entry.is_file() for entry in self.data_directory.iterdir())

    def is_current_tab(self) -> bool:
        """Returns True if this tab is currently visible.

        Returns:
            True if this tab is currently visible.
        """
        return self._is_current_tab

    def notify_current_tab(self, widget: QWidget) -> None:
        """Called by the parent to notify this widget which tab is currently visible.

        Pending changes are processed immediately regardless of whether this tab is
        current. Since loading happens in a background thread, all tabs can load in
        parallel. The parent is expected to call the current tab first so it gets
        priority.

        Args:
            widget: The widget that is currently the visible tab.
        """
        is_current = widget is self
        self._is_current_tab = is_current
        self.on_tab_visibility_changed(is_current)
        if self.has_pending_changes:
            self.on_pending_changes()
            self.has_pending_changes = False

    def on_tab_visibility_changed(self, is_current: bool) -> None:
        """Override in subclasses to handle tab visibility changes.

        We assume that any pending changes should be handled when the tab becomes visible.

        Args:
            is_current: True if this tab is now visible, False otherwise.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def is_loading(self) -> bool:
        """Override in subclasses that perform background loading.

        Returns:
            True if this tab is currently loading data in the background.
        """
        return False

    def on_pending_changes(self) -> None:
        """Override in subclasses to handle pending changes.

        Called whenever the data directory changes, for all tabs (not only the
        currently visible one). Implementations should clear stale in-memory data
        before loading to avoid showing unnecessary confirmation dialogs.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method.")
