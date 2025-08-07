"""
Stitch multiple point clouds captured with a robot mounted camera.

The sample simulates a camera capturing the point clouds at different robot poses.
The point clouds are pre-aligned using the robot's pose and a hand-eye calibration transform.
The resulting stitched point cloud is displayed and saved to a PLY file.

The sample demonstrates stitching of a small and a big object.
The small object fits within the camera's field of view and the result of stitching is a full
point cloud of the object, seen from different angles, i.e, from the front, back, left, and right sides.
The big object does not fit within the camera's field of view, so the stitching is done to extend the
field of view of the camera, and see the object in full.

The resulting stitched point cloud is voxel downsampled if the `--full-resolution` flag is not set.

Dataset: https://support.zivid.com/en/latest/api-reference/samples/sample-data.html

Extract the content into :
    • Windows:   %ProgramData%\\Zivid\\StitchingPointClouds\\
    • Linux:     /usr/share/Zivid/data/StitchingPointClouds/

    StitchingPointClouds/
    ├── SmallObject/
    └── BigObject/

Each of these folders must contain ZDF captures, robot poses, and a hand-eye transform file.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

import argparse
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
from zividsamples.paths import get_sample_data_path
from zividsamples.save_load_matrix import load_and_assert_affine_matrix


def _options() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-resolution",
        action="store_true",
        help="Use full resolution for stitching. If not set, downsampling is applied.",
    )

    return parser.parse_args()


def _stitch_point_clouds(directory: Path, full_resolution: bool) -> zivid.UnorganizedPointCloud:
    """Stitch multiple point clouds captured at different robot poses.

    Args:
        directory (Path): Path to directory containing point clouds in ZDF and robot poses and a hand-eye transform in YML format.
        full_resolution (bool): If True, use full resolution (no downsampling). Otherwise, voxel downsample.

    Returns:
        zivid.UnorganizedPointCloud: The stitched point cloud.

    Raises:
        FileNotFoundError: If required files (ZDFs, robot poses, or hand-eye calibration) are missing in the directory.
        ValueError: If the number of ZDF files and robot pose files do not match.

    """
    zdf_files = list(directory.rglob("capture_*.zdf"))
    pose_files = list(directory.rglob("robot_pose_*.yaml"))

    if not zdf_files or not pose_files or not (directory / "hand_eye_transform.yaml").exists():
        raise FileNotFoundError("Required files are missing in the directory.")

    if len(zdf_files) != len(pose_files):
        raise ValueError("Number of ZDF files and robot pose files do not match.")

    hand_eye_transform = load_and_assert_affine_matrix(directory / "hand_eye_transform.yaml")

    stitched_point_clouds_to_current_point_cloud_transform = np.eye(4)
    unorganized_stitched_point_cloud_bucket = zivid.UnorganizedPointCloud()
    registration_params = LocalPointCloudRegistrationParameters(max_correspondence_distance=2)

    list_of_transforms = []
    stitched_count = 1

    for index, zdf in enumerate(zdf_files):
        robot_pose = load_and_assert_affine_matrix(pose_files[index])
        frame = zivid.Frame(zdf)

        base_to_camera_transform = np.matmul(robot_pose, hand_eye_transform)
        unorganized_point_cloud_in_base_frame = (
            frame.point_cloud()
            .to_unorganized_point_cloud()
            .voxel_downsampled(voxel_size=1.0, min_points_per_voxel=2)
            .transformed(base_to_camera_transform)
        )

        if index != 0:
            local_point_cloud_registration_result = local_point_cloud_registration(
                target=unorganized_stitched_point_cloud_bucket,
                source=unorganized_point_cloud_in_base_frame,
                parameters=registration_params,
            )

            # Aligning the new point cloud to the existing stitched result using local point cloud registration
            if not local_point_cloud_registration_result.converged():
                print("Registration did not converge...")
                continue
            stitched_point_clouds_to_current_point_cloud_transform = (
                local_point_cloud_registration_result.transform().to_matrix()
            )
            unorganized_stitched_point_cloud_bucket.transform(
                np.linalg.inv(stitched_point_clouds_to_current_point_cloud_transform)
            )
            stitched_count += 1

            if full_resolution:
                print(f"{stitched_count} out of {len(zdf_files)} Point clouds aligned.")
            else:
                print(f"{stitched_count} out of {len(zdf_files)} Point clouds stitched.")

        list_of_transforms.append((base_to_camera_transform, stitched_point_clouds_to_current_point_cloud_transform))

        unorganized_stitched_point_cloud_bucket.extend(unorganized_point_cloud_in_base_frame)

    final_point_cloud = zivid.UnorganizedPointCloud()

    if full_resolution:
        for index, transform in enumerate(list_of_transforms):
            frame = zivid.Frame(zdf_files[index])
            frame.point_cloud().transform(transform[0])
            final_point_cloud.transform(np.linalg.inv(transform[1]))
            final_point_cloud.extend(frame.point_cloud().to_unorganized_point_cloud())

            if index > 0:
                print(f"{index + 1} out of {len(list_of_transforms)} point clouds stitched.")
    else:
        # Downsampling the final result for efficiency
        final_point_cloud = unorganized_stitched_point_cloud_bucket.voxel_downsampled(
            voxel_size=1.0, min_points_per_voxel=2
        )

    return final_point_cloud


def _main() -> None:
    args = _options()
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    # Ensure the dataset is extracted to the correct location depending on the operating system:
    #   • Windows:   %ProgramData%\\Zivid\\StitchingPointClouds\\
    #   • Linux:     /usr/share/Zivid/data/StitchingPointClouds/
    #   StitchingPointClouds/
    #     ├── SmallObject/
    #     └── BigObject/
    # Each folder must include:
    #   - capture_*.zdf
    #   - robot_pose_*.yaml
    #   - hand_eye_transform.yaml
    small_object_dir = get_sample_data_path() / "StitchingPointClouds" / "SmallObject"
    big_object_dir = get_sample_data_path() / "StitchingPointClouds" / "BigObject"

    if not small_object_dir.exists() or not big_object_dir.exists():
        raise FileNotFoundError(
            f"Missing dataset folders.\n"
            f"Make sure 'StitchingPointClouds/SmallObject' and 'StitchingPointClouds/BigObject' exist at {get_sample_data_path()}.\n\n"
            f"You can download the dataset (StitchingPointClouds.zip) from:\n"
            f"https://support.zivid.com/en/latest/api-reference/samples/sample-data.html"
        )

    print("Stitching small object...")
    final_point_cloud_small = _stitch_point_clouds(small_object_dir, args.full_resolution)
    display_pointcloud(
        xyz=final_point_cloud_small.copy_data("xyz"),
        rgb=final_point_cloud_small.copy_data("rgba_srgb")[:, 0:3],
    )
    file_name_small = Path(__file__).parent / "StitchedPointCloudSmallObject.ply"
    export_unorganized_point_cloud(final_point_cloud_small, PLY(str(file_name_small), layout=PLY.Layout.unordered))

    print("Stitching big  object...")
    final_point_cloud_big = _stitch_point_clouds(big_object_dir, args.full_resolution)
    display_pointcloud(
        xyz=final_point_cloud_big.copy_data("xyz"),
        rgb=final_point_cloud_big.copy_data("rgba_srgb")[:, 0:3],
    )
    file_name_big = Path(__file__).parent / "StitchedPointCloudBigObject.ply"
    export_unorganized_point_cloud(final_point_cloud_big, PLY(str(file_name_big), layout=PLY.Layout.unordered))


if __name__ == "__main__":
    _main()
