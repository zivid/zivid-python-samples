"""
Utilize the result of eye-in-hand calibration to transform (picking) point
coordinates from the camera frame to the robot base frame.
"""

from pathlib import Path
import numpy as np
import cv2


def _read_transform(file_name):
    """Read transformation matrix from a YAML file.

    Args:
        file_name: Path to the YAML file.

    Returns:
        transform: Transformation matrix.

    """

    file_storage = cv2.FileStorage(file_name, cv2.FILE_STORAGE_READ)
    transform = file_storage.getNode("PoseState").mat()
    file_storage.release()

    return transform


def _main():

    np.set_printoptions(precision=2)

    # Define (picking) point in camera frame
    point_in_camera_frame = np.array([81.2, 18.0, 594.6, 1])

    print(f"Point coordinates in camera frame: {point_in_camera_frame[0:3]}")

    # Reading camera pose in end-effector frame (result of eye-in-hand calibration)
    transform_end_effector_to_camera = _read_transform(
        str(Path("eyeInHandTransform.yaml"))
    )

    # Reading end-effector pose in robot base frame
    transform_base_to_end_effector = _read_transform(str(Path("robotTransform.yaml")))

    # Computing camera pose in robot base frame
    transform_base_to_camera = np.matmul(
        transform_base_to_end_effector, transform_end_effector_to_camera
    )

    # Computing (picking) point in robot base frame
    point_in_base_frame = np.matmul(transform_base_to_camera, point_in_camera_frame)

    print(f"Point coordinates in robot base frame: {point_in_base_frame[0:3]}")


if __name__ == "__main__":
    _main()
