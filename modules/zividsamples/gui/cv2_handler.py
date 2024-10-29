from typing import List, Tuple

import numpy as np
import zivid
from nptyping import NDArray, Shape, UInt8
from zivid.calibration import MarkerShape
from zivid.experimental import PixelMapping
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
        projected_points, _ = self.cv2.projectPoints(
            transformed_axis_points,
            rvec=np.zeros(3),
            tvec=np.zeros(3),
            cameraMatrix=_zivid_camera_matrix_to_opencv_camera_matrix(intrinsics.camera_matrix),
            distCoeffs=_zivid_distortion_coefficients_to_opencv_distortion_coefficients(intrinsics.distortion),
        )
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
        color: Tuple[int, int, int, int] = (0, 255, 0, 255),
    ) -> None:
        polygons = points.reshape((-1, 4, 1, 2))
        for polygon in polygons:
            self.cv2.polylines(
                image,
                [polygon],
                isClosed=True,
                color=color,
                thickness=1,
                lineType=self.cv2.LINE_AA,
            )

    def apply_colormap(self, depth_map_uint8: NDArray[Shape["N, M, 3"], UInt8]):  # type: ignore
        return self.cv2.applyColorMap(depth_map_uint8, self.cv2.COLORMAP_VIRIDIS)
