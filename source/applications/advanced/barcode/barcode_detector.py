"""
Detect and decode linear and matrix barcodes from a 2D capture.

"""

import zivid
from zivid.experimental.toolbox.barcode import BarcodeDetector, LinearBarcodeFormat, MatrixBarcodeFormat


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    barcode_detector = BarcodeDetector()

    # Select your specific barcode formats for optimal performance
    linear_format_filter = {
        LinearBarcodeFormat.code128,
        LinearBarcodeFormat.code93,
        LinearBarcodeFormat.code39,
        LinearBarcodeFormat.ean13,
        LinearBarcodeFormat.ean8,
        LinearBarcodeFormat.upcA,
        LinearBarcodeFormat.upcE,
    }
    matrix_format_filter = {MatrixBarcodeFormat.qrcode, MatrixBarcodeFormat.dataMatrix}

    settings_2d = barcode_detector.suggest_settings(camera)

    print("Detecting barcodes ...")
    frame_2d = camera.capture_2d(settings_2d)

    linear_barcode_results = barcode_detector.read_linear_codes(frame_2d, linear_format_filter)
    matrix_barcode_results = barcode_detector.read_matrix_codes(frame_2d, matrix_format_filter)

    if linear_barcode_results:
        print(f"Detected {len(linear_barcode_results)} linear barcodes:")
        for result in linear_barcode_results:
            print(
                f"-- Detected barcode {result.code()} on format {result.code_format()} at pixel {result.center_position()}"
            )

    if matrix_barcode_results:
        print(f"Detected {len(matrix_barcode_results)} matrix barcodes:")
        for result in matrix_barcode_results:
            print(
                f"-- Detected barcode {result.code()} on format {result.code_format()} at pixel {result.center_position()}"
            )

    if not linear_barcode_results and not matrix_barcode_results:
        print("No barcodes detected")


if __name__ == "__main__":
    _main()
