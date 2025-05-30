from typing import List, Tuple

import numpy as np
import zivid
from nptyping import NDArray, Shape, UInt8
from zivid.calibration import MarkerShape
from zivid.experimental import PixelMapping
from zividsamples.gui.fov import PointsOfInterest, PointsOfInterest2D
from zividsamples.transformation_matrix import TransformationMatrix


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


class CV2Handler:
    def __init__(self):
        import cv2  # pylint: disable=import-outside-toplevel

        self.cv2 = cv2

    def project_points(self, points: NDArray[Shape["N, 3"], np.float32], intrinsics: zivid.CameraIntrinsics) -> NDArray[Shape["N, 2"], np.float32]:  # type: ignore
        points_2d, _ = self.cv2.projectPoints(
            np.array(points, dtype=np.float32),
            rvec=np.zeros(3),
            tvec=np.zeros(3),
            cameraMatrix=_zivid_camera_matrix_to_opencv_camera_matrix(intrinsics.camera_matrix),
            distCoeffs=_zivid_distortion_coefficients_to_opencv_distortion_coefficients(intrinsics.distortion),
        )
        return np.array(points_2d).reshape(-1, 2)

    def points_of_interest_in_2d_from_3d(
        self, points_of_interest: PointsOfInterest, intrinsics: zivid.CameraIntrinsics
    ) -> PointsOfInterest2D:
        full_fov_corners_2d = self.project_points(points_of_interest.full_fov_corners, intrinsics)
        full_fov_corners_2d_with_margin = self.project_points(
            points_of_interest.full_fov_corners_with_margin, intrinsics
        )
        center_points_2d = self.project_points(points_of_interest.center_corners, intrinsics)
        line_points_2d = self.project_points(points_of_interest.lines_3d().reshape(-1, 3), intrinsics)
        lines_2d = line_points_2d.reshape(-1, 2, 2).astype(int)  # pylint: disable=too-many-function-args
        return PointsOfInterest2D(
            full_fov_corners=np.array(full_fov_corners_2d, dtype=np.int32),
            full_fov_corners_with_margin=np.array(full_fov_corners_2d_with_margin, dtype=np.int32),
            center_corners=np.array(center_points_2d, dtype=np.int32),
            left_top_line=lines_2d[0],
            left_bottom_line=lines_2d[1],
            top_left_line=lines_2d[2],
            top_right_line=lines_2d[3],
            right_top_line=lines_2d[4],
            right_bottom_line=lines_2d[5],
            bottom_left_line=lines_2d[6],
            bottom_right_line=lines_2d[7],
            left_center_line=lines_2d[8],
            top_center_line=lines_2d[9],
            right_center_line=lines_2d[10],
            bottom_center_line=lines_2d[11],
        )

    def draw_detected_markers(
        self,
        detected_markers: List[MarkerShape],
        rgb: NDArray[Shape["N, M, 3"], UInt8],  # type: ignore
        pixel_mapping: PixelMapping,
    ):
        detected_corners = [
            np.array(marker.corners_in_pixel_coordinates).reshape((4, 1, 2)) for marker in detected_markers
        ]
        detected_corners = [
            (corner * [pixel_mapping.col_stride, pixel_mapping.row_stride])
            + [pixel_mapping.col_offset, pixel_mapping.row_offset]
            for corner in detected_corners
        ]
        marker_ids = np.array([marker.identifier for marker in detected_markers])
        return self.cv2.aruco.drawDetectedMarkers(rgb, detected_corners, marker_ids, [0, 255, 0])

    def draw_projected_axis_cross(
        self,
        intrinsics: zivid.CameraIntrinsics,
        rgb: NDArray[Shape["N, M, 3"], UInt8],  # type: ignore
        pose: TransformationMatrix,
    ) -> NDArray[Shape["N, M, 3"], UInt8]:  # type: ignore
        axis_length = 30
        axis_points = np.array(
            [
                [0, 0, 0],  # Origin
                [axis_length, 0, 0],  # X-axis
                [0, axis_length, 0],  # Y-axis
                [0, 0, axis_length],  # Z-axis
            ],
            dtype=np.float32,
        )
        transformed_axis_points = pose.transform(axis_points)
        projected_points = self.project_points(transformed_axis_points, intrinsics)
        projected_points = projected_points.reshape(-1, 2).astype(int)
        self.cv2.arrowedLine(
            rgb,
            projected_points[0],
            projected_points[3],
            color=(0, 0, 255),
            thickness=8,
            tipLength=0.1,
        )
        self.cv2.arrowedLine(
            rgb,
            projected_points[0],
            projected_points[1],
            color=(255, 0, 0),
            thickness=8,
            tipLength=0.1,
        )
        self.cv2.arrowedLine(
            rgb,
            projected_points[0],
            projected_points[2],
            color=(0, 255, 0),
            thickness=8,
            tipLength=0.1,
        )
        return rgb

    def draw_3d_points_in_2d(
        self,
        intrinsics: zivid.CameraIntrinsics,
        rgb: NDArray[Shape["N, M, 3"], UInt8],  # type: ignore
        points: NDArray[Shape["N, 3"], np.int32],  # type: ignore
        circle_color: Tuple[int, int, int, int] = (0, 255, 0, 255),
    ):
        circle_size_in_pixels: int = 8
        np_points = np.array(points, dtype=np.float32)
        projected_points, _ = self.cv2.projectPoints(
            np_points,
            rvec=np.zeros(3),
            tvec=np.zeros(3),
            cameraMatrix=_zivid_camera_matrix_to_opencv_camera_matrix(intrinsics.camera_matrix),
            distCoeffs=_zivid_distortion_coefficients_to_opencv_distortion_coefficients(intrinsics.distortion),
        )
        projected_points = projected_points.reshape(-1, 2).astype(int)
        for original_point, projected_point in zip(np_points, projected_points, strict=False):
            self.cv2.circle(
                img=rgb,
                center=projected_point,
                radius=circle_size_in_pixels,
                color=circle_color,
                thickness=self.cv2.FILLED,
                lineType=self.cv2.LINE_AA,
            )
            text = f"[{original_point[0]:6.1f}, {original_point[1]:6.1f}, {original_point[2]:6.1f}]"
            text_size, _ = self.cv2.getTextSize(text, self.cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            text_x = projected_point[0] - text_size[0] // 2
            if projected_point[1] < rgb.shape[0] // 3:
                text_y = projected_point[1] + circle_size_in_pixels + text_size[1] * 2
            else:
                text_y = projected_point[1] - circle_size_in_pixels - text_size[1] * 2
            self.cv2.rectangle(
                img=rgb,
                pt1=(text_x, text_y - text_size[1]),
                pt2=(text_x + text_size[0], text_y + text_size[1]),
                color=(255, 255, 255),
                thickness=self.cv2.FILLED,
            )
            self.cv2.putText(
                img=rgb,
                text=text,
                org=(text_x, text_y),
                fontFace=self.cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.5,
                color=(0, 0, 0),  # Black text
                thickness=1,
                lineType=self.cv2.LINE_AA,
            )
        return rgb

    def draw_circles(
        self,
        image: NDArray[Shape["N, M, 3"], UInt8],  # type: ignore
        points: NDArray[Shape["N, 2"], np.int32],  # type: ignore
        circle_color: Tuple[int, int, int, int] = (0, 255, 0, 255),
    ):
        circle_size_in_pixels = 2
        for point in points:
            self.cv2.circle(
                img=image,
                center=point,
                radius=circle_size_in_pixels,
                color=circle_color,
                thickness=self.cv2.FILLED,
                lineType=self.cv2.LINE_AA,
            )

    def draw_polygons(
        self,
        image: NDArray[Shape["N, M, 3"], UInt8],  # type: ignore
        points: NDArray[Shape["N, 2"], np.int32],  # type: ignore
        *,
        color: Tuple[int, int, int, int] = (0, 255, 0, 255),
        isClosed: bool = True,
        thickness: int = 1,
    ) -> None:
        polygons = points.reshape((1, -1, 1, 2))
        for polygon in polygons:
            self.cv2.polylines(
                image,
                [polygon],
                isClosed=isClosed,
                color=color,
                thickness=thickness,
                lineType=self.cv2.LINE_AA,
            )

    def draw_fov_division_from_3d(self, rgb: NDArray[Shape["N, M, 3"], UInt8], points_of_interest_3d: PointsOfInterest, intrinsics: zivid.CameraIntrinsics):  # type: ignore
        self.draw_fov_division(rgb, self.points_of_interest_in_2d_from_3d(points_of_interest_3d, intrinsics))

    def draw_fov_division(self, rgb: NDArray[Shape["N, M, 3"], UInt8], points_of_interest_2d: PointsOfInterest2D, use_bgr: bool = False):  # type: ignore
        thickness = 8
        lines_2d = points_of_interest_2d.lines_2d()
        for line_2d in lines_2d[-4:]:
            self.draw_polygons(
                rgb,
                points=line_2d,
                color=(0, 150, 0, 255),
                isClosed=False,
                thickness=thickness // 2,
            )
        self.draw_polygons(
            rgb,
            points=points_of_interest_2d.full_fov_corners_with_margin,
            color=(0, 0, 255, 255) if use_bgr else (255, 0, 0, 255),
            isClosed=True,
            thickness=thickness,
        )
        self.draw_polygons(
            rgb,
            points=points_of_interest_2d.full_fov_corners,
            color=(255, 0, 0, 255) if use_bgr else (0, 0, 255, 255),
            isClosed=True,
            thickness=thickness,
        )
        self.draw_polygons(
            rgb, points=points_of_interest_2d.center_corners, color=(0, 255, 0, 255), thickness=thickness
        )

    def apply_colormap(self, depth_map_uint8: NDArray[Shape["N, M, 3"], UInt8]):  # type: ignore
        return self.cv2.applyColorMap(depth_map_uint8, self.cv2.COLORMAP_VIRIDIS)
