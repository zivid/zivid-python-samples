"""
Correct the dimension trueness of a Zivid camera.

This example shows how to perform In-field correction. This involves gathering data from
a compatible calibration board at several distances, calculating an updated camera
correction, and optionally saving that new correction to the camera.

The correction will persist on the camera even though the camera is power-cycled or
connected to a different PC. After saving a correction, it will automatically be used any
time that camera captures a new point cloud.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.
"""

import zivid
from zivid.experimental import calibration


def yes_no_prompt(question: str):
    while True:
        response = input(question)
        if response in ["n", "N"]:
            return False
        if response in ["y", "Y"]:
            return True
        print("Invalid response. Please respond with either 'y' or 'n'.")


def collect_dataset(camera: zivid.camera):

    dataset = []
    print("Please point the camera at a Zivid in-field calibration board. ")

    print_line = "------------------------------------------------------------------------"
    while True:
        print(print_line)
        if yes_no_prompt("Capture (y) or finish (n)? "):
            print("Capturing calibration board")
            detection_result = calibration.detect_feature_points(camera)
            infield_input = calibration.InfieldCorrectionInput(detection_result)

            if infield_input.valid():
                dataset.append(infield_input)
            else:
                print("****INVALID****")
                print(f"Feedback: {infield_input.status_description()}")

            print(print_line)
        else:
            print("End of capturing stage.")
            print(print_line)
            break

        print(f"You have collected {len(dataset)} valid measurements so far.")
    return dataset


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    # Gather data
    dataset = collect_dataset(camera)

    # Calculate infield correciton
    print(f"Collected {len(dataset)} valid measurements.")
    print("Computing new camera correction...")
    correction = calibration.compute_camera_correction(dataset)
    accuracy_estimate = correction.accuracy_estimate()

    print(
        "If written to the camera, this correction can be expected to yield a dimension accuracy of ",
        f"{accuracy_estimate.dimension_accuracy()*100:.3f} or better in the range of z=[{accuracy_estimate.z_min():.3f}, {accuracy_estimate.z_max():.3f}] across the full FOV.",
        "Accuracy close to where the correction data was collected is likely better.",
    )

    # Optionally save to camera
    if yes_no_prompt("Save to camera? "):
        print("Writing correction to camera")
        calibration.write_camera_correction(camera, correction)
        print("Success")


if __name__ == "__main__":
    _main()
