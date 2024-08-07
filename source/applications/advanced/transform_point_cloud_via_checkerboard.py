"""
Transform a point cloud from camera to checkerboard (Zivid Calibration Board) coordinate frame by getting checkerboard pose from the API.

The ZDF file for this sample can be found under the main instructions for Zivid samples.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
import zivid
import zivid.experimental.calibration
from sample_utils.display import display_bgr
from sample_utils.paths import get_sample_data_path
from sample_utils.save_load_matrix import assert_affine_matrix_and_save


def _coordinate_system_line(
    bgra_image: np.ndarray,
    first_point: Tuple[int, int],
    second_point: Tuple[int, int],
    line_color: Tuple[int, int, int],
) -> None:
    """Draw a line on a BGRA image.

    Args:
        bgra_image: BGRA image.
        first_point: Pixel coordinates of the first end point.
        second_point: Pixel coordinates of the second end point.
        line_color: Line color.
    """

    line_thickness = 4
    line_type = cv2.LINE_8
    cv2.line(bgra_image, first_point, second_point, line_color, line_thickness, line_type)


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
    origin_in_camera_frame: np.ndarray, offset_in_board_frame: np.ndarray, checkerboard_pose: np.ndarray
) -> np.ndarray:
    """Move a coordinate system origin point given a direction and an offset to create a coordinate system axis point.

    Args:
        origin_in_camera_frame: 3D coordinates of the coordinate system origin point.
        offset_in_board_frame: 3D coordinates of the offset to move the coordinate system origin point to.
        checkerboard_pose: Transformation matrix (checkerboard in camera frame).

    Returns:
        translated point: 3D coordinates of coordinate system axis point.
    """

    rotation_matrix = checkerboard_pose[:3, :3]
    offset_rotated = np.dot(rotation_matrix, offset_in_board_frame)
    return origin_in_camera_frame + offset_rotated


def _get_coordinate_system_points(
    frame: zivid.Frame, checkerboard_pose: np.ndarray, size_of_axis: float
) -> Dict[str, Tuple[int, int]]:
    """Get pixel coordinates of the coordinate system origin and axes.

    Args:
        frame: Zivid frame containing point cloud.
        checkerboard_pose: Transformation matrix (checkerboard in camera frame).
        size_of_axis: Coordinate system axis length in mm.

    Returns:
        frame_points: Pixel coordinates of the coordinate system origin and axes.
    """

    intrinsics = zivid.experimental.calibration.estimate_intrinsics(frame)
    cv_camera_matrix = _zivid_camera_matrix_to_opencv_camera_matrix(intrinsics.camera_matrix)
    cv_dist_coeffs = _zivid_distortion_coefficients_to_opencv_distortion_coefficients(intrinsics.distortion)

    origin_position = np.array([checkerboard_pose[0, 3], checkerboard_pose[1, 3], checkerboard_pose[2, 3]])
    x_axis_direction = _move_point(origin_position, np.array([size_of_axis, 0.0, 0.0]), checkerboard_pose)
    y_axis_direction = _move_point(origin_position, np.array([0.0, size_of_axis, 0.0]), checkerboard_pose)
    z_axis_direction = _move_point(origin_position, np.array([0.0, 0.0, size_of_axis]), checkerboard_pose)

    points_to_project = np.array([origin_position, x_axis_direction, y_axis_direction, z_axis_direction])
    projected_points = cv2.projectPoints(points_to_project, np.zeros(3), np.zeros(3), cv_camera_matrix, cv_dist_coeffs)

    projected_points = projected_points.reshape(-1, 2)
    return {
        "origin_point": (int(projected_points[0][0]), int(projected_points[0][1])),
        "x_axis_point": (int(projected_points[1][0]), int(projected_points[1][1])),
        "y_axis_point": (int(projected_points[2][0]), int(projected_points[2][1])),
        "z_axis_point": (int(projected_points[3][0]), int(projected_points[3][1])),
    }


def _draw_coordinate_system(frame: zivid.Frame, checkerboard_pose: np.ndarray, bgra_image: np.ndarray) -> None:
    """Draw a coordinate system on a BGRA image.

    Args:
        frame: Zivid frame containing point cloud.
        checkerboard_pose: Transformation matrix (checkerboard in camera frame).
        bgra_image: BGRA image.
    """

    size_of_axis = 30.0  # each axis has 30 mm of length

    print("Acquiring frame points")
    frame_points = _get_coordinate_system_points(frame, checkerboard_pose, size_of_axis)

    origin_point = frame_points["origin_point"]
    z = frame_points["z_axis_point"]
    y = frame_points["y_axis_point"]
    x = frame_points["x_axis_point"]

    print("Drawing Z axis")
    _coordinate_system_line(bgra_image, origin_point, z, (255, 0, 0))

    print("Drawing Y axis")
    _coordinate_system_line(bgra_image, origin_point, y, (0, 255, 0))

    print("Drawing X axis")
    _coordinate_system_line(bgra_image, origin_point, x, (0, 0, 255))


def _main() -> None:
    with zivid.Application():

        data_file = get_sample_data_path() / "CalibrationBoardInCameraOrigin.zdf"
        print(f"Reading ZDF frame from file: {data_file}")
        frame = zivid.Frame(data_file)
        point_cloud = frame.point_cloud()

        print("Detecting and estimating pose of the Zivid checkerboard in the camera frame")
        detection_result = zivid.calibration.detect_calibration_board(frame)
        camera_to_checkerboard_transform = detection_result.pose().to_matrix()
        print(camera_to_checkerboard_transform)
        print("Camera pose in checkerboard frame:")
        checkerboard_to_camera_transform = np.linalg.inv(camera_to_checkerboard_transform)
        print(checkerboard_to_camera_transform)

        transform_file = Path("CheckerboardToCameraTransform.yaml")
        print("Saving a YAML file with Inverted checkerboard pose to file: ")
        assert_affine_matrix_and_save(checkerboard_to_camera_transform, transform_file)

        print("Transforming point cloud from camera frame to Checkerboard frame")
        point_cloud.transform(checkerboard_to_camera_transform)

        print("Converting to OpenCV image format")
        bgra_image = point_cloud.copy_data("bgra")

        print("Visualizing checkerboard with coordinate system")
        _draw_coordinate_system(frame, camera_to_checkerboard_transform, bgra_image)
        display_bgr(bgra_image, "Checkerboard transformation frame")

        checkerboard_transformed_file = "CalibrationBoardInCheckerboardOrigin.zdf"
        print(f"Saving transformed point cloud to file: {checkerboard_transformed_file}")
        frame.save(checkerboard_transformed_file)


if __name__ == "__main__":
    _main()
