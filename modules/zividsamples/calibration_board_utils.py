"""
Utility functions for the Zivid calibration board.

"""

from typing import Tuple

import cv2
import numpy as np


def _get_mask_from_polygons(polygons: np.ndarray, shape: Tuple) -> np.ndarray:
    """Make mask on each channel for pixels filled by polygons.

    Args:
        polygons: (N, 4, 1, 2) array of polygon vertices
        shape: (H, W) of mask

    Returns:
        mask: Mask of bools (H, W), True for pixels fill by polygons

    """
    mask = np.zeros(shape[:2])
    cv2.fillPoly(mask, polygons, 1)
    mask[0, 0] = 0
    return mask


def _make_white_squares_mask(checkerboard_corners: np.ndarray, image_shape: Tuple) -> np.ndarray:
    """Make mask of bools covering pixels containing white checkerboard squares. True for pixels with white checkers,
    False otherwise.

    Args:
        checkerboard_corners: ((rows-1), (cols-1), 2) float array of inner-corner coordinates
        image_shape: (H, W)

    Returns:
        white_squares_mask: Mask of bools (H, W) for pixels containing white checkerboard squares

    """
    number_of_white_squares = (checkerboard_corners.shape[0] // 2) * checkerboard_corners.shape[1]
    white_vertices = np.zeros((number_of_white_squares, 4, 1, 2), dtype=np.int32)
    vertex_idx = 0
    for row in range(checkerboard_corners.shape[0] - 1):
        for col in range(checkerboard_corners.shape[1] - 1):
            if ((row % 2 == 0) and (col % 2 == 0)) or ((row % 2 == 1) and (col % 2 == 1)):
                white_vertices[vertex_idx, 0, 0, :] = checkerboard_corners[row, col, :]
                white_vertices[vertex_idx, 1, 0, :] = checkerboard_corners[row, col + 1, :]
                white_vertices[vertex_idx, 2, 0, :] = checkerboard_corners[row + 1, col + 1, :]
                white_vertices[vertex_idx, 3, 0, :] = checkerboard_corners[row + 1, col, :]

                vertex_idx += 1

    white_squares_mask = _get_mask_from_polygons(white_vertices, image_shape)

    return white_squares_mask


def _detect_checkerboard_opencv(rgb: np.ndarray) -> np.ndarray:
    """Use OpenCV to detect corner coordinates of a (7, 8) checkerboard.

    Args:
        rgb: RGB image (H, W, 3)

    Raises:
        RuntimeError: If checkerboard cannot be detected in image

    Returns:
        Array ((rows-1), (cols-1), 2) of inner-corner coordinates

    """
    grayscale = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    checkerboard_size = (7, 8)
    checkerboard_size_opencv = (checkerboard_size[1] - 1, checkerboard_size[0] - 1)
    chessboard_flags = cv2.CALIB_CB_ACCURACY | cv2.CALIB_CB_EXHAUSTIVE

    success, corners = cv2.findChessboardCornersSB(grayscale, checkerboard_size_opencv, chessboard_flags)
    if not success:
        # Trying histogram equalization for more contrast
        grayscale_equalized = cv2.equalizeHist(grayscale)
        success, corners = cv2.findChessboardCornersSB(grayscale_equalized, checkerboard_size_opencv, chessboard_flags)

    if corners is None:
        raise RuntimeError("Failed to detect checkerboard in image.")

    return corners.flatten().reshape(checkerboard_size_opencv[1], checkerboard_size_opencv[0], 2)


def find_white_mask_from_checkerboard(rgb: np.ndarray) -> np.ndarray:
    """Generate a 2D mask of the white checkers on a (7, 8) checkerboard.

    Args:
        rgb: RGB image (H, W, 3)

    Returns:
        white_squares_mask: Mask of bools (H, W) for pixels containing white checkerboard squares

    """
    checkerboard_corners = _detect_checkerboard_opencv(rgb)
    white_squares_mask = _make_white_squares_mask(checkerboard_corners, rgb.shape)

    return white_squares_mask
