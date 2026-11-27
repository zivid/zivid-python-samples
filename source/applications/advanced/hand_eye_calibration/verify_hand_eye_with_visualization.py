"""
Verify hand-eye calibration by transforming all dataset point clouds and visualizing them overlapped.

Running this sample requires a hand-eye session (robot poses, captures and the calibrated transform),
such as one produced by the Zivid Studio Hand-Eye GUI or by the robodk_hand_eye_calibration and
ur_hand_eye_calibration samples. Datasets from older versions of those samples (img01.zdf, pos01.yaml)
are not sessions; regenerate them with the current samples.

The transformation will be done to different robot frames, depending on the type of calibration in
the session:
- eye-to-hand: The point clouds are transformed to the robot end-effector frame
- eye-in-hand: The point clouds are transformed to the robot base frame

The Hand-Eye calibration is good if the visualized calibration objects overlap accurately.

Tip: This sample saves the point clouds in PLY format in the same directory where this sample is
stored. You can open the PLY point clouds in MeshLab for visual inspection.

For more information on verifying Hand-Eye calibration, check out this tutorial:
https://support.zivid.com/en/latest/camera/academy/applications/hand-eye/hand-eye-calibration-verification.html

"""

import argparse
import colorsys
from pathlib import Path
from typing import List

import numpy as np
import zivid
from zivid.experimental.point_cloud_export import export_unorganized_point_cloud
from zivid.experimental.point_cloud_export.file_format import PLY, ColorSpace
from zividsamples.display import display_pointcloud
from zividsamples.hand_eye_session import HandEyeSession


def _distinct_colors(number_of_colors: int) -> List[List[int]]:
    """Generate n visually distinct RGB colors.

    Args:
        number_of_colors: Number of distinct colors to generate

    Returns:
        List of distinct RGB colors

    """

    return [
        [round(c * 255) for c in colorsys.hsv_to_rgb(i / number_of_colors, 0.75, 0.9)] for i in range(number_of_colors)
    ]


def _options() -> argparse.Namespace:
    """Function for taking in arguments from user.

    Returns:
        Argument from user

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-path",
        type=Path,
        required=True,
        help="Path to the Hand-Eye session folder",
    )

    return parser.parse_args()


def _main() -> None:
    # Application class must be initialized before using other Zivid classes.
    app = zivid.Application()  # noqa: F841  # pylint: disable=unused-variable

    args = _options()

    session = HandEyeSession.open(args.input_path)
    pose_pairs = session.load_pose_pairs()
    if len(pose_pairs) < 2:
        raise RuntimeError(f"Need at least two pose pairs to verify, found {len(pose_pairs)}")

    hand_eye_transform = session.load_hand_eye_transform()
    print(f"Verifying {'eye-in-hand' if session.eye_in_hand else 'eye-to-hand'} session: {session.name}")

    stitched_point_cloud = zivid.UnorganizedPointCloud()
    for index, (pose_pair, rgb_color) in enumerate(zip(pose_pairs, _distinct_colors(len(pose_pairs)), strict=True)):
        percentage = int(100 * index / len(pose_pairs))
        print(f"{index} / {len(pose_pairs)} - {percentage:>3}%")

        point_cloud = zivid.Frame(pose_pair.frame_path).point_cloud()

        # Transforms point cloud to the robot base frame (eye-in-hand) or end-effector frame (eye-to-hand)
        if session.eye_in_hand:
            point_cloud.transform(np.matmul(pose_pair.robot_pose, hand_eye_transform))
        else:
            point_cloud.transform(np.matmul(np.linalg.inv(pose_pair.robot_pose), hand_eye_transform))

        transformed_point_cloud = point_cloud.to_unorganized_point_cloud()

        # Saving point cloud to PLY file
        export_unorganized_point_cloud(
            transformed_point_cloud,
            PLY(f"pose_{pose_pair.pose_id:02d}.ply", layout=PLY.Layout.unordered, color_space=ColorSpace.srgb),
        )

        # Setting monochrome color and adding to stitched point cloud
        transformed_point_cloud.paint_uniform_color(rgb_color + [128])
        stitched_point_cloud.extend(transformed_point_cloud)

    print(f"{len(pose_pairs)} / {len(pose_pairs)} - 100%")
    print("\nAll done!\n")

    print("Visualizing transformed point clouds\n")
    display_pointcloud(stitched_point_cloud)


if __name__ == "__main__":
    _main()
