"""
Use transformation matrices from Multi-Camera calibration to transform point clouds into single coordinate frame, from a ZDF files.
"""

import argparse
from pathlib import Path
from typing import List

import zivid
from zivid.experimental.point_cloud_export import export_unorganized_point_cloud
from zivid.experimental.point_cloud_export.file_format import PLY, ColorSpace
from zividsamples.display import copy_to_open3d_point_cloud, display_open3d_point_cloud


def _user_arguments() -> argparse.Namespace:
    """Parse command line options for the script.

    Returns:
        Arguments from the user
    """
    parser = argparse.ArgumentParser(
        description="Stitch point clouds from multiple ZDF files using transformation matrices from YAML files."
    )
    parser.add_argument("-zdf", nargs="+", required=True, help="List of ZDF files to stitch.", type=Path)
    parser.add_argument(
        "-yaml",
        nargs="+",
        required=True,
        help="List of YAML files containing the corresponding transformation matrices.",
        type=Path,
    )
    parser.add_argument(
        "-o", "--output-file", type=Path, help="Save the stitched point cloud to a file with this name (.ply)."
    )
    return parser.parse_args()


def get_transformed_point_clouds(
    zdf_file_list: List[Path],
    transformation_matrix_files_list: List[Path],
) -> zivid.UnorganizedPointCloud:
    """
    Loads ZDF frames and corresponding transformation matrices, applies the transformations,
    and returns a stitched Zivid UnorganizedPointCloud.

    Args:
        zdf_file_list: List of ZDF files containing point clouds.
        transformation_matrix_files_list: List of YAML files containing transformation matrices.

    Returns:
        A stitched UnorganizedPointCloud containing all transformed point clouds.

    Raises:
        RuntimeError: If a YAML file for a camera is missing or if fewer than two point clouds are provided.
    """
    stitched_point_cloud = zivid.UnorganizedPointCloud()
    number_of_point_clouds = 0

    # Building a mapping from serial number to transformation matrix file
    serial_to_yaml = {}
    for yaml_file in transformation_matrix_files_list:
        serial_number = yaml_file.stem
        serial_to_yaml[serial_number] = yaml_file

    for zdf_file in zdf_file_list:
        frame = zivid.Frame(zdf_file)
        serial_number = frame.camera_info.serial_number
        print(f"Searching in {zdf_file}")

        yaml_file = serial_to_yaml.get(serial_number)
        if not yaml_file:
            raise RuntimeError(f"You are missing a YAML file named {serial_number}.yaml!")

        transformation_matrix = zivid.Matrix4x4(yaml_file)
        current_point_cloud = frame.point_cloud().to_unorganized_point_cloud()
        stitched_point_cloud.extend(current_point_cloud.transform(transformation_matrix))
        number_of_point_clouds += 1

    if number_of_point_clouds < 2:
        raise RuntimeError(f"Require minimum two matching transformation and frames, got {number_of_point_clouds}")

    return stitched_point_cloud


def main() -> None:
    args = _user_arguments()

    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    stitched_point_cloud = get_transformed_point_clouds(args.zdf, args.yaml)

    print("Voxel-downsampling the stitched point cloud")
    final_point_cloud = stitched_point_cloud.voxel_downsampled(0.5, 1)

    print("Copying the stitched point cloud to Open3D")
    open3d_point_cloud = copy_to_open3d_point_cloud(
        final_point_cloud.copy_data("xyz"), final_point_cloud.copy_data("rgba_srgb")
    )

    print(f"Visualizing the stitched point cloud ({len(open3d_point_cloud.points)} data points)")
    display_open3d_point_cloud(open3d_point_cloud)

    if args.output_file:
        print(f"Saving {final_point_cloud.size} data points to {args.output_file}")
        export_unorganized_point_cloud(
            final_point_cloud,
            PLY(str(args.output_file.resolve()), layout=PLY.Layout.unordered, color_space=ColorSpace.srgb),
        )


if __name__ == "__main__":
    main()
