import threading
from time import sleep
from typing import Union

import zivid


class VisualizerWidget:
    visualizer_thread: threading.Thread
    visualizer: zivid.visualization.Visualizer

    def __init__(self):
        self.visualizer_thread = threading.Thread(target=self.run, daemon=True)
        self.visualizer_thread.start()

    def run(self):
        self.visualizer = zivid.visualization.Visualizer()
        self.visualizer.set_window_title("Zivid Point Cloud Visualizer")
        self.visualizer.colors_enabled = True
        self.visualizer.axis_indicator_enabled = True
        self.visualizer.hide()
        self.visualizer.run()
        self.visualizer.release()

    def set_point_cloud(self, data: Union[zivid.Frame, zivid.PointCloud, zivid.UnorganizedPointCloud]):
        if not self.visualizer_thread.is_alive():
            self.visualizer_thread = threading.Thread(target=self.run, daemon=True)
            self.visualizer_thread.start()
            sleep(0.2)  # Give some time for the thread to start
        self.visualizer.show(data)

    def hide(self):
        if self.visualizer_thread.is_alive():
            self.visualizer.hide()

    def close(self) -> None:
        if self.visualizer_thread.is_alive():
            self.visualizer.close()
            self.visualizer_thread.join()
