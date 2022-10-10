"""
Read intrinsic parameters from the Zivid camera (OpenCV model).

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

import zivid
from zivid.experimental import calibration


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Getting camera intrinsics")
    intrinsics = calibration.intrinsics(camera)
    print(intrinsics)

    print("Separated camera intrinsic parameters:")

    print(f"    CX: {intrinsics.camera_matrix.cx}")
    print(f"    CY: {intrinsics.camera_matrix.cy}")
    print(f"    FX: {intrinsics.camera_matrix.fx}")
    print(f"    FY: {intrinsics.camera_matrix.fy}")

    print(f"    K1: {intrinsics.distortion.k1}")
    print(f"    K2: {intrinsics.distortion.k2}")
    print(f"    K3: {intrinsics.distortion.k3}")
    print(f"    P1: {intrinsics.distortion.p1}")
    print(f"    P2: {intrinsics.distortion.p2}")

    output_file = "Intrinsics.yml"
    print(f"Saving camera intrinsics to file: {output_file}")
    intrinsics.save(output_file)


if __name__ == "__main__":
    _main()
