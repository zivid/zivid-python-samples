"""
Read point cloud data from a ZDF file, apply a binary mask, and visualize it.

The ZDF file for this sample can be found under the main instructions for Zivid samples.

"""

import sys

import numpy as np
import zivid
from zividsamples.display import display_depthmap, display_pointcloud, display_rgb
from zividsamples.paths import get_sample_data_path

try:
    import open3d as o3d
except ImportError:
    print(
        "⚠️  Failed to import Open3D. It is installed via `pip install -r requirements.txt`, "
        f"however it might not be available for your Python version: {sys.version_info.major}.{sys.version_info.minor}. "
        "See https://pypi.org/project/open3d/ for supported versions."
    )
    sys.exit(1)


def _copy_to_open3d_point_cloud(xyz: np.ndarray, rgb: np.ndarray) -> o3d.geometry.PointCloud:
    """Copy point cloud data to Open3D PointCloud object.

    Args:
        xyz: A numpy array of X, Y and Z point cloud coordinates
        rgb: RGB image

    Returns:
        An Open3D PointCloud object
    """
    xyz = np.nan_to_num(xyz).reshape(-1, 3)
    rgb = rgb.reshape(-1, rgb.shape[-1])[:, :3]

    open3d_point_cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
    open3d_point_cloud.colors = o3d.utility.Vector3dVector(rgb / 255)
    return open3d_point_cloud


def _display_open3d_point_cloud(open3d_point_cloud: o3d.geometry.PointCloud) -> None:
    """Display Open3D PointCloud object.

    Args:
        open3d_point_cloud: Open3D PointCloud object to display
    """
    visualizer = o3d.visualization.Visualizer()  # pylint: disable=no-member
    visualizer.create_window()
    visualizer.add_geometry(open3d_point_cloud)

    print("Open 3D controls:")
    print("  1: RGB")
    print("  4: for point cloud colored by depth")
    print("  h: for all controls")
    visualizer.get_render_option().background_color = (0, 0, 0)
    visualizer.get_render_option().point_size = 2
    visualizer.get_render_option().show_coordinate_frame = True
    visualizer.get_view_control().set_front([0, 0, -1])
    visualizer.get_view_control().set_up([0, -1, 0])

    visualizer.run()
    visualizer.destroy_window()


def display_point_cloud_from_xyz_rgb(xyz: np.ndarray, rgb: np.ndarray) -> None:
    """Display point cloud provided from 'xyz' with colors from 'rgb'.

    Args:
        xyz: A numpy array of X, Y and Z point cloud coordinates
        rgb: RGB image
    """
    open3d_point_cloud = _copy_to_open3d_point_cloud(xyz, rgb)
    _display_open3d_point_cloud(open3d_point_cloud)


def _main() -> None:
    # Application class must be initialized before using other Zivid classes.
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    data_file = get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading ZDF frame from file: {data_file}")

    frame = zivid.Frame(data_file)
    point_cloud = frame.point_cloud()
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba_srgb")

    pixels_to_display = 300
    print(f"Generating binary mask of central {pixels_to_display} x {pixels_to_display} pixels")
    mask = np.zeros((rgba.shape[0], rgba.shape[1]), bool)
    height = frame.point_cloud().height
    width = frame.point_cloud().width

    h_min = int((height - pixels_to_display) / 2)
    h_max = int((height + pixels_to_display) / 2)
    w_min = int((width - pixels_to_display) / 2)
    w_max = int((width + pixels_to_display) / 2)
    mask[h_min:h_max, w_min:w_max] = 1

    display_rgb(rgba[:, :, 0:3], title="RGB image")

    display_depthmap(xyz)
    display_pointcloud(point_cloud)

    print("Masking point cloud")
    xyz_masked = xyz.copy()
    xyz_masked[mask == 0] = np.nan

    display_depthmap(xyz_masked)
    display_point_cloud_from_xyz_rgb(xyz_masked, rgba)


if __name__ == "__main__":
    _main()
