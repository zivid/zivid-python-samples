"""
Display relevant data for Zivid Samples.
"""

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
from zivid import PointCloud


def display_rgb(rgb, title="RGB image"):
    """Display RGB image.

    Args:
        rgb: RGB image (HxWx3 darray)
        title: Image title

    Returns None

    """
    plt.figure()
    plt.imshow(rgb)
    plt.title(title)
    plt.show(block=False)




def display_depthmap(xyz):
    """Create and display depthmap.

    Args:
        xyz: X, Y and Z images (point cloud co-ordinates)

    Returns None

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
    plt.show(block=False)




def display_pointcloud(xyz, rgb, normals=None):
    """Display point cloud provided from 'xyz' with colors from 'rgb'.

    Args:
        rgb: RGB image
        xyz: X, Y and Z images (point cloud co-ordinates)
        normals: ordered array of normal vectors, mapped to xyz

    Returns None

    """
    xyz = np.nan_to_num(xyz).reshape(-1, 3)
    if normals is not None:
        normals = np.nan_to_num(normals).reshape(-1, 3)
    rgb = rgb.reshape(-1, 3)

    point_cloud_open3d = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
    point_cloud_open3d.colors = o3d.utility.Vector3dVector(rgb / 255)
    if normals is not None:
        point_cloud_open3d.normals = o3d.utility.Vector3dVector(normals)
        print("Open 3D controls:")
        print("  n: for normals")
        print("  9: for point cloud colored by normals")
        print("  h: for all controls")

    visualizer = o3d.visualization.Visualizer()  # pylint: disable=no-member
    visualizer.create_window()
    visualizer.add_geometry(point_cloud_open3d)

    if normals is None:
        visualizer.get_render_option().background_color = (0, 0, 0)
    visualizer.get_render_option().point_size = 1
    visualizer.get_render_option().show_coordinate_frame = True
    visualizer.get_view_control().set_front([0, 0, -1])
    visualizer.get_view_control().set_up([0, -1, 0])

    visualizer.run()
    visualizer.destroy_window()




def display_pointcloud_with_downsampled_normals(point_cloud: PointCloud, downsampling: PointCloud.Downsampling):
    """Display point cloud with downsampled normals

    Args:
        point_cloud: a Zivid point cloud handle
        downsampling: a valid Zivid downsampling factor to apply to normals

    Returns None

    """
    rgb = point_cloud.copy_data("rgba")[:, :, :3]
    xyz = point_cloud.copy_data("xyz")
    point_cloud.downsample(downsampling)
    normals = point_cloud.copy_data("normals")

    display_pointcloud(xyz=xyz, rgb=rgb, normals=normals)


