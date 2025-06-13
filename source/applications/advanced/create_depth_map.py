"""
Read point cloud data from a ZDF file, convert it to OpenCV format, then extract and visualize depth map.

The ZDF files for this sample can be found under the main instructions for Zivid samples.

"""

import cv2
import numpy as np
import zivid
from zividsamples.display import display_bgr
from zividsamples.paths import get_sample_data_path


def _point_cloud_to_cv_z(point_cloud: zivid.PointCloud) -> np.ndarray:
    """Get depth map from frame.

    Args:
        point_cloud: Zivid point cloud

    Returns:
        depth_map_color_map: Depth map (HxWx1 ndarray)

    """
    depth_map = point_cloud.copy_data("z")
    depth_map_uint8 = ((depth_map - np.nanmin(depth_map)) / (np.nanmax(depth_map) - np.nanmin(depth_map)) * 255).astype(
        np.uint8
    )

    depth_map_color_map = cv2.applyColorMap(depth_map_uint8, cv2.COLORMAP_VIRIDIS)

    # Setting nans to black
    depth_map_color_map[np.isnan(depth_map)[:, :]] = 0

    return depth_map_color_map


def _point_cloud_to_cv_bgr(point_cloud: zivid.PointCloud) -> np.ndarray:
    """Get bgr image from frame.

    Args:
        point_cloud: Zivid point cloud

    Returns:
        bgr: BGR image (HxWx3 ndarray)

    """
    bgra = point_cloud.copy_data("bgra_srgb")

    return bgra[:, :, :3]


def _visualize_and_save_image(image: np.ndarray, image_file: str, title: str) -> None:
    """Visualize and save image to file.

    Args:
        image: BGR image (HxWx3 ndarray)
        image_file: File name
        title: OpenCV Window name

    """
    display_bgr(image, title)
    cv2.imwrite(image_file, image)


def _main() -> None:
    # Application class must be initialized before using other Zivid classes.
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    data_file = get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading ZDF frame from file: {data_file}")

    frame = zivid.Frame(data_file)
    point_cloud = frame.point_cloud()

    print("Converting to BGR image in OpenCV format")
    bgr = _point_cloud_to_cv_bgr(point_cloud)

    bgr_image_file = "ImageRGB.png"
    print(f"Visualizing and saving BGR image to file: {bgr_image_file}")
    _visualize_and_save_image(bgr, bgr_image_file, "BGR image")

    print("Converting to Depth map in OpenCV format")
    z_color_map = _point_cloud_to_cv_z(point_cloud)

    depth_map_file = "DepthMap.png"
    print(f"Visualizing and saving Depth map to file: {depth_map_file}")
    _visualize_and_save_image(z_color_map, depth_map_file, "Depth map")


if __name__ == "__main__":
    _main()
