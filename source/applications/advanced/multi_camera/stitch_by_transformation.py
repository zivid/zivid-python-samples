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
from zividsamples.display import display_pointcloud
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
        "-o",
        "--output-file",
        required=False,
        type=Path,
        help="Save the stitched point cloud to a file with this name (.ply)",
    )

    parser.add_argument(
        "--settings-path",
        required=False,
        type=Path,
        help="Path to the camera settings YML file",
    )

    return parser.parse_args()


def sanitized_model_name(camera: zivid.Camera) -> str:
    """Get a string that represents the camera model name.

    Args:
        camera: Zivid camera

    Raises:
        RuntimeError: If unsupported camera model for this code sample

    Returns:
        A string representing the camera model name

    """
    model = camera.info.model

    model_map = {
        zivid.CameraInfo.Model.zividTwo: "Zivid_Two_M70",
        zivid.CameraInfo.Model.zividTwoL100: "Zivid_Two_L100",
        zivid.CameraInfo.Model.zivid2PlusM130: "Zivid_Two_Plus_M130",
        zivid.CameraInfo.Model.zivid2PlusM60: "Zivid_Two_Plus_M60",
        zivid.CameraInfo.Model.zivid2PlusL110: "Zivid_Two_Plus_L110",
        zivid.CameraInfo.Model.zivid2PlusMR130: "Zivid_Two_Plus_MR130",
        zivid.CameraInfo.Model.zivid2PlusMR60: "Zivid_Two_Plus_MR60",
        zivid.CameraInfo.Model.zivid2PlusLR110: "Zivid_Two_Plus_LR110",
        zivid.CameraInfo.Model.zivid3XL250: "Zivid_Three_XL250",
    }
    if model not in model_map:
        raise RuntimeError(f"Unhandled camera model: {camera.info().model().to_string()}")

    return model_map[model]


def connect_to_all_available_cameras(cameras: List[zivid.Camera]) -> List[zivid.Camera]:
    """get a list of available cameras and connect to them.

    Args:
        cameras: List of Zivid cameras

    Returns:
        List of connected Zivid cameras

    """
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
        transforms_mapped_to_cameras: A dictionary mapping camera serial numbers to their corresponding transformation matrices

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
        if args.settings_path is not None:
            settings_path = args.settings_path
        else:
            settings_path = (
                get_sample_data_path() / "Settings" / f"{sanitized_model_name(camera)}_ManufacturingSpecular.yml"
            )
        print(f"Imaging from camera: {camera.info.serial_number}")
        frame = camera.capture(zivid.Settings.load(settings_path))
        unorganized_point_cloud = frame.point_cloud().to_unorganized_point_cloud()
        transformation_matrix = transforms_mapped_to_cameras[camera.info.serial_number]
        transformed_unorganized_point_cloud = unorganized_point_cloud.transformed(transformation_matrix)
        stitched_point_cloud.extend(transformed_unorganized_point_cloud)

    print("Voxel-downsampling the stitched point cloud")
    final_point_cloud = stitched_point_cloud.voxel_downsampled(0.5, 1)

    print(f"Visualizing the stitched point cloud ({final_point_cloud.size} data points)")
    display_pointcloud(final_point_cloud)

    if args.output_file is not None:
        print(f"Saving {final_point_cloud.size} data points to {args.output_file}")
        export_unorganized_point_cloud(
            final_point_cloud, PLY(str(args.output_file), layout=PLY.Layout.unordered, color_space=ColorSpace.srgb)
        )


if __name__ == "__main__":
    main()
