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

from typing import List

import zivid
import zivid.experimental.calibration


def _yes_no_prompt(question: str) -> bool:
    """Gets a yes or no answer to a given question.

    Args:
        question: A question that requires a yes or no answer

    Returns:
        Bool that is True for 'y' and 'Y' and False for 'n' or 'N'

    """
    while True:
        response = input(f"{question} (y/n): ")
        if response in {"y", "Y"}:
            return True
        if response in {"n", "N"}:
            return False
        print("Invalid response. Please respond with either 'y' or 'n'.")


def _collect_dataset(camera: zivid.Camera) -> List[zivid.experimental.calibration.InfieldCorrectionInput]:
    """Collects input-data needed by infield verification and correction function.

    Args:
        camera: Zivid camera instance

    Returns:
        dataset: Contains input-data needed by infield verification and correction function

    """
    dataset = []
    print("Please point the camera at a Zivid infield calibration board. ")

    print_line = "------------------------------------------------------------------------"
    while True:
        print(print_line)
        if _yes_no_prompt("Capture (y) or finish (n)? "):
            print("Capturing calibration board")
            detection_result = zivid.calibration.detect_calibration_board(camera)
            if detection_result.valid():
                infield_input = zivid.experimental.calibration.InfieldCorrectionInput(detection_result)

                if infield_input.valid():
                    dataset.append(infield_input)
                else:
                    print("****Invalid Input****")
                    print(f"Feedback: {infield_input.status_description()}")
            else:
                print("****Failed Detection****")
                print(f"Feedback: {detection_result.status_description()}")

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
    dataset = _collect_dataset(camera)

    # Calculate infield correciton
    print(f"Collected {len(dataset)} valid measurements.")
    if len(dataset) > 0:
        print("Computing new camera correction...")
        correction = zivid.experimental.calibration.compute_camera_correction(dataset)
        accuracy_estimate = correction.accuracy_estimate()

        print(
            "If written to the camera, this correction can be expected to yield a dimension accuracy error of",
            f"{accuracy_estimate.dimension_accuracy() * 100:.3f}% or better in the range of z=[{accuracy_estimate.z_min():.3f}, {accuracy_estimate.z_max():.3f}] across the full FOV.",
            "Accuracy close to where the correction data was collected is likely better.",
        )

        # Optionally save to camera
        if _yes_no_prompt("Save to camera?"):
            print("Writing correction to camera")
            zivid.experimental.calibration.write_camera_correction(camera, correction)
            print("Success")


if __name__ == "__main__":
    _main()
