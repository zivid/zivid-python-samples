import threading
from typing import Optional, Union

import zivid


class VisualizerWidget:
    visualizer_thread: threading.Thread
    visualizer: Optional[zivid.visualization.Visualizer]

    def __init__(self) -> None:
        self._ready = threading.Event()
        self.visualizer = None
        self._failed = False
        self._start_thread()

    def _start_thread(self) -> None:
        self._ready.clear()
        self.visualizer_thread = threading.Thread(target=self.run, daemon=True)
        self.visualizer_thread.start()

    def run(self) -> None:
        try:
            visualizer = zivid.visualization.Visualizer()
            visualizer.set_window_title("Zivid Point Cloud Visualizer")
            visualizer.colors_enabled = True
            visualizer.axis_indicator_enabled = True
            visualizer.hide()
        except RuntimeError as ex:
            self._failed = True
            self.visualizer = None
            print(f"Point cloud visualizer unavailable: {ex}")
            self._ready.set()
            return
        self.visualizer = visualizer
        self._ready.set()
        visualizer.run()
        visualizer.release()

    def set_point_cloud(self, data: Union[zivid.Frame, zivid.PointCloud, zivid.UnorganizedPointCloud]) -> None:
        if not self.visualizer_thread.is_alive() and not self._failed:
            self._start_thread()
        self._ready.wait()
        if self.visualizer is not None:
            self.visualizer.show(data)

    def hide(self) -> None:
        self._ready.wait()
        if self.visualizer is not None:
            self.visualizer.hide()

    def close(self) -> None:
        self._ready.wait()
        if self.visualizer is not None and self.visualizer_thread.is_alive():
            self.visualizer.close()
            self.visualizer_thread.join()
