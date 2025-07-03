"""
Use transformation matrices from Multi-Camera calibration to transform point clouds into a single coordinate frame, from connected cameras.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.
"""

import argparse
import os
from pathlib import Path
from typing import Dict, List

import zivid
from zivid.experimental.point_cloud_export import export_unorganized_point_cloud
from zivid.experimental.point_cloud_export.file_format import PLY, ColorSpace
from zividsamples.display import copy_to_open3d_point_cloud, display_open3d_point_cloud
from zividsamples.paths import get_sample_data_path


def _user_arguments() -> argparse.Namespace:
    """Parse command line options for the script.

    Returns:
        Arguments from the user
    """
    parser = argparse.ArgumentParser(
        description="Stitch point clouds from multiple Zivid cameras using transformation matrices."
    )
    parser.add_argument(
        "yaml_files",
        type=Path,
        nargs="+",
        help="YAML files containing the corresponding transformation matrices (one per camera).",
    )
    parser.add_argument(
        "-o", "--output-file", type=Path, help="Save the stitched point cloud to a file with this name (.ply)"
    )
    return parser.parse_args()


def connect_to_all_available_cameras(cameras: List[zivid.Camera]) -> List[zivid.Camera]:
    connected_cameras = []
    for camera in cameras:
        if camera.state.status == zivid.CameraState.Status.available:
            print(f"Connecting to camera: {camera.info.serial_number}")
            camera.connect()
            connected_cameras.append(camera)
        else:
            print(f"Camera {camera.info.serial_number} is not available. " f"Camera status: {camera.state.status}")
    return connected_cameras


def get_transformation_matrices_from_yaml(
    file_list: List[Path], cameras: List[zivid.Camera]
) -> Dict[str, zivid.Matrix4x4]:
    """
    Reads transformation matrices from YAML files and maps them to the corresponding cameras.

    Args:
        file_list: List of YAML files containing transformation matrices
        cameras: List of connected Zivid cameras

    Returns:
        A dictionary mapping camera serial numbers to their corresponding transformation matrices

    Raises:
        RuntimeError: If a YAML file for a camera is missing
    """
    transforms_mapped_to_cameras = {}
    for camera in cameras:
        serial_number = str(camera.info.serial_number)
        found = False
        for file_name in file_list:
            base = os.path.splitext(os.path.basename(file_name))[0]
            if serial_number == base:
                transforms_mapped_to_cameras[serial_number] = zivid.Matrix4x4(file_name)
                found = True
                break
        if not found:
            raise RuntimeError(f"You are missing a YAML file named {serial_number}.yaml!")
    return transforms_mapped_to_cameras


def main() -> None:
    args = _user_arguments()

    app = zivid.Application()
    print("Finding cameras")
    cameras = app.cameras()
    print(f"Number of cameras found: {len(cameras)}")

    connected_cameras = connect_to_all_available_cameras(cameras)
    if len(connected_cameras) < 2:
        raise RuntimeError("At least two cameras need to be connected")
    print(f"Number of connected cameras: {len(connected_cameras)}")

    transforms_mapped_to_cameras = get_transformation_matrices_from_yaml(args.yaml_files, connected_cameras)

    # Capture from all cameras
    stitched_point_cloud = zivid.UnorganizedPointCloud()

    #  DOCTAG-START-CAPTURE-AND-STITCH-POINT-CLOUDS-PART1
    for camera in connected_cameras:
        settings_path = (
            get_sample_data_path()
            / "Settings"
            / f"{camera.info.model_name.replace('2+', 'Two_Plus').replace('2', 'Two').replace(' ', '_')}_ManufacturingSpecular.yml"
        )
        print(f"Imaging from camera: {camera.info.serial_number}")
        frame = camera.capture(zivid.Settings.load(settings_path))
        unorganized_point_cloud = frame.point_cloud().to_unorganized_point_cloud()
        transformation_matrix = transforms_mapped_to_cameras[camera.info.serial_number]
        transformed_unorganized_point_cloud = unorganized_point_cloud.transformed(transformation_matrix)
        stitched_point_cloud.extend(transformed_unorganized_point_cloud)

    print("Voxel-downsampling the stitched point cloud")
    final_point_cloud = stitched_point_cloud.voxel_downsampled(0.5, 1)

    print("Copying the stitched point cloud to Open3D")
    open3d_point_cloud = copy_to_open3d_point_cloud(
        final_point_cloud.copy_data("xyz"), final_point_cloud.copy_data("rgba_srgb")
    )

    print(f"Visualizing the stitched point cloud ({len(open3d_point_cloud.points)} data points)")
    display_open3d_point_cloud(open3d_point_cloud)

    if args.output_file:
        print(f"Saving {len(final_point_cloud.size())} data points to {args.output_file}")
        export_unorganized_point_cloud(
            final_point_cloud, PLY(args.output_file, layout=PLY.Layout.unordered, color_space=ColorSpace.srgb)
        )


if __name__ == "__main__":
    main()
