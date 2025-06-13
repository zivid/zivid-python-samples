"""
Transform point cloud data from millimeters to meters.

The ZDF file for this sample can be found under the main instructions for Zivid samples.

"""

import numpy as np
import zivid
from zividsamples.paths import get_sample_data_path


def _main() -> None:
    # Application class must be initialized before using other Zivid classes.
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    data_file = get_sample_data_path() / "CalibrationBoardInCameraOrigin.zdf"
    print(f"Reading {data_file} point cloud")

    frame = zivid.Frame(data_file)
    point_cloud = frame.point_cloud()

    transform_millimeters_to_meters = np.array(
        [[0.001, 0, 0, 0], [0, 0.001, 0, 0], [0, 0, 0.001, 0], [0, 0, 0, 1]], dtype=np.float32
    )

    print("Transforming point cloud from mm to m")
    point_cloud.transform(transform_millimeters_to_meters)

    transformed_file = "FrameInMeters.zdf"
    print(f"Saving transformed point cloud to file: {transformed_file}")
    frame.save(transformed_file)


if __name__ == "__main__":
    _main()
