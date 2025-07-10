"""
Display relevant data for Zivid Samples.

"""

from typing import List, Optional, Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
from zivid import PointCloud


def display_rgb(rgb: np.ndarray, title: str = "RGB image", block: bool = True) -> None:
    """Display RGB image.

    Args:
        rgb: RGB image (HxWx3 ndarray)
        title: Image title
        block: Stops the running program until the windows is closed

    """
    plt.figure()
    plt.imshow(rgb)
    plt.title(title)
    plt.show(block=block)


def display_rgbs(rgbs: List[np.ndarray], titles: List[str], layout: Tuple[int, int], block: bool = True) -> None:
    if layout[0] * layout[1] < len(rgbs):
        raise RuntimeError(
            f"Layout {layout} only has room for {layout[0] * layout[1]} images, while {len(rgbs)} was provided."
        )
    if len(titles) != len(rgbs):
        raise RuntimeError(f"Expected {len(titles)} titles, because {len(rgbs)} images were provided.")
    axs = plt.subplots(layout[0], layout[1], figsize=(layout[1] * 8, layout[0] * 6))[1]
    axs.resize(layout[0], layout[1])
    for row in range(layout[0]):
        for col in range(layout[1]):
            axs[row, col].imshow(rgbs[col + row * layout[1]])
            axs[row, col].title.set_text(titles[col + row * layout[1]])
    plt.tight_layout()
    plt.show(block=block)


def display_bgr(bgr: np.ndarray, title: str = "RGB image") -> None:
    """Display BGR image using OpenCV.

    Args:
        bgr: BGR image (HxWx3 ndarray)
        title: Name of the OpenCV window

    """
    cv2.imshow(title, bgr)
    print("Press any key to continue")
    cv2.waitKey(0)


def display_depthmap(xyz: np.ndarray, block: bool = True) -> None:
    """Create and display depthmap.

    Args:
        xyz: A numpy array of X, Y and Z point cloud coordinates
        block: Stops the running program until the windows is closed

    """
    plt.figure()
    plt.imshow(
        xyz[:, :, 2],
        vmin=np.nanmin(xyz[:, :, 2]),
        vmax=np.nanmax(xyz[:, :, 2]),
        cmap="viridis",
    )
    plt.colorbar()
    plt.title("Depth map")
    plt.show(block=block)


def copy_to_open3d_point_cloud(
    xyz: np.ndarray, rgb: np.ndarray, normals: Optional[np.ndarray] = None
) -> o3d.geometry.PointCloud:
    """Copy point cloud data to Open3D PointCloud object.

    Args:
        rgb: RGB image
        xyz: A numpy array of X, Y and Z point cloud coordinates
        normals: Ordered array of normal vectors, mapped to xyz

    Returns:
        An Open3D PointCloud
    """
    if len(np.shape(xyz)) == 3:
        xyz = np.nan_to_num(xyz).reshape(-1, 3)
    if normals is not None:
        normals = np.nan_to_num(normals).reshape(-1, 3)
    if len(np.shape(rgb)) == 3:
        rgb = rgb.reshape(-1, rgb.shape[-1])[:, :3]

    open3d_point_cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
    open3d_point_cloud.colors = o3d.utility.Vector3dVector(rgb / 255)
    if normals is not None:
        open3d_point_cloud.normals = o3d.utility.Vector3dVector(normals)

    return open3d_point_cloud


def display_open3d_point_cloud(open3d_point_cloud: o3d.geometry.PointCloud) -> None:
    """Display Open3D PointCloud object.

    Args:
        open3d_point_cloud
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


def display_pointcloud(xyz: np.ndarray, rgb: np.ndarray, normals: Optional[np.ndarray] = None) -> None:
    """Display point cloud provided from 'xyz' with colors from 'rgb'.

    Args:
        rgb: RGB image
        xyz: A numpy array of X, Y and Z point cloud coordinates
        normals: Ordered array of normal vectors, mapped to xyz

    """
    open3d_point_cloud = copy_to_open3d_point_cloud(xyz, rgb, normals)
    display_open3d_point_cloud(open3d_point_cloud)


def display_pointcloud_with_downsampled_normals(
    point_cloud: PointCloud,
    downsampling: PointCloud.Downsampling,
) -> None:
    """Display point cloud with downsampled normals.

    Args:
        point_cloud: A Zivid point cloud handle
        downsampling: A valid Zivid downsampling factor to apply to normals

    """
    rgb = point_cloud.copy_data("rgba_srgb")[:, :, :3]
    xyz = point_cloud.copy_data("xyz")
    point_cloud.downsample(downsampling)
    normals = point_cloud.copy_data("normals")

    display_pointcloud(xyz=xyz, rgb=rgb, normals=normals)
