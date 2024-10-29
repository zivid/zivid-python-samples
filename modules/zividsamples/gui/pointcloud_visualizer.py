import threading
from typing import List, Optional

import numpy as np
import open3d as o3d
from nptyping import Float32, NDArray, Shape, UInt8
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow


class Open3DVisualizerWidget(QMainWindow):
    open3d_thread: Optional[threading.Thread] = None
    running: bool = False

    def __init__(self):
        super().__init__()

        self.visualizer = o3d.visualization.Visualizer()
        self.pcd_list = []

        self.visualizer.create_window(visible=True)
        self.visualizer.get_render_option().background_color = (0, 0, 0)
        self.visualizer.get_render_option().point_size = 1
        self.visualizer.get_render_option().show_coordinate_frame = True

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_visualization)
        self.timer.start(32)

    def update_visualization(self):
        self.visualizer.poll_events()
        self.visualizer.update_renderer()

    def set_point_cloud(
        self,
        xyz_flattened: List[NDArray[Shape["N, M, 3"], Float32]],  # type: ignore
        rgb_flattened: List[NDArray[Shape["N, M, 3"], UInt8]],  # type: ignore
    ):
        self.visualizer.clear_geometries()
        self.pcd_list = []
        valid_max_z = 0
        for xyz, rgb in zip(xyz_flattened, rgb_flattened):  # noqa: B905
            valid_indices = np.logical_not(np.isnan(xyz).any(axis=1))
            valid_xyz = xyz[valid_indices]
            valid_max_z = max(valid_max_z, np.abs(valid_xyz[:, 2]).max())
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(xyz)
            pcd.colors = o3d.utility.Vector3dVector(rgb / 255)
            self.pcd_list.append(pcd)
            self.visualizer.add_geometry(pcd)

        self.visualizer.get_view_control().set_lookat([0, 0, valid_max_z])
        self.visualizer.get_view_control().set_front([0, 0, 1])
        self.visualizer.get_view_control().set_up([0, 1, 0])

    def closeEvent(self, event):
        self.timer.stop()
        self.visualizer.destroy_window()
        if event is not None:
            event.accept()


def show_open3d_visualizer(xyz_flattened, rgb_flattened):
    valid_indices = np.logical_not(np.isnan(xyz_flattened).any(axis=1))
    valid_xyz = xyz_flattened[valid_indices]
    valid_rgb = rgb_flattened[valid_indices]
    visualizer = o3d.visualization.Visualizer()
    visualizer.create_window()
    visualizer.clear_geometries()
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(valid_xyz)
    pcd.colors = o3d.utility.Vector3dVector(valid_rgb / 255)
    visualizer.add_geometry(pcd)
    visualizer.get_render_option().background_color = (0, 0, 0)
    visualizer.get_render_option().point_size = 1
    visualizer.get_render_option().show_coordinate_frame = True
    visualizer.get_view_control().set_lookat([0, 0, np.abs(valid_xyz[:, 2]).max()])
    visualizer.get_view_control().set_front([0, 0, -1])
    visualizer.get_view_control().set_up([0, -1, 0])
    visualizer.run()
    visualizer.destroy_window()
