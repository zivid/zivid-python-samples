"""
Read point cloud data of a Zivid calibration board from a ZDF file, estimate the
checkerboard pose and save the transformation matrix to a YAML file.

The checkerboard point cloud is also visualized with a coordinate system.
The ZDF file for this sample can be found under the main instructions for Zivid samples.

"""

from pathlib import Path

import numpy as np
import open3d as o3d
import zivid
from sample_utils.paths import get_sample_data_path
from sample_utils.save_load_matrix import assert_affine_matrix_and_save


def _create_open3d_point_cloud(point_cloud: zivid.PointCloud) -> o3d.geometry.PointCloud:
    """Create a point cloud in Open3D format from NumPy array.

    Args:
        point_cloud: Zivid point cloud

    Returns:
        refined_point_cloud_open3d: Point cloud in Open3D format without Nans or non finite values

    """
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba")

    xyz = np.nan_to_num(xyz).reshape(-1, 3)
    rgb = rgba[:, :, 0:3].reshape(-1, 3)

    point_cloud_open3d = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
    point_cloud_open3d.colors = o3d.utility.Vector3dVector(rgb / 255)

    refined_point_cloud_open3d = o3d.geometry.PointCloud.remove_non_finite_points(
        point_cloud_open3d, remove_nan=True, remove_infinite=True
    )
    return refined_point_cloud_open3d


def _visualize_checkerboard_point_cloud_with_coordinate_system(
    point_cloud_open3d: o3d.geometry.PointCloud,
    transform: np.ndarray,
) -> None:
    """Create a mesh of a coordinate system and visualize it with the point cloud
    of a checkerboard and the checkerboard coordinate system.

    Args:
        point_cloud_open3d: An Open3d point cloud of a checkerboard
        transform: Transformation matrix

    """
    coord_system_mesh = o3d.geometry.TriangleMesh.create_coordinate_frame(size=30)
    coord_system_mesh.transform(transform)

    visualizer = o3d.visualization.Visualizer()
    visualizer.create_window()
    visualizer.add_geometry(point_cloud_open3d)
    visualizer.add_geometry(coord_system_mesh)
    visualizer.run()
    visualizer.destroy_window()


def _main() -> None:

    with zivid.Application():

        data_file = get_sample_data_path() / "CalibrationBoardInCameraOrigin.zdf"
        print(f"Reading ZDF frame from file: {data_file}")
        frame = zivid.Frame(data_file)
        point_cloud = frame.point_cloud()

        print("Detecting checkerboard and estimating its pose in camera frame")
        transform_camera_to_checkerboard = zivid.calibration.detect_feature_points(point_cloud).pose().to_matrix()
        print(f"Camera pose in checkerboard frame:\n{transform_camera_to_checkerboard}")

        transform_file_name = "CameraToCheckerboardTransform.yaml"
        print(f"Saving detected checkerboard pose to YAML file: {transform_file_name}")
        transform_file_path = Path(__file__).parent / transform_file_name
        assert_affine_matrix_and_save(transform_camera_to_checkerboard, transform_file_path)

        print("Visualizing checkerboard with coordinate system")
        checkerboard_point_cloud = _create_open3d_point_cloud(point_cloud)
        _visualize_checkerboard_point_cloud_with_coordinate_system(
            checkerboard_point_cloud, transform_camera_to_checkerboard
        )


if __name__ == "__main__":
    _main()
