"""
Verify hand-eye calibration by transforming all dataset point clouds and
visualizing them overlapped.

Running this sample requires the dataset (robot poses and point clouds)
and the output transformation matrix of the Hand-Eye calibration.

The transformation will be done to different robot frames, depending on
the type of calibration made. Options:
- eye-to-hand: The point clouds are transformed to the robot end-effector frame
- eye-in-hand: The point clouds are transformed to the robot base frame

The Hand-Eye calibration is good if the visualized checkerboards overlap
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
from sample_utils.save_load_matrix import load_and_assert_affine_matrix


def _filter_checkerboard_roi(xyz: np.ndarray, centroid: np.ndarray) -> np.ndarray:
    """Filters out the data outside the region of interest defined by the checkerboard centroid.

    Args:
        xyz: A numpy array of X, Y and Z point cloud coordinates
        centroid: A numpy array of X, Y and Z checkerboard centroid coordinates

    Returns:
        xyz: A numpy array of X, Y and Z point cloud coordinates within the region of interest

    """
    # the longest distance from the checkerboard centroid to the calibration board corner is < 245 mm
    radius_threshold = 245
    radius = np.linalg.norm(centroid - xyz, axis=2)
    xyz[radius > radius_threshold] = np.NaN

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

    point_cloud_open3d = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
    point_cloud_open3d.colors = o3d.utility.Vector3dVector(rgb / 255)

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

        next_file_path = path / f"{file_prefix_name}{str(num+1).zfill(number_of_digits_zfill)}{file_suffix_name}"

        if not next_file_path.exists():
            return list_of_paths

        num = num + 1


def _main() -> None:

    with zivid.Application():

        while True:
            robot_camera_configuration = input(
                "Enter type of calibration, eth (for eye-to-hand) or eih (for eye-in-hand):"
            ).strip()
            if robot_camera_configuration.lower() == "eth" or robot_camera_configuration.lower() == "eih":
                break
            print("Entered unknown Hand-Eye calibration type")

        args = _options()
        path = args.input_path

        list_of_paths_to_hand_eye_dataset_point_clouds = _path_list_creator(path, "img", 2, ".zdf")

        list_of_paths_to_hand_eye_dataset_robot_poses = _path_list_creator(path, "pos", 2, ".yaml")

        if len(list_of_paths_to_hand_eye_dataset_robot_poses) != len(list_of_paths_to_hand_eye_dataset_point_clouds):
            raise Exception("The number of point clouds (ZDF iles) and robot poses (YAML files) must be the same")

        if len(list_of_paths_to_hand_eye_dataset_robot_poses) == 0:
            raise Exception("There are no robot poses (YAML files) in the data folder")

        if len(list_of_paths_to_hand_eye_dataset_point_clouds) == 0:
            raise Exception("There are no point clouds (ZDF files) in the data folder")

        if len(list_of_paths_to_hand_eye_dataset_robot_poses) == len(list_of_paths_to_hand_eye_dataset_point_clouds):

            hand_eye_transform = load_and_assert_affine_matrix(path / "handEyeTransform.yaml")

            number_of_dataset_pairs = len(list_of_paths_to_hand_eye_dataset_point_clouds)

            list_of_open_3d_point_clouds = []
            for data_pair_id in range(number_of_dataset_pairs):

                # Updating the user about the process status through the terminal
                print(f"{data_pair_id} / {number_of_dataset_pairs} - {100*data_pair_id / number_of_dataset_pairs}%")

                # Reading point cloud from file
                point_cloud = zivid.Frame(list_of_paths_to_hand_eye_dataset_point_clouds[data_pair_id]).point_cloud()

                robot_pose = load_and_assert_affine_matrix(list_of_paths_to_hand_eye_dataset_robot_poses[data_pair_id])

                # Transforms point cloud to the robot end-effector frame
                if robot_camera_configuration.lower() == "eth":
                    inv_robot_pose = np.linalg.inv(robot_pose)
                    point_cloud_transformed = point_cloud.transform(np.matmul(inv_robot_pose, hand_eye_transform))

                # Transforms point cloud to the robot base frame
                if robot_camera_configuration.lower() == "eih":
                    point_cloud_transformed = point_cloud.transform(np.matmul(robot_pose, hand_eye_transform))

                xyz = point_cloud_transformed.copy_data("xyz")
                rgba = point_cloud_transformed.copy_data("rgba")

                # Finding Cartesian coordinates of the checkerboard center point
                detection_result = zivid.calibration.detect_feature_points(point_cloud_transformed)

                if detection_result.valid():
                    # Extracting the points within the ROI (checkerboard)
                    xyz_filtered = _filter_checkerboard_roi(xyz, detection_result.centroid())

                    # Converting from NumPy array to Open3D format
                    point_cloud_open3d = _create_open3d_point_cloud(rgba, xyz_filtered)

                    # Saving point cloud to PLY file
                    o3d.io.write_point_cloud(f"img{data_pair_id + 1}.ply", point_cloud_open3d)

                    # Appending the Open3D point cloud to a list for visualization
                    list_of_open_3d_point_clouds.append(point_cloud_open3d)

        print(f"{number_of_dataset_pairs} / {number_of_dataset_pairs} - 100.0%")
        print("\nAll done!\n")

        if data_pair_id > 1:
            print("Visualizing transformed point clouds\n")
            o3d.visualization.draw_geometries(list_of_open_3d_point_clouds)
        else:
            raise Exception("Not enought data!")


if __name__ == "__main__":
    _main()
