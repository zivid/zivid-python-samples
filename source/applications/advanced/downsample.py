"""
Downsample point cloud from a ZDF file.

The ZDF files for this sample can be found under the main instructions for Zivid samples.

"""

import argparse
from pathlib import Path

import zivid
from zividsamples.display import display_pointcloud
from zividsamples.paths import get_sample_data_path


def _options() -> argparse.Namespace:
    """Function to read user arguments.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--zdf-path",
        required=False,
        type=Path,
        default=get_sample_data_path() / "Zivid3D.zdf",
        help="Path to the ZDF file",
    )

    return parser.parse_args()


def _main() -> None:
    # Application class must be initialized before using other Zivid classes.
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    user_options = _options()
    data_file = user_options.zdf_path

    print(f"Reading ZDF frame from file: {data_file}")
    frame = zivid.Frame(data_file)

    point_cloud = frame.point_cloud()
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba_sgrb")

    print(f"Before downsampling: {point_cloud.width * point_cloud.height} point cloud")

    display_pointcloud(xyz, rgba[:, :, 0:3])

    print("Downsampling point cloud")
    print("This does not modify the current point cloud but returns")
    print("the downsampled point cloud as a new point cloud instance.")
    downsampled_point_cloud = point_cloud.downsampled(zivid.PointCloud.Downsampling.by2x2)

    print(f"After downsampling: {downsampled_point_cloud.width * downsampled_point_cloud.height} point cloud")

    print("Downsampling point cloud (in-place)")
    print("This modifies the current point cloud.")
    point_cloud.downsample(zivid.PointCloud.Downsampling.by2x2)

    xyz_donwsampled = point_cloud.copy_data("xyz")
    rgba_downsampled = point_cloud.copy_data("rgba_srgb")

    print(f"After downsampling: {point_cloud.width * point_cloud.height} point cloud")

    display_pointcloud(xyz_donwsampled, rgba_downsampled[:, :, 0:3])


if __name__ == "__main__":
    _main()
