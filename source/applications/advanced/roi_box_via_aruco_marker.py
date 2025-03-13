"""
Filter the point cloud based on a ROI box given relative to the ArUco marker on a Zivid Calibration Board.

The ZFC file for this sample can be downloaded from https://support.zivid.com/en/latest/api-reference/samples/sample-data.html.

"""

from typing import List

import numpy as np
import zivid
from zividsamples.display import display_depthmap, display_pointcloud
from zividsamples.paths import get_sample_data_path


def _transform_points(points: List[np.ndarray], transform: np.ndarray) -> List[np.ndarray]:
    """Perform a homogenous transformation to every point in 'points' and return the transformed points.

    Args:
        points: list of 3D points to be transformed
        transform: homogenous transformation matrix (4x4)

    Returns:
        transformed_points: list of transformed 3D points

    """
    rotation_matrix = transform[:3, :3]
    translation_vector = transform[:3, 3]

    transformed_points = []
    for point in points:
        transformed_points.append(rotation_matrix @ point + translation_vector)

    return transformed_points


def _main() -> None:
    with zivid.Application() as app:

        file_camera = get_sample_data_path() / "BinWithCalibrationBoard.zfc"

        print(f"Creating virtual camera using file: {file_camera}")
        camera = app.create_file_camera(file_camera)

        settings = zivid.Settings([zivid.Settings.Acquisition()])
        settings.color = zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()])

        original_frame = camera.capture_2d_3d(settings)
        point_cloud = original_frame.point_cloud()

        print("Displaying the original point cloud")
        display_pointcloud(point_cloud.copy_data("xyz"), point_cloud.copy_data("rgba")[:, :, :3])

        print("Configuring ROI box based on bin size and checkerboard placement")
        roi_box_length = 545
        roi_box_width = 345
        roi_box_height = 150

        # Coordinates are relative to the ArUco marker origin which lies in the center of the ArUco marker.
        # Positive x-axis is "East", y-axis is "South" and z-axis is "Down".
        roi_box_lower_right_corner_in_aruco_frame = np.array([240, 30, 5])
        roi_box_upper_right_corner_in_aruco_frame = np.array(
            [
                roi_box_lower_right_corner_in_aruco_frame[0],
                roi_box_lower_right_corner_in_aruco_frame[1] - roi_box_width,
                roi_box_lower_right_corner_in_aruco_frame[2],
            ]
        )
        roi_box_lower_left_corner_in_aruco_frame = np.array(
            [
                roi_box_lower_right_corner_in_aruco_frame[0] - roi_box_length,
                roi_box_lower_right_corner_in_aruco_frame[1],
                roi_box_lower_right_corner_in_aruco_frame[2],
            ]
        )

        point_o_in_aruco_frame = roi_box_lower_right_corner_in_aruco_frame
        point_a_in_aruco_frame = roi_box_upper_right_corner_in_aruco_frame
        point_b_in_aruco_frame = roi_box_lower_left_corner_in_aruco_frame

        print("Configuring ArUco marker")
        marker_dictionary = zivid.calibration.MarkerDictionary.aruco4x4_50
        marker_id = [1]

        print("Detecting ArUco marker")
        detection_result = zivid.calibration.detect_markers(original_frame, marker_id, marker_dictionary)

        if not detection_result.valid():
            raise RuntimeError("No ArUco markers detected")

        print("Estimating pose of detected ArUco marker")
        camera_to_marker_transform = detection_result.detected_markers()[0].pose.to_matrix()

        print("Transforming the ROI base frame points to the camera frame")
        roi_points_in_camera_frame = _transform_points(
            [point_o_in_aruco_frame, point_a_in_aruco_frame, point_b_in_aruco_frame],
            camera_to_marker_transform,
        )

        print("Setting the ROI")
        settings.region_of_interest.box.enabled = True
        settings.region_of_interest.box.point_o = roi_points_in_camera_frame[0]
        settings.region_of_interest.box.point_a = roi_points_in_camera_frame[1]
        settings.region_of_interest.box.point_b = roi_points_in_camera_frame[2]
        settings.region_of_interest.box.extents = (-10, roi_box_height)

        roi_point_cloud = camera.capture_2d_3d(settings).point_cloud()

        print("Displaying the ROI-filtered point cloud")
        display_pointcloud(roi_point_cloud.copy_data("xyz"), roi_point_cloud.copy_data("rgba")[:, :, :3])

        print("Displaying depth map of the ROI-filtered point cloud")
        display_depthmap(roi_point_cloud.copy_data("xyz"))


if __name__ == "__main__":
    _main()
