"""
Stitch point clouds from a continuously rotating object without pre-alignment using Local Point Cloud Registration and apply Voxel Downsample.

It is assumed that the object is rotating around its own axis and the camera is stationary.
The camera settings should have defined a region of interest box that removes unnecessary points, keeping only the object to be stitched.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

import argparse
import time
from pathlib import Path

import numpy as np
import zivid
from zivid.experimental.point_cloud_export import export_unorganized_point_cloud
from zivid.experimental.point_cloud_export.file_format import PLY
from zivid.experimental.toolbox.point_cloud_registration import (
    LocalPointCloudRegistrationParameters,
    local_point_cloud_registration,
)
from zividsamples.display import display_pointcloud


def _options() -> argparse.Namespace:
    """Function to read user arguments.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--settings-path",
        required=True,
        type=Path,
        help="Path to the camera settings YML file",
    )

    return parser.parse_args()


def _main() -> None:
    user_options = _options()

    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    settings_file = Path(user_options.settings_path)
    print(f"Loading settings from file: {settings_file}")
    settings = zivid.Settings.load(settings_file)

    previous_to_current_point_cloud_transform = np.eye(4)
    unorganized_stitched_point_cloud = zivid.UnorganizedPointCloud()
    registration_params = LocalPointCloudRegistrationParameters()

    for number_of_captures in range(20):
        time.sleep(1)
        frame = camera.capture_2d_3d(settings)
        unorganized_point_cloud = (
            frame.point_cloud().to_unorganized_point_cloud().voxel_downsampled(voxel_size=1.0, min_points_per_voxel=2)
        )

        if number_of_captures != 0:
            local_point_cloud_registration_result = local_point_cloud_registration(
                target=unorganized_stitched_point_cloud,
                source=unorganized_point_cloud,
                parameters=registration_params,
                initial_transform=previous_to_current_point_cloud_transform,
            )
            if not local_point_cloud_registration_result.converged():
                print("Registration did not converge...")
                continue
            previous_to_current_point_cloud_transform = local_point_cloud_registration_result.transform().to_matrix()

            unorganized_stitched_point_cloud.transform(np.linalg.inv(previous_to_current_point_cloud_transform))
        unorganized_stitched_point_cloud.extend(unorganized_point_cloud)

        print(f"Captures done: {number_of_captures}")

    print("Voxel-downsampling the stitched point cloud")
    unorganized_stitched_point_cloud = unorganized_stitched_point_cloud.voxel_downsampled(
        voxel_size=0.75, min_points_per_voxel=2
    )

    display_pointcloud(
        xyz=unorganized_stitched_point_cloud.copy_data("xyz"),
        rgb=unorganized_stitched_point_cloud.copy_data("rgba")[:, 0:3],
    )

    file_name = Path(__file__).parent / "StitchedPointCloudOfRotatingObject.ply"
    export_unorganized_point_cloud(unorganized_stitched_point_cloud, PLY(str(file_name), layout=PLY.Layout.unordered))


if __name__ == "__main__":
    _main()
