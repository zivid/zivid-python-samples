"""
Read point cloud data from a ZDF file, apply a binary mask, and visualize it.

The ZDF file for this sample can be found under the main instructions for Zivid samples.

"""

import cv2
import numpy as np
import zivid
from zividsamples.display import display_depthmap, display_pointcloud, display_rgb
from zividsamples.paths import get_sample_data_path


def _main() -> None:
    # Application class must be initialized before using other Zivid classes.
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    data_file = get_sample_data_path() / "Zivid3D.zdf"
    print(f"Reading ZDF frame from file: {data_file}")

    frame = zivid.Frame(data_file)
    point_cloud = frame.point_cloud()
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba_srgb")

    display_rgb(rgba[:, :, 0:3], title="RGB image")

    display_depthmap(xyz)
    display_pointcloud(point_cloud)

    pixels_to_display = 300
    print(f"Generating binary mask of central {pixels_to_display} x {pixels_to_display} pixels")
    height = frame.point_cloud().height
    width = frame.point_cloud().width
    mask = np.ones((height, width), bool)

    h_min = (height - pixels_to_display) // 2
    h_max = (height + pixels_to_display) // 2
    w_min = (width - pixels_to_display) // 2
    w_max = (width + pixels_to_display) // 2
    mask[h_min:h_max, w_min:w_max] = 0

    print("Masking point cloud")
    point_cloud.mask(mask)

    xyz_masked = point_cloud.copy_data("xyz")
    display_depthmap(xyz_masked)
    display_pointcloud(point_cloud)

    opencv_mask = np.ones((height, width), dtype=np.uint8)
    center_x = width // 2
    center_y = height // 2
    radius = pixels_to_display
    cv2.circle(opencv_mask, (center_x, center_y), radius, 0, thickness=cv2.FILLED)

    point_cloud.mask(opencv_mask.astype(bool))

    display_pointcloud(point_cloud)


if __name__ == "__main__":
    _main()
