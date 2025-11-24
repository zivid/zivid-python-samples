"""
Capture Zivid point clouds, compute normals and convert to color map and display.

"""

import sys

import numpy as np
import zivid
from zividsamples.display import display_rgb

try:
    import open3d as o3d
except ImportError:
    print(
        "⚠️  Failed to import Open3D. It is installed via `pip install -r requirements.txt`, "
        f"however it might not be available for your Python version: {sys.version_info.major}.{sys.version_info.minor}. "
        "See https://pypi.org/project/open3d/ for supported versions."
    )
    sys.exit(1)


def _copy_to_open3d_point_cloud(xyz: np.ndarray, rgb: np.ndarray, normals: np.ndarray) -> o3d.geometry.PointCloud:
    """Copy point cloud data to Open3D PointCloud object.

    Args:
        xyz: A numpy array of X, Y and Z point cloud coordinates
        rgb: RGB image
        normals: Ordered array of normal vectors, mapped to xyz

    Returns:
        An Open3D PointCloud object
    """
    xyz = np.nan_to_num(xyz).reshape(-1, 3)
    normals = np.nan_to_num(normals).reshape(-1, 3)
    rgb = rgb.reshape(-1, rgb.shape[-1])[:, :3]

    open3d_point_cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
    open3d_point_cloud.colors = o3d.utility.Vector3dVector(rgb / 255)
    open3d_point_cloud.normals = o3d.utility.Vector3dVector(normals)

    return open3d_point_cloud


def _display_open3d_point_cloud(open3d_point_cloud: o3d.geometry.PointCloud) -> None:
    """Display Open3D PointCloud object.

    Args:
        open3d_point_cloud: Open3D PointCloud object to display
    """
    visualizer = o3d.visualization.Visualizer()  # pylint: disable=no-member
    visualizer.create_window()
    visualizer.add_geometry(open3d_point_cloud)

    if len(open3d_point_cloud.normals) > 0:
        print("Open 3D controls:")
        print("  n: for normals")
        print("  9: for point cloud colored by normals")
        print("  h: for all controls")
    visualizer.get_render_option().background_color = (0, 0, 0)
    visualizer.get_render_option().point_size = 2
    visualizer.get_render_option().show_coordinate_frame = True
    visualizer.get_view_control().set_front([0, 0, -1])
    visualizer.get_view_control().set_up([0, -1, 0])

    visualizer.run()
    visualizer.destroy_window()


def display_pointcloud_with_downsampled_normals(
    point_cloud: zivid.PointCloud,
    downsampling: zivid.PointCloud.Downsampling,
) -> None:
    """Display point cloud with downsampled normals.

    Args:
        point_cloud: A Zivid point cloud handle
        downsampling: A valid Zivid downsampling factor to apply to normals

    """
    point_cloud.downsample(downsampling)
    rgb = point_cloud.copy_data("rgba_srgb")[:, :, :3]
    xyz = point_cloud.copy_data("xyz")
    normals = point_cloud.copy_data("normals")

    open3d_point_cloud = _copy_to_open3d_point_cloud(xyz, rgb, normals)
    _display_open3d_point_cloud(open3d_point_cloud)


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings")
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    print("Capturing frame")
    frame = camera.capture_2d_3d(settings)
    point_cloud = frame.point_cloud()
    rgba = point_cloud.copy_data("rgba_srgb")
    normals = point_cloud.copy_data("normals")
    normals_colormap = 0.5 * (1 - normals)
    normals_colormap = np.nan_to_num(normals_colormap, nan=0.0, posinf=1.0, neginf=0.0)

    print("Visualizing normals in 2D")
    display_rgb(rgb=rgba[:, :, :3], title="RGB image", block=False)
    display_rgb(rgb=normals_colormap, title="Colormapped normals", block=True)

    print("Visualizing normals in 3D")
    display_pointcloud_with_downsampled_normals(point_cloud, zivid.PointCloud.Downsampling.by4x4)


if __name__ == "__main__":
    _main()
