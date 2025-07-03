"""
Use captures of a calibration object to generate transformation matrices to a single coordinate frame, from connected cameras.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List

import zivid
from zividsamples.save_load_matrix import assert_affine_matrix_and_save


def _args() -> argparse.Namespace:
    """Parse command line options for the script.

    Returns:
        Arguments from the user
    """
    parser = argparse.ArgumentParser(description="Multi-camera calibration using Zivid cameras.")
    parser.add_argument(
        "transformation_matrices_save_path",
        help="Path where the transformation matrices YAML files will be saved",
        type=Path,
    )
    return parser.parse_args()


def connect_to_all_available_cameras(cameras: List[zivid.Camera]) -> List[zivid.Camera]:
    connected_cameras = []
    for camera in cameras:
        if camera.state.status == zivid.CameraState.Status.available:
            print(f"Connecting to camera: {camera.info.serial_number}")
            camera.connect()
            connected_cameras.append(camera)
        else:
            print(f"Camera {camera.info.serial_number} is not available. " f"Camera status: {camera.state.status}")
    return connected_cameras


@dataclass
class Detection:
    serial_number: str
    detection_result: zivid.calibration.DetectionResult


def get_detections(connected_cameras: List[zivid.Camera]) -> List[Detection]:
    detections_list = []
    for camera in connected_cameras:
        serial = camera.info.serial_number
        print(f"Capturing frame with camera: {serial}")
        frame = zivid.calibration.capture_calibration_board(camera)
        print("Detecting checkerboard in point cloud")
        detection_result = zivid.calibration.detect_calibration_board(frame)
        if detection_result:
            detections_list.append(Detection(serial, detection_result))
        else:
            raise RuntimeError("Could not detect checkerboard. Please ensure it is visible from all cameras.")
    return detections_list


def run_multi_camera_calibration(detections_list: List[zivid.Camera], transformation_matrices_save_path: Path) -> None:
    detection_results_list = [d.detection_result for d in detections_list]
    results = zivid.calibration.calibrate_multi_camera(detection_results_list)

    if results:
        print("Multi-camera calibration OK.")
        transforms = results.transforms()
        residuals = results.residuals()
        for i, transform in enumerate(transforms):
            assert_affine_matrix_and_save(
                transform, transformation_matrices_save_path / f"{detections_list[i].serial_number}.yaml"
            )
            print(
                f"Pose of camera {detections_list[i].serial_number} in first camera "
                f"{detections_list[0].serial_number} frame:\n{transform}"
            )
            print(residuals[i])
    else:
        print("Multi-camera calibration FAILED.")


def main() -> None:
    args = _args()

    app = zivid.Application()
    print("Finding cameras")
    cameras = app.cameras()
    print(f"Number of cameras found: {len(cameras)}")

    connected_cameras = connect_to_all_available_cameras(cameras)
    if len(connected_cameras) < 2:
        raise RuntimeError("At least two cameras need to be connected")
    print(f"Number of connected cameras: {len(connected_cameras)}")

    detections = get_detections(connected_cameras)
    run_multi_camera_calibration(detections, args.transformation_matrices_save_path)


if __name__ == "__main__":
    main()
