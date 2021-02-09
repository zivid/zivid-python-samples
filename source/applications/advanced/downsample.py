"""
This example shows how to downsample point cloud from a ZDF file.

The ZDF files for this sample can be found under the main instructions for Zivid samples.
"""

from pathlib import Path
import numpy as np
import open3d as o3d
import zivid
from sample_utils.paths import get_sample_data_path


def _display_pointcloud(xyz, rgb):
    """Display point cloud.

    Args:
        rgb: RGB image
        xyz: X, Y and Z images (point cloud co-ordinates)

    Returns None

    """
    xyz = np.nan_to_num(xyz).reshape(-1, 3)
    rgb = rgb.reshape(-1, 3)

    point_cloud_open3d = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
    point_cloud_open3d.colors = o3d.utility.Vector3dVector(rgb / 255)

    visualizer = o3d.visualization.Visualizer()  # pylint: disable=no-member
    visualizer.create_window()
    visualizer.add_geometry(point_cloud_open3d)

    visualizer.get_render_option().background_color = (0, 0, 0)
    visualizer.get_render_option().point_size = 1
    visualizer.get_render_option().show_coordinate_frame = True
    visualizer.get_view_control().set_front([0, 0, -1])
    visualizer.get_view_control().set_up([0, -1, 0])

    visualizer.run()
    visualizer.destroy_window()


def _main():

    app = zivid.Application()

    data_file = Path() / get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading ZDF frame from file: {data_file}")
    frame = zivid.Frame(data_file)

    point_cloud = frame.point_cloud()
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba")

    print(f"Before downsampling: {point_cloud.width * point_cloud.height} point cloud")

    _display_pointcloud(xyz, rgba[:, :, 0:3])

    print("Downsampling point cloud")
    point_cloud.downsample(zivid.PointCloud.Downsampling.by2x2)
    xyz_donwsampled = point_cloud.copy_data("xyz")
    rgba_downsampled = point_cloud.copy_data("rgba")

    print(f"After downsampling: {point_cloud.width * point_cloud.height} point cloud")

    _display_pointcloud(xyz_donwsampled, rgba_downsampled[:, :, 0:3])

    input("Press Enter to close...")


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
