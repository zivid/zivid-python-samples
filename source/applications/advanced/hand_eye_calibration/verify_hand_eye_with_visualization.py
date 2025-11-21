"""
Verify hand-eye calibration by transforming all dataset point clouds and
visualizing them overlapped.

Running this sample requires the dataset (robot poses and point clouds)
and the output transformation matrix of the Hand-Eye calibration.

The transformation will be done to different robot frames, depending on
the type of calibration made. Options:
- eye-to-hand: The point clouds are transformed to the robot end-effector frame
- eye-in-hand: The point clouds are transformed to the robot base frame

The Hand-Eye calibration is good if the visualized calibration objects overlap
accurately.

Tip: This sample saves the point clouds in PLY format in the same
directory where this sample is stored. You can open the PLY point clouds
in MeshLab for visual inspection.

"""

import argparse
import colorsys
from pathlib import Path
from typing import List

import numpy as np
import zivid
from zivid.experimental.point_cloud_export import export_unorganized_point_cloud
from zivid.experimental.point_cloud_export.file_format import PLY, ColorSpace
from zividsamples.display import display_pointcloud
from zividsamples.save_load_matrix import load_and_assert_affine_matrix


def _distinct_colors(number_of_colors: int) -> List[List[int]]:
    """Generate n visually distinct RGB colors.

    Args:
        number_of_colors: Number of distinct colors to generate

    Returns:
        List of distinct RGB colors

    """

    return [
        [round(c * 255) for c in colorsys.hsv_to_rgb(i / number_of_colors, 0.75, 0.9)] for i in range(number_of_colors)
    ]


def _options() -> argparse.Namespace:
    """Function for taking in arguments from user.

    Returns:
        Argument from user

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-path",
        type=Path,
        required=True,
        help="Path to the Hand-Eye dataset",
    )

    subparsers = parser.add_subparsers(dest="calibration_object", required=True, help="Calibration object type")
    subparsers.add_parser("checkerboard", help="Verify using Zivid calibration board")
    marker_parser = subparsers.add_parser("marker", help="Verify using ArUco marker")
    marker_parser.add_argument(
        "--dictionary",
        required=True,
        choices=list(zivid.calibration.MarkerDictionary.valid_values()),
        help="Dictionary of the targeted ArUco marker",
    )
    marker_parser.add_argument(
        "--id", nargs=1, required=True, type=int, help="ID of ArUco marker to be used for verification"
    )
    marker_parser.add_argument("--size", required=True, type=float, help="ArUco marker size in mm")

    return parser.parse_args()


def _path_list_creator(
    path: Path,
    file_prefix_name: str,
    number_of_digits_zfill: int,
    file_suffix_name: str,
) -> List[Path]:
    """Creates a list of paths where the files have a predefined prefix,
        an incremental number and a predefined suffix on their name,
        respectively. Eg.: img01.zdf

    Args:
        path: A path that leads to the files directory
        file_prefix_name: A string that comes before the number
        number_of_digits_zfill: A number of digits in the number
        file_suffix_name: A string that comes after the number

    Returns:
        list_of_paths: List of appended paths

    """
    num = 1
    list_of_paths = []

    while True:
        file_path = path / f"{file_prefix_name}{str(num).zfill(number_of_digits_zfill)}{file_suffix_name}"
        list_of_paths.append(file_path)

        next_file_path = path / f"{file_prefix_name}{str(num + 1).zfill(number_of_digits_zfill)}{file_suffix_name}"

        if not next_file_path.exists():
            return list_of_paths

        num = num + 1


def _main() -> None:
    # Application class must be initialized before using other Zivid classes.
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    args = _options()

    while True:
        robot_camera_configuration = input(
            "Enter type of calibration, eth (for eye-to-hand) or eih (for eye-in-hand):"
        ).strip()
        if robot_camera_configuration.lower() == "eth" or robot_camera_configuration.lower() == "eih":
            break
        print("Entered unknown Hand-Eye calibration type")

    path = args.input_path
    list_of_paths_to_hand_eye_dataset_point_clouds = _path_list_creator(path, "img", 2, ".zdf")
    list_of_paths_to_hand_eye_dataset_robot_poses = _path_list_creator(path, "pos", 2, ".yaml")

    if len(list_of_paths_to_hand_eye_dataset_robot_poses) != len(list_of_paths_to_hand_eye_dataset_point_clouds):
        raise RuntimeError(
            f"The number of point clouds (ZDF files - {len(list_of_paths_to_hand_eye_dataset_point_clouds)}) and robot poses (YAML files - {len(list_of_paths_to_hand_eye_dataset_robot_poses)}) must be the same"
        )

    if len(list_of_paths_to_hand_eye_dataset_robot_poses) == 0:
        raise RuntimeError("There are no robot poses (YAML files) in the data folder")

    if len(list_of_paths_to_hand_eye_dataset_point_clouds) == 0:
        raise RuntimeError("There are no point clouds (ZDF files) in the data folder")

    if len(list_of_paths_to_hand_eye_dataset_robot_poses) == len(list_of_paths_to_hand_eye_dataset_point_clouds):
        hand_eye_transform = load_and_assert_affine_matrix(path / "handEyeTransform.yaml")

        number_of_dataset_pairs = len(list_of_paths_to_hand_eye_dataset_point_clouds)

        stitched_point_cloud = zivid.UnorganizedPointCloud()
        for data_pair_id, rgb_color in zip(
            range(number_of_dataset_pairs), _distinct_colors(number_of_dataset_pairs), strict=False
        ):
            # Updating the user about the process status through the terminal
            percentage = int(100 * data_pair_id / number_of_dataset_pairs)
            print(f"{data_pair_id} / {number_of_dataset_pairs} - {percentage:>3}%")

            # Reading point cloud from file
            frame = zivid.Frame(list_of_paths_to_hand_eye_dataset_point_clouds[data_pair_id])

            robot_pose = load_and_assert_affine_matrix(list_of_paths_to_hand_eye_dataset_robot_poses[data_pair_id])

            point_cloud = frame.point_cloud()

            # Transforms point cloud to the robot end-effector frame
            if robot_camera_configuration.lower() == "eth":
                inv_robot_pose = np.linalg.inv(robot_pose)
                point_cloud.transform(np.matmul(inv_robot_pose, hand_eye_transform))

            # Transforms point cloud to the robot base frame
            if robot_camera_configuration.lower() == "eih":
                point_cloud.transform(np.matmul(robot_pose, hand_eye_transform))

            transformed_point_cloud = point_cloud.to_unorganized_point_cloud()

            # Saving point cloud to PLY file
            export_unorganized_point_cloud(
                transformed_point_cloud,
                PLY(f"img{data_pair_id + 1}.ply", layout=PLY.Layout.unordered, color_space=ColorSpace.srgb),
            )

            # Setting monochrome color and adding to stitched point cloud
            transformed_point_cloud.paint_uniform_color(rgb_color + [128])
            stitched_point_cloud.extend(transformed_point_cloud)

    print(f"{number_of_dataset_pairs} / {number_of_dataset_pairs} - 100%")
    print("\nAll done!\n")

    if number_of_dataset_pairs > 1:
        print("Visualizing transformed point clouds\n")
        display_pointcloud(stitched_point_cloud)
    else:
        raise RuntimeError("Not enough data!")


if __name__ == "__main__":
    _main()
