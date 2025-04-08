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
from pathlib import Path
from typing import List

import numpy as np
import open3d as o3d
import zivid
from zividsamples.save_load_matrix import load_and_assert_affine_matrix


def _filter_calibration_object_roi(frame: zivid.Frame, args: argparse.Namespace) -> np.ndarray:
    """Filters out the data outside the region of interest defined by the calibration_object centroid.

    Args:
        frame: Zivid frame
        args: Input arguments

    Raises:
        RuntimeError: If the calibration object is not detected

    Returns:
        xyz: A numpy array of X, Y and Z point cloud coordinates within the region of interest

    """

    xyz = frame.point_cloud().copy_data("xyz")

    if args.calibration_object == "checkerboard":
        # Finding Cartesian coordinates of the checkerboard center point
        detection_result = zivid.calibration.detect_calibration_board(frame)

        if not detection_result.valid():
            raise RuntimeError(f"Calibration board not detected! {detection_result.status_description()}")

        centroid = detection_result.centroid()
        # the longest distance from the checkerboard centroid to the calibration board corner is < 245 mm
        radius_threshold = 245
    else:
        # Finding Cartesian coordinates of the ArUco marker center point
        detection_result = zivid.calibration.detect_markers(frame, args.id, args.dictionary)
        pose = detection_result.detected_markers()[0].pose.to_matrix()
        translation = pose[:3, 3]
        centroid = translation.flatten()
        radius_threshold = args.size * np.sqrt(2) / 2

    radius = np.linalg.norm(centroid - xyz, axis=2)
    xyz[radius > radius_threshold] = np.nan

    return xyz


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


def _create_open3d_point_cloud(rgba: np.ndarray, xyz: np.ndarray) -> o3d.geometry.PointCloud:
    """Creates a point cloud in Open3D format from NumPy array.

    Args:
        xyz: A numpy array of X, Y and Z point cloud coordinates
        rgba: A numpy array of R, G and B point cloud pixels

    Returns:
        refined_point_cloud_open3d: Point cloud in Open3D format without Nans
        or non finite values

    """
    xyz = xyz.reshape(-1, 3)
    rgb = rgba[:, :, 0:3].reshape(-1, 3)

    point_cloud_open3d = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz.astype(np.float64)))
    point_cloud_open3d.colors = o3d.utility.Vector3dVector(rgb.astype(np.float64) / 255)

    refined_point_cloud_open3d = o3d.geometry.PointCloud.remove_non_finite_points(
        point_cloud_open3d, remove_nan=True, remove_infinite=True
    )

    return refined_point_cloud_open3d


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
    with zivid.Application():
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
            raise RuntimeError("The number of point clouds (ZDF files) and robot poses (YAML files) must be the same")

        if len(list_of_paths_to_hand_eye_dataset_robot_poses) == 0:
            raise RuntimeError("There are no robot poses (YAML files) in the data folder")

        if len(list_of_paths_to_hand_eye_dataset_point_clouds) == 0:
            raise RuntimeError("There are no point clouds (ZDF files) in the data folder")

        if len(list_of_paths_to_hand_eye_dataset_robot_poses) == len(list_of_paths_to_hand_eye_dataset_point_clouds):
            hand_eye_transform = load_and_assert_affine_matrix(path / "handEyeTransform.yaml")

            number_of_dataset_pairs = len(list_of_paths_to_hand_eye_dataset_point_clouds)

            list_of_open_3d_point_clouds = []
            for data_pair_id in range(number_of_dataset_pairs):
                # Updating the user about the process status through the terminal
                percentage = int(100 * data_pair_id / number_of_dataset_pairs)
                print(f"{data_pair_id} / {number_of_dataset_pairs} - {percentage:>3}%")

                # Reading point cloud from file
                frame = zivid.Frame(list_of_paths_to_hand_eye_dataset_point_clouds[data_pair_id])

                robot_pose = load_and_assert_affine_matrix(list_of_paths_to_hand_eye_dataset_robot_poses[data_pair_id])

                # Transforms point cloud to the robot end-effector frame
                if robot_camera_configuration.lower() == "eth":
                    inv_robot_pose = np.linalg.inv(robot_pose)
                    frame.point_cloud().transform(np.matmul(inv_robot_pose, hand_eye_transform))

                # Transforms point cloud to the robot base frame
                if robot_camera_configuration.lower() == "eih":
                    frame.point_cloud().transform(np.matmul(robot_pose, hand_eye_transform))

                # Extracting the points within the ROI (calibration object)
                xyz_filtered = _filter_calibration_object_roi(frame, args)

                # Converting from NumPy array to Open3D format
                point_cloud_open3d = _create_open3d_point_cloud(
                    frame.point_cloud().copy_data("rgba_srgb"), xyz_filtered
                )

                # Saving point cloud to PLY file
                o3d.io.write_point_cloud(f"img{data_pair_id + 1}.ply", point_cloud_open3d)

                # Appending the Open3D point cloud to a list for visualization
                list_of_open_3d_point_clouds.append(point_cloud_open3d)

        print(f"{number_of_dataset_pairs} / {number_of_dataset_pairs} - 100%")
        print("\nAll done!\n")

        if data_pair_id > 1:
            print("Visualizing transformed point clouds\n")
            o3d.visualization.draw_geometries(list_of_open_3d_point_clouds)
        else:
            raise RuntimeError("Not enough data!")


if __name__ == "__main__":
    _main()
