"""
Detect and decode linear and matrix barcodes from a 2D capture.

For more information on how to use the Zivid Barcode Detector, check out the Barcode Detection tutorial:
https://support.zivid.com/en/latest/camera/academy/applications/barcode-detection.html

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
        LinearBarcodeFormat.itf,
    }
    matrix_format_filter = {MatrixBarcodeFormat.qrcode, MatrixBarcodeFormat.dataMatrix}

    settings_2d = barcode_detector.suggest_settings(camera)

    print("Capturing 2D frame ...")
    frame_2d = camera.capture_2d(settings_2d)

    print("Detecting linear barcode candidates ...")
    detection_results = barcode_detector.detect_linear_codes(frame_2d)

    decoding_results = barcode_detector.decode_linear_codes(detection_results, linear_format_filter)

    if detection_results:
        print(f"Detected {len(detection_results)} linear barcode candidates:")
        for i, (candidate, decoded) in enumerate(zip(detection_results, decoding_results, strict=False)):
            print(f"-- Candidate {i + 1}:")
            print(f"   Bounding box: {candidate.bounding_box()}")
            if decoded is not None:
                print(f"   Code:         {decoded.code()}")
                print(f"   Format:       {decoded.code_format()}")
                print(f"   Bounding box: {decoded.bounding_box()}")
            else:
                print("   Failed to decode")
    else:
        print("No linear barcode candidates detected")

    print("Reading matrix barcodes ...")
    matrix_barcode_results = barcode_detector.read_matrix_codes(frame_2d, matrix_format_filter)

    if matrix_barcode_results:
        print(f"Detected {len(matrix_barcode_results)} matrix barcodes:")
        for result in matrix_barcode_results:
            print(f"-- Code:         {result.code()}")
            print(f"   Format:       {result.code_format()}")
            print(f"   Bounding box: {result.bounding_box()}")
    else:
        print("No matrix barcodes detected")


if __name__ == "__main__":
    _main()
