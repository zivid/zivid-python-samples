"""
Sample showing how to use a context manager with Zivid Application and safely return processed data.

This pattern avoids returning any Zivid objects outside the Application scope. It ensures all resources are
properly released by returning only NumPy arrays (e.g., point cloud data). This is important because using
Zivid objects after the Application is destroyed can lead to undefined behavior.

"""

from typing import Tuple

import numpy as np
import zivid
from zividsamples.display import display_pointcloud
from zividsamples.paths import get_sample_data_path


def load_point_cloud_as_numpy() -> Tuple[np.ndarray, np.ndarray]:
    """
    Creates a Zivid Application inside a context manager, reads a frame, and returns point cloud data
    as NumPy arrays. No Zivid objects are returned or persist outside this function.

    Returns:
        Tuple[np.ndarray, np.ndarray]: A tuple containing the XYZ point cloud (float32) and RGBA color data (uint8).

     Raises:
        RuntimeError: If point cloud data could not be extracted.

    """
    with zivid.Application():
        print("Zivid Application started")

        data_file = get_sample_data_path() / "Zivid3D.zdf"
        print(f"Reading ZDF frame from file: {data_file}")

        with zivid.Frame(data_file) as frame:
            with frame.point_cloud() as point_cloud:
                xyz = point_cloud.copy_data("xyz")
                rgba = point_cloud.copy_data("rgba_srgb")

                if xyz is None or rgba is None:
                    raise RuntimeError("Point cloud data could not be extracted")

    print("Zivid Application released")
    return xyz, rgba


def use_zivid_application_with_context() -> None:
    """Calls the processing function multiple times, demonstrating safe use of Zivid context manager."""
    for i in range(2):
        print(f"\nIteration {i + 1}")
        xyz, rgba = load_point_cloud_as_numpy()
        display_pointcloud(xyz, rgba[:, :, 0:3])  # Only RGB used for display


if __name__ == "__main__":
    use_zivid_application_with_context()
