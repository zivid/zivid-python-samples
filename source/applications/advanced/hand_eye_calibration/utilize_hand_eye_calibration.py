"""
Transform single data point or entire point cloud from camera frame to robot base frame using Hand-Eye calibration
matrix.

This example shows how to utilize the result of Hand-Eye calibration to transform either (picking) point coordinates
or the entire point cloud from the camera frame to the robot base frame.

For both Eye-To-Hand and Eye-In-Hand, there is a Zivid gem placed approx. 500 mm away from the robot base (see below).
The (picking) point is the Zivid gem centroid, defined as image coordinates in the camera frame and hard-coded
in this code example. Open the ZDF files in Zivid Studio to inspect the gem's 2D and corresponding 3D coordinates.

Eye-To-Hand
- ZDF file: ZividGemEyeToHand.zdf
- 2D image coordinates: (1035,255)
- Corresponding 3D coordinates: (37.77 -145.92 1227.1)
- Corresponding 3D coordinates (robot base frame): (-12.4  514.37 -21.79)

Eye-In-Hand:
- ZDF file: ZividGemEyeInHand.zdf
- 2D image coordinates: (1460,755)
- Corresponding 3D coordinates (camera frame): (83.95  28.84 305.7)
- Corresponding 3D coordinates (robot base frame): (531.03  -5.44 164.6)

For verification, check that the Zivid gem centroid 3D coordinates are the same as above after the transformation.

The YAML files for this sample can be found under the main instructions for Zivid samples.

"""

import numpy as np
import zivid
from sample_utils.paths import get_sample_data_path
from sample_utils.save_load_matrix import load_and_assert_affine_matrix


def _main() -> None:

    with zivid.Application():

        np.set_printoptions(precision=2)

        while True:
            robot_camera_configuration = input(
                "Enter type of calibration, eth (for eye-to-hand) or eih (for eye-in-hand):"
            ).strip()

            if robot_camera_configuration.lower() == "eth":

                file_name = "ZividGemEyeToHand.zdf"

                # The (picking) point is defined as image coordinates in camera frame. It is hard-coded for the
                # ZividGemEyeToHand.zdf (1035,255) X: 37.77 Y: -145.92 Z: 1227.1
                image_coordinate_x = 1035
                image_coordinate_y = 255

                eye_to_hand_transform_file_path = get_sample_data_path() / "EyeToHandTransform.yaml"

                print("Reading camera pose in robot base frame (result of eye-to-hand calibration)")
                transform_base_to_camera = load_and_assert_affine_matrix(eye_to_hand_transform_file_path)

                break

            if robot_camera_configuration.lower() == "eih":

                file_name = "ZividGemEyeInHand.zdf"

                # The (picking) point is defined as image coordinates in camera frame. It is hard-coded for the
                # ZividGemEyeInHand.zdf (1460,755) X: 83.95 Y: 28.84 Z: 305.7
                image_coordinate_x = 1460
                image_coordinate_y = 755

                eye_in_hand_transform_file_path = get_sample_data_path() / "EyeInHandTransform.yaml"
                robot_transform_file_path = get_sample_data_path() / "RobotTransform.yaml"

                print("Reading camera pose in flange (end-effector) frame (result of eye-in-hand calibration)")
                transform_flange_to_camera = load_and_assert_affine_matrix(eye_in_hand_transform_file_path)

                print("Reading flange (end-effector) pose in robot base frame")
                transform_base_to_flange = load_and_assert_affine_matrix(robot_transform_file_path)

                print("Computing camera pose in robot base frame")
                transform_base_to_camera = np.matmul(transform_base_to_flange, transform_flange_to_camera)

                break

            print("Entered unknown Hand-Eye calibration type")

        data_file = get_sample_data_path() / file_name
        print(f"Reading point cloud from file: {data_file}")
        frame = zivid.Frame(data_file)
        point_cloud = frame.point_cloud()

        while True:
            command = input("Enter command, s (to transform single point) or p (to transform point cloud): ").strip()

            if command.lower() == "s":

                print("Transforming single point")

                xyz = point_cloud.copy_data("xyz")

                point_in_camera_frame = np.array(
                    [
                        xyz[image_coordinate_y, image_coordinate_x, 0],
                        xyz[image_coordinate_y, image_coordinate_x, 1],
                        xyz[image_coordinate_y, image_coordinate_x, 2],
                        1,
                    ]
                )
                print(f"Point coordinates in camera frame: {point_in_camera_frame[0:3]}")

                print("Transforming (picking) point from camera to robot base frame")
                point_in_base_frame = np.matmul(transform_base_to_camera, point_in_camera_frame)

                print(f"Point coordinates in robot base frame: {point_in_base_frame[0:3]}")

                break

            if command.lower() == "p":

                print("Transforming point cloud")

                point_cloud.transform(transform_base_to_camera)

                save_file = "ZividGemTransformed.zdf"
                print(f"Saving frame to file: {save_file}")
                frame.save(save_file)

                break

            print("Entered unknown command")


if __name__ == "__main__":
    _main()
