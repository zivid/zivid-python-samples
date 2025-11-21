"""
Display relevant data for Zivid Samples.

"""

from typing import List, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import zivid


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
    import cv2  # pylint: disable=import-outside-toplevel

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


def display_pointcloud(data: Union[zivid.Frame, zivid.PointCloud, zivid.UnorganizedPointCloud]) -> None:
    """Display point cloud provided either as Frame, PointCloud or UnorganizedPointCloud.

    Args:
        data: Union[zivid.Frame, zivid.PointCloud, zivid.UnorganizedPointCloud]
        normals: If True, display normals as color map

    """
    with zivid.visualization.Visualizer() as visualizer:
        visualizer.set_window_title("Zivid Point Cloud Visualizer")
        visualizer.colors_enabled = True
        visualizer.axis_indicator_enabled = True
        visualizer.show(data)
        visualizer.reset_to_fit()
        visualizer.run()
