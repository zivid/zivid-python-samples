"""
Filter the point cloud based on a ROI box given relative to the Zivid Calibration Board.

The ZDF file for this sample can be found under the main instructions for Zivid samples.

"""

import argparse
from pathlib import Path
from typing import Tuple

import numpy as np
import zivid
from sample_utils.display import display_depthmap, display_pointcloud
from sample_utils.paths import get_sample_data_path
from zivid.point_cloud import PointCloud


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
        default=get_sample_data_path() / "BinWithCalibrationBoard.zdf",
        help="Path to the ZDF file",
    )

    parser.add_argument(
        "--roi-box-bottom-left-corner-x",
        required=False,
        type=float,
        default=-80,
        help="Distance in X coordinate from the board origin to the bottom left bin corner in checkerboard coordinate system",
    )

    parser.add_argument(
        "--roi-box-bottom-left-corner-y",
        required=False,
        type=float,
        default=280,
        help="Distance in Y coordinate from the board origin to the bottom left bin corner in checkerboard coordinate system",
    )

    parser.add_argument(
        "--roi-box-bottom-left-corner-z",
        required=False,
        type=float,
        default=5,
        help="Distance in Z coordinate from the board origin to the bottom left bin corner in checkerboard coordinate system",
    )

    parser.add_argument(
        "--box-dimension-in-axis-x",
        required=False,
        type=float,
        default=600,
        help="Bin dimension in X axis of the checkerboard coordinate system",
    )

    parser.add_argument(
        "--box-dimension-in-axis-y",
        required=False,
        type=float,
        default=400,
        help="Bin dimension in Y axis of the checkerboard coordinate system",
    )

    parser.add_argument(
        "--box-dimension-in-axis-z",
        required=False,
        type=float,
        default=80,
        help="Bin dimension in Z axis of the checkerboard coordinate system",
    )

    parser.add_argument(
        "--downsample",
        required=False,
        type=str,
        choices=["by2x2", "by3x3", "by4x4"],
        help="Downsampling rate; possible value: by2x2, by3x3, and by4x4",
    )

    return parser.parse_args()


def roi_box_point_cloud(
    point_cloud: PointCloud,
    roi_box_bottom_left_corner_x: float,
    roi_box_bottom_left_corner_y: float,
    roi_box_bottom_left_corner_z: float,
    box_dimension_in_axis_x: float,
    box_dimension_in_axis_y: float,
    box_dimension_in_axis_z: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Filter point cloud based on ROI box by providing box location and dimensions.

    This function assumes that the point cloud is transformed to the checkerboard frame.

    Args:
        point_cloud: Zivid point cloud
        roi_box_bottom_left_corner_x: Distance in X coordinate from the board origin to the bottom left bin corner in checkerboard coordinate system
        roi_box_bottom_left_corner_y: Distance in Y coordinate from the board origin to the bottom left bin corner in checkerboard coordinate system
        roi_box_bottom_left_corner_z: Distance in Z coordinate from the board origin to the bottom left bin corner in checkerboard coordinate system
        box_dimension_in_axis_x: Bin dimension in X axis of the checkerboard coordinate system
        box_dimension_in_axis_y: Bin dimension in Y axis of the checkerboard coordinate system
        box_dimension_in_axis_z: Bin dimension in Z axis of the checkerboard coordinate system

    Returns:
        masked_xyz: A masked numpy array of X, Y and Z point cloud coordinates (HxWx3 ndarray)
        masked_rgba: A masked masked RGB image (HxWx3 ndarray)

    """
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba")

    masked_xyz = np.copy(xyz)
    masked_rgba = np.copy(rgba)

    # Creating ROI box mask
    margin_of_box_roi = 10
    mask_x = np.logical_and(
        xyz[:, :, 0] > roi_box_bottom_left_corner_x - margin_of_box_roi,
        xyz[:, :, 0] < roi_box_bottom_left_corner_x + box_dimension_in_axis_x + margin_of_box_roi,
    )
    mask_y = np.logical_and(
        xyz[:, :, 1] < roi_box_bottom_left_corner_y + margin_of_box_roi,
        xyz[:, :, 1] > roi_box_bottom_left_corner_y - box_dimension_in_axis_y - margin_of_box_roi,
    )
    mask_z = np.logical_and(
        xyz[:, :, 2] < roi_box_bottom_left_corner_z + margin_of_box_roi,
        xyz[:, :, 2] > roi_box_bottom_left_corner_z - box_dimension_in_axis_z - margin_of_box_roi,
    )
    mask = np.logical_and(np.logical_and(mask_x, mask_y), mask_z)

    # Filtering out points outside the ROI box
    masked_xyz[~mask] = np.nan
    masked_rgba[~mask] = 0

    return masked_xyz, masked_rgba


def _main() -> None:

    with zivid.Application():

        user_options = _options()
        data_file = user_options.zdf_path
        print(f"Reading ZDF frame from file: {data_file}")
        frame = zivid.Frame(data_file)
        point_cloud = frame.point_cloud()

        print("Displaying the point cloud original point cloud")
        display_pointcloud(point_cloud.copy_data("xyz"), point_cloud.copy_data("rgba")[:, :, 0:3])

        if user_options.downsample:
            point_cloud.downsample(user_options.downsample)

        print("Detecting and estimating pose of the Zivid checkerboard in the camera frame")
        detection_result = zivid.calibration.detect_feature_points(point_cloud)
        transform_camera_to_checkerboard = detection_result.pose().to_matrix()

        print("Camera pose in checkerboard frame:")
        transform_checkerboard_to_camera = np.linalg.inv(transform_camera_to_checkerboard)
        print(transform_checkerboard_to_camera)

        print("Transforming point cloud from camera frame to Checkerboard frame")
        point_cloud.transform(transform_checkerboard_to_camera)

        print("Bottom-Left ROI Box corner:")
        roi_box_bottom_left_corner_x = user_options.roi_box_bottom_left_corner_x  # Positive is "East"
        roi_box_bottom_left_corner_y = user_options.roi_box_bottom_left_corner_y  # Positive is "South"
        roi_box_bottom_left_corner_z = user_options.roi_box_bottom_left_corner_z  # Positive is "Down"
        print(f"X: {roi_box_bottom_left_corner_x}")
        print(f"Y: {roi_box_bottom_left_corner_y}")
        print(f"Z: {roi_box_bottom_left_corner_z}")

        print("ROI Box size:")
        roi_box_length = user_options.box_dimension_in_axis_x
        roi_box_width = user_options.box_dimension_in_axis_y
        roi_box_height = user_options.box_dimension_in_axis_z
        print(f"Length: {roi_box_length}")
        print(f"Width: {roi_box_width}")
        print(f"Height: {roi_box_height}")

        print("Filtering the point cloud based on ROI Box")
        filtered_xyz, filtered_rgba = roi_box_point_cloud(
            point_cloud,
            roi_box_bottom_left_corner_x,
            roi_box_bottom_left_corner_y,
            roi_box_bottom_left_corner_z,
            roi_box_length,
            roi_box_width,
            roi_box_height,
        )

        print("Displaying transformed point cloud after ROI Box filtering")
        display_pointcloud(filtered_xyz, filtered_rgba[:, :, 0:3])

        print("Displaying depth map of the transformed point cloud after ROI Box filtering")
        display_depthmap(filtered_xyz)


if __name__ == "__main__":
    _main()
