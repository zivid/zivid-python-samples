"""
Use captures of a calibration object to generate transformation matrices to a single coordinate frame, from ZDF files.
"""

import argparse
from pathlib import Path
from typing import List, Tuple

import zivid
from zividsamples.save_load_matrix import assert_affine_matrix_and_save


def _args() -> argparse.Namespace:
    """Parse command line options for the script.

    Returns:
        Arguments from the user
    """
    parser = argparse.ArgumentParser(description="Multi-camera calibration from ZDF files")
    parser.add_argument(
        "-zdf",
        nargs="+",
        required=True,
        help="List of ZDF files which contain captures of checker boards",
        type=Path,
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        required=True,
        help="Transformation Matrices Files will be saved into this directory",
        type=Path,
    )

    return parser.parse_args()


def get_detections_from_zdf(zdf_file_list: List[Path]) -> List[Tuple[str, zivid.calibration.DetectionResult]]:
    detections_list = []

    for file_name in zdf_file_list:
        print(f"Reading {file_name} point cloud")
        frame = zivid.Frame(file_name)
        serial = frame.camera_info.serial_number

        print("Detecting checkerboard in point cloud...")
        detection_result = zivid.calibration.detect_calibration_board(frame)
        if detection_result:
            detections_list.append((serial, detection_result))
        else:
            raise RuntimeError("Could not detect checkerboard. Please ensure it is visible from all cameras.")

    return detections_list


def run_multi_camera_calibration(
    detections_list: List[Tuple[str, zivid.calibration.DetectionResult]], transformation_matrices_save_path: Path
) -> None:
    detection_results_list = [detection_result for _, detection_result in detections_list]

    results = zivid.calibration.calibrate_multi_camera(detection_results_list)

    if results:
        print("Multi-camera calibration OK.")
        transforms = results.transforms()
        residuals = results.residuals()
        for i, (serial, _) in enumerate(detections_list):
            assert_affine_matrix_and_save(transforms[i], transformation_matrices_save_path / f"{serial}.yaml")

            print(f"Pose of camera {serial} in first camera {detections_list[0][0]} frame:\n" f"{transforms[i]}")
            print(residuals[i])
    else:
        print("Multi-camera calibration FAILED.")


def main() -> None:
    args = _args()

    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    detections = get_detections_from_zdf(zdf_file_list=args.zdf)
    run_multi_camera_calibration(detections, transformation_matrices_save_path=args.output_dir)


if __name__ == "__main__":
    main()
