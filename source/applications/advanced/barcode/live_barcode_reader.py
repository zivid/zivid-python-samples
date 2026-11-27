"""
Continuously capture 2D frames, detect and decode barcodes, and display a live view with the results overlaid.

For each decoded barcode, this sample draws its bounding box, code, and an arrow showing its
decoded orientation, meaning the direction the barcode should be read in.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

For more information on how to use the Zivid Barcode Detector, check out the Barcode Reading tutorial:
https://support.zivid.com/en/latest/camera/academy/applications/barcode-detection.html
"""

import math
from typing import List, Union

import cv2
import numpy
import zivid
from zivid.experimental.toolbox.barcode import (
    BarcodeDetector,
    LinearBarcodeDecodingResult,
    MatrixBarcodeDecodingResult,
)

_ARROW_LENGTH_PX = 80
_ARROW_HEAD_ANGLE_DEGREES = 30.0
_ARROW_HEAD_LENGTH_RATIO = 0.3
_ARROW_COLOR = (31, 95, 255)  # neon orange, BGR
_BOX_COLOR = (0, 200, 0)  # green, BGR
_TEXT_COLOR = (255, 0, 0)  # blue, BGR


def _draw_arrow(image: numpy.ndarray, start: tuple, tip: tuple, color: tuple, thickness: int) -> None:
    """Draw an arrow from start to tip, with a head angle narrower than cv2.arrowedLine's fixed 45 degrees.

    Args:
        image: Image to draw on, modified in place.
        start: Arrow shaft start point, as (x, y).
        tip: Arrow shaft end point (the arrowhead location), as (x, y).
        color: Line color, as BGR tuple.
        thickness: Line thickness in pixels.
    """
    cv2.line(image, start, tip, color, thickness, cv2.LINE_AA)

    shaft_length = math.hypot(start[0] - tip[0], start[1] - tip[1])
    head_length = shaft_length * _ARROW_HEAD_LENGTH_RATIO
    reversed_angle = math.atan2(start[1] - tip[1], start[0] - tip[0])
    head_angle_rad = math.radians(_ARROW_HEAD_ANGLE_DEGREES)

    for sign in (1.0, -1.0):
        head_point = (
            int(round(tip[0] + head_length * math.cos(reversed_angle + sign * head_angle_rad))),
            int(round(tip[1] + head_length * math.sin(reversed_angle + sign * head_angle_rad))),
        )
        cv2.line(image, tip, head_point, color, thickness, cv2.LINE_AA)


def _draw_decoding_result(
    image: numpy.ndarray, decoding_result: Union[LinearBarcodeDecodingResult, MatrixBarcodeDecodingResult]
) -> None:
    """Draw a decoded barcode's bounding box, code, and orientation arrow onto image in place.

    Args:
        image: Image to draw on, modified in place.
        decoding_result: A LinearBarcodeDecodingResult or MatrixBarcodeDecodingResult.
    """
    box = decoding_result.bounding_box()
    top_left = (box.x, box.y)
    bottom_right = (box.x + box.width, box.y + box.height)
    cv2.rectangle(image, top_left, bottom_right, _BOX_COLOR, 2)

    center_x, center_y = decoding_result.center_position()
    center = (int(round(center_x)), int(round(center_y)))

    orientation = decoding_result.orientation()
    tip = (
        int(round(center_x + orientation.x * _ARROW_LENGTH_PX)),
        int(round(center_y + orientation.y * _ARROW_LENGTH_PX)),
    )
    _draw_arrow(image, center, tip, _ARROW_COLOR, 3)

    label = f"{decoding_result.code()} ({orientation.angle_in_degrees():.0f} deg)"
    cv2.putText(
        image,
        label,
        (box.x, max(box.y - 10, 0)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        _TEXT_COLOR,
        2,
        cv2.LINE_AA,
    )


def _draw_overlay(
    image: numpy.ndarray,
    linear_results: List[LinearBarcodeDecodingResult],
    matrix_results: List[MatrixBarcodeDecodingResult],
) -> None:
    """Draw every decoded barcode plus a count label onto image in place.

    Args:
        image: Image to draw on, modified in place.
        linear_results: Decoded linear barcodes.
        matrix_results: Decoded matrix barcodes.
    """
    for result in linear_results:
        _draw_decoding_result(image, result)
    for result in matrix_results:
        _draw_decoding_result(image, result)

    cv2.putText(
        image,
        f"Linear: {len(linear_results)}  Matrix: {len(matrix_results)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        _TEXT_COLOR,
        2,
        cv2.LINE_AA,
    )


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    barcode_detector = BarcodeDetector()

    settings_2d = barcode_detector.suggest_settings(camera)

    window_name = "Zivid Live Barcode Reader (press 'q' or Esc to exit)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    print("Press q to exit the viewer application")
    try:
        while True:
            frame_2d = camera.capture_2d(settings_2d)
            image = frame_2d.image_bgr_srgb().copy_data()

            # Reading all formats here; passing only the formats you use is faster and more reliable
            linear_results = barcode_detector.read_linear_codes(frame_2d)
            matrix_results = barcode_detector.read_matrix_codes(frame_2d)

            _draw_overlay(image, linear_results, matrix_results)

            cv2.imshow(window_name, image)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):  # 27 == Esc
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        cv2.destroyAllWindows()
        camera.disconnect()


if __name__ == "__main__":
    _main()
