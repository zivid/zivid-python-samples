"""
Transform a point cloud from camera to ArUco marker coordinate frame using the marker's estimated pose.

The ZDF file for this sample can be found under the main instructions for Zivid samples.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

For more information on transforming point clouds, check out this tutorial:
https://support.zivid.com/en/latest/camera/academy/applications/transformations.html

"""

from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
import zivid
import zivid.experimental.calibration
from zividsamples.display import display_bgr
from zividsamples.paths import get_sample_data_path
from zividsamples.save_load_matrix import assert_affine_matrix_and_save


def _draw_detected_marker(bgra_image: np.ndarray, detection_result: zivid.calibration.DetectionResult) -> np.ndarray:
    """Draw detected ArUco marker on the BGRA image based on Zivid ArUco marker detection results.

    Args:
        bgra_image: The input BGRA image.
        detection_result: The result object containing detected ArUco markers with their corners.

    Returns:
        bgra_image: The BGR image with ArUco detected marker drawn on it.
    """

    bgr = bgra_image[:, :, 0:3].copy()
    marker_corners = detection_result.detected_markers()[0].corners_in_pixel_coordinates

    for i, corner in enumerate(marker_corners):
        start_point = tuple(map(int, corner))
        end_point = tuple(map(int, marker_corners[(i + 1) % len(marker_corners)]))
        cv2.line(bgr, start_point, end_point, (0, 255, 0), 2)

    return bgr


def _coordinate_system_line(
    bgr_image: np.ndarray,
    first_point: Tuple[int, int],
    second_point: Tuple[int, int],
    line_color: Tuple[int, int, int],
) -> None:
    """Draw a line on a BGR image.

    Args:
        bgr_image: BGR image.
        first_point: Pixel coordinates of the first end point.
        second_point: Pixel coordinates of the second end point.
        line_color: Line color.
    """

    line_thickness = 4
    line_type = cv2.LINE_8
    cv2.line(bgr_image, first_point, second_point, line_color, line_thickness, line_type)


def _zivid_camera_matrix_to_opencv_camera_matrix(camera_matrix: zivid.CameraIntrinsics.CameraMatrix) -> np.ndarray:
    """Convert camera matrix from Zivid to OpenCV.

    Args:
        camera_matrix: Camera matrix in Zivid format.

    Returns:
        camera_matrix_opencv: Camera matrix in OpenCV format.
    """

    return np.array(
        [[camera_matrix.fx, 0.0, camera_matrix.cx], [0.0, camera_matrix.fy, camera_matrix.cy], [0.0, 0.0, 1.0]]
    )


def _zivid_distortion_coefficients_to_opencv_distortion_coefficients(
    distortion_coeffs: zivid.CameraIntrinsics.Distortion,
) -> np.ndarray:
    """Convert distortion coefficients from Zivid to OpenCV.

    Args:
        distortion_coeffs: Camera distortion coefficients in Zivid format.

    Returns:
        distortion_coeffs_opencv: Camera distortion coefficients in OpenCV format.
    """

    return np.array(
        [distortion_coeffs.k1, distortion_coeffs.k2, distortion_coeffs.p1, distortion_coeffs.p2, distortion_coeffs.k3]
    )


def _move_point(
    origin_in_camera_frame: np.ndarray, offset_in_marker_frame: np.ndarray, marker_pose: np.ndarray
) -> np.ndarray:
    """Move a coordinate system origin point given a direction and an offset to create a coordinate system axis point.

    Args:
        origin_in_camera_frame: 3D coordinates of the coordinate system origin point.
        offset_in_marker_frame: 3D coordinates of the offset to move the coordinate system origin point to.
        marker_pose: Transformation matrix (ArUco marker in camera frame).

    Returns:
        translated point: 3D coordinates of coordinate system axis point.
    """

    rotation_matrix = marker_pose[:3, :3]
    offset_rotated = np.dot(rotation_matrix, offset_in_marker_frame)
    return origin_in_camera_frame + offset_rotated


def _get_coordinate_system_points(
    frame: zivid.Frame, marker_pose: np.ndarray, size_of_axis: float
) -> Dict[str, Tuple[int, int]]:
    """Get pixel coordinates of the coordinate system origin and axes.

    Args:
        frame: Zivid frame containing point cloud.
        marker_pose: Transformation matrix (ArUco marker in camera frame).
        size_of_axis: Coordinate system axis length in mm.

    Returns:
        frame_points: Pixel coordinates of the coordinate system origin and axes.
    """

    intrinsics = zivid.experimental.calibration.estimate_intrinsics(frame)
    cv_camera_matrix = _zivid_camera_matrix_to_opencv_camera_matrix(intrinsics.camera_matrix)
    cv_dist_coeffs = _zivid_distortion_coefficients_to_opencv_distortion_coefficients(intrinsics.distortion)

    origin_position = np.array([marker_pose[0, 3], marker_pose[1, 3], marker_pose[2, 3]])
    x_axis_direction = _move_point(origin_position, np.array([size_of_axis, 0.0, 0.0]), marker_pose)
    y_axis_direction = _move_point(origin_position, np.array([0.0, size_of_axis, 0.0]), marker_pose)
    z_axis_direction = _move_point(origin_position, np.array([0.0, 0.0, size_of_axis]), marker_pose)

    points_to_project = np.array([origin_position, x_axis_direction, y_axis_direction, z_axis_direction])
    projected_points = cv2.projectPoints(points_to_project, np.zeros(3), np.zeros(3), cv_camera_matrix, cv_dist_coeffs)[
        0
    ]

    projected_points = projected_points.reshape(-1, 2)
    return {
        "origin_point": (int(projected_points[0][0]), int(projected_points[0][1])),
        "x_axis_point": (int(projected_points[1][0]), int(projected_points[1][1])),
        "y_axis_point": (int(projected_points[2][0]), int(projected_points[2][1])),
        "z_axis_point": (int(projected_points[3][0]), int(projected_points[3][1])),
    }


def _draw_coordinate_system(frame: zivid.Frame, marker_pose: np.ndarray, bgr_image: np.ndarray) -> None:
    """Draw a coordinate system on a BGR image.

    Args:
        frame: Zivid frame containing point cloud.
        marker_pose: Transformation matrix (ArUco marker in camera frame).
        bgr_image: BGR image.
    """

    size_of_axis = 30.0  # each axis has 30 mm of length

    print("Acquiring frame points")
    frame_points = _get_coordinate_system_points(frame, marker_pose, size_of_axis)

    origin_point = frame_points["origin_point"]
    z = frame_points["z_axis_point"]
    y = frame_points["y_axis_point"]
    x = frame_points["x_axis_point"]

    print("Drawing Z axis")
    _coordinate_system_line(bgr_image, origin_point, z, (255, 0, 0))

    print("Drawing Y axis")
    _coordinate_system_line(bgr_image, origin_point, y, (0, 255, 0))

    print("Drawing X axis")
    _coordinate_system_line(bgr_image, origin_point, x, (0, 0, 255))


def _main() -> None:
    # Application class must be initialized before using other Zivid classes.
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    data_file = get_sample_data_path() / "CalibrationBoardInCameraOrigin.zdf"
    print(f"Reading ZDF frame from file: {data_file}")

    frame = zivid.Frame(data_file)
    point_cloud = frame.point_cloud()

    print("Configuring ArUco marker")
    marker_dictionary = zivid.calibration.MarkerDictionary.aruco4x4_50
    marker_id = [1]

    print("Detecting ArUco marker")
    detection_result = zivid.calibration.detect_markers(frame, marker_id, marker_dictionary)

    if not detection_result.valid():
        raise RuntimeError("No ArUco markers detected")

    print("Converting to OpenCV image format")
    bgra_image = point_cloud.copy_data("bgra_srgb")

    print("Displaying detected ArUco marker")
    bgr = _draw_detected_marker(bgra_image, detection_result)
    display_bgr(bgr, "ArucoMarkerDetected")

    bgr_image_file = "ArucoMarkerDetected.png"
    print(f"Saving 2D color image with detected ArUco marker to file: {bgr_image_file}")
    cv2.imwrite(bgr_image_file, bgr)

    print("Estimating pose of detected ArUco marker")
    camera_to_marker_transform = detection_result.detected_markers()[0].pose.to_matrix()
    print("ArUco marker pose in camera frame:")
    print(camera_to_marker_transform)
    print("Camera pose in ArUco marker frame:")
    marker_to_camera_transform = np.linalg.inv(camera_to_marker_transform)
    print(marker_to_camera_transform)

    print("Visualizing ArUco marker with coordinate system")
    bgr_coordinate_system = bgra_image[:, :, 0:3].copy()
    _draw_coordinate_system(frame, camera_to_marker_transform, bgr_coordinate_system)
    display_bgr(bgr_coordinate_system, "ArUco marker transformation frame")

    transform_file = Path("ArUcoMarkerToCameraTransform.yaml")
    print("Saving a YAML file with Inverted ArUco marker pose to file: ")
    assert_affine_matrix_and_save(marker_to_camera_transform, transform_file)

    print("Transforming point cloud from camera frame to ArUco marker frame")
    point_cloud.transform(marker_to_camera_transform)

    aruco_marker_transformed_file = "CalibrationBoardInArucoMarkerOrigin.zdf"
    print(f"Saving transformed point cloud to file: {aruco_marker_transformed_file}")
    frame.save(aruco_marker_transformed_file)


if __name__ == "__main__":
    _main()
