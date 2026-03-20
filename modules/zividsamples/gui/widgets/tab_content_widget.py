from pathlib import Path

from PyQt5.QtWidgets import QWidget


class TabContentWidget(QWidget):
    data_directory: Path
    has_pending_changes: bool
    _is_current_tab: bool

    def __init__(self, data_directory: Path, parent=None):
        super().__init__(parent)
        self._is_current_tab = False
        self.data_directory = data_directory
        self.session_info = None
        self.has_pending_changes = True

    def update_data_directory(self, data_directory: Path, session_info=None):
        self.session_info = session_info
        if self.data_directory != data_directory:
            self.data_directory = data_directory
            self.has_pending_changes = True

    def data_directory_has_data(self) -> bool:
        return any(entry.is_file() for entry in self.data_directory.iterdir())

    def is_current_tab(self):
        """Returns True if this tab is currently visible."""
        return self._is_current_tab

    def notify_current_tab(self, widget: QWidget):
        """Called by the parent to notify this widget which tab is currently visible.

        Pending changes are processed immediately regardless of whether this tab is
        current. Since loading happens in a background thread, all tabs can load in
        parallel. The parent is expected to call the current tab first so it gets
        priority.
        """
        is_current = widget is self
        self._is_current_tab = is_current
        self.on_tab_visibility_changed(is_current)
        if self.has_pending_changes:
            self.on_pending_changes()
            self.has_pending_changes = False

    def on_tab_visibility_changed(self, is_current: bool):
        """
        Override in subclasses to handle tab visibility changes.
        :param is_current: True if this tab is now visible, False otherwise.

        We assume that any pending changes should be handled when the tab becomes visible.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def is_loading(self) -> bool:
        """Override in subclasses that perform background loading."""
        return False

    def on_pending_changes(self):
        """Override in subclasses to handle pending changes.

        Called whenever the data directory changes, for all tabs (not only the
        currently visible one). Implementations should clear stale in-memory data
        before loading to avoid showing unnecessary confirmation dialogs.
        """
        raise NotImplementedError("Subclasses should implement this method.")
