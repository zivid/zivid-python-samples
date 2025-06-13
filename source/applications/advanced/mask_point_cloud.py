"""
Read point cloud data from a ZDF file, apply a binary mask, and visualize it.

The ZDF file for this sample can be found under the main instructions for Zivid samples.

"""

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
    display_pointcloud(xyz, rgba[:, :, 0:3])

    print("Masking point cloud")
    xyz_masked = xyz.copy()
    xyz_masked[mask == 0] = np.nan

    display_depthmap(xyz_masked)
    display_pointcloud(xyz_masked, rgba[:, :, 0:3])


if __name__ == "__main__":
    _main()
