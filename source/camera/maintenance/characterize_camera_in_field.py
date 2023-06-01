"""
Check the dimension trueness of a Zivid camera.

This example shows how to verify the local dimension trueness of a camera.
If the trueness is much worse than expected, the camera may have been damaged by
shock in shipping in handling. If so, look at the correct_camera_in_field sample sample.

Note: This example uses experimental SDK features, which may be modified, moved, or deleted in the future without notice.

"""

import argparse
import csv
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Union

import zivid
from zivid.experimental import calibration


def _options() -> argparse.Namespace:
    """Function to read user arguments


    Returns:
        Argument from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--csv-path",
        required=False,
        type=Path,
        default=Path(__file__).parent / "verification_data.csv",
        help="Path to the verification data",
    )

    return parser.parse_args()


@dataclass
class RandomCaptureCycle:
    min_captures: int = 3
    max_captures: int = 15
    min_capture_interval: timedelta = timedelta(seconds=5)
    max_capture_interval: timedelta = timedelta(seconds=15)

    def __post_init__(self) -> None:
        random.seed(datetime.now().microsecond)

    def capture_interval(self) -> timedelta:
        return timedelta(
            seconds=random.uniform(self.min_capture_interval.total_seconds(), self.max_capture_interval.total_seconds())
        )

    def number_of_captures(self) -> int:
        return random.randint(self.min_captures, self.max_captures)


@dataclass
class StandbyCycle:
    total_duration: timedelta = timedelta(minutes=30)
    sample_interval: timedelta = timedelta(seconds=30)


@dataclass
class VerificationAndState:
    verification: calibration.CameraVerification
    info: zivid.CameraInfo
    state: zivid.CameraState
    time: str

    def __str__(self) -> str:
        return f"""\
Time: {self.time}
Pose: {'x':>4}:{self.verification.position()[0]:>8.3f} mm{'y':>4}:{self.verification.position()[1]:>8.3f} mm{'z':>4}:{self.verification.position()[2]:>8.3f} mm
Estimated dimension trueness: {self.verification.local_dimension_trueness()*100:.3f}%
Temperatures:
    {'DMD:':<9}{self.state.temperature.dmd:>6.1f}\u00b0C
    {'Lens:':<9}{self.state.temperature.lens:>6.1f}\u00b0C
    {'LED:':<9}{self.state.temperature.led:>6.1f}\u00b0C
    {'PCB:':<9}{self.state.temperature.pcb:>6.1f}\u00b0C
    {'General:':<9}{self.state.temperature.general:>6.1f}\u00b0C
"""

    def as_dict(self) -> dict:
        return {
            "time": self.time,
            "position.x": self.verification.position()[0],
            "position.y": self.verification.position()[1],
            "position.z": self.verification.position()[2],
            "dimension_trueness": self.verification.local_dimension_trueness(),
            "temperature.DMD": self.state.temperature.dmd,
            "temperature.Lens": self.state.temperature.lens,
            "temperature.LED": self.state.temperature.led,
            "temperature.PCB": self.state.temperature.pcb,
            "temperature.General": self.state.temperature.general,
        }


def _measure(camera: zivid.Camera) -> VerificationAndState:
    time_string = time.strftime("%Y-%m-%d %H:%M:%S")
    detection_result = calibration.detect_feature_points(camera)
    camera_state = camera.state
    infield_input = calibration.InfieldCorrectionInput(detection_result)
    if not infield_input.valid():
        raise RuntimeError(
            f"Capture not valid for infield verification! Feedback: {infield_input.status_description()}"
        )
    return VerificationAndState(
        verification=calibration.verify_camera(infield_input),
        info=camera.info,
        state=camera_state,
        time=time_string,
    )


def append_to_csv_file(csv_path: Path, verification_data: VerificationAndState) -> None:
    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=verification_data.as_dict().keys())
        writer.writerow(verification_data.as_dict())


def start_csv_file(
    csv_path: Path, verification_data: VerificationAndState, camera_correction_timestamp: Union[datetime, None]
) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=verification_data.as_dict().keys())
        csvfile.write("\n".join([f"# {line}" for line in str(verification_data.info).splitlines()]))
        csvfile.write("\n")
        if camera_correction_timestamp:
            csvfile.write(
                f"# Timestamp of current camera correction: {camera_correction_timestamp.strftime(r'%Y-%m-%d %H:%M:%S')}"
            )
            csvfile.write("\n")
        else:
            csvfile.write("# This camera has no infield correction written to it.")
            csvfile.write("\n")
        writer.writeheader()


def standby_loop(camera: zivid.Camera, csv_path: Path, standby_cycle: StandbyCycle) -> None:
    end_time = datetime.now() + standby_cycle.total_duration
    start_of_loop = datetime.now()
    while start_of_loop < end_time:
        verification_data = _measure(camera)
        print(verification_data)
        append_to_csv_file(csv_path, verification_data)
        time.sleep((standby_cycle.sample_interval - (datetime.now() - start_of_loop)).total_seconds())
        start_of_loop = datetime.now()


def random_capture_loop(camera: zivid.Camera, csv_path: Path, timing: RandomCaptureCycle) -> None:
    for _ in range(timing.number_of_captures()):
        verification_data = _measure(camera)
        print(verification_data)
        append_to_csv_file(csv_path, verification_data)
        time.sleep(timing.capture_interval().total_seconds())


def _main() -> None:
    user_input = _options()

    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    camera_correction_timestamp = (
        calibration.camera_correction_timestamp(camera) if calibration.has_camera_correction(camera) else None
    )
    initial_verification = _measure(camera)
    print(initial_verification)
    start_csv_file(user_input.csv_path, initial_verification, camera_correction_timestamp)

    standby_cycle = StandbyCycle()
    random_capture_cycle = RandomCaptureCycle()
    while True:
        standby_loop(camera, user_input.csv_path, standby_cycle)
        random_capture_loop(camera, user_input.csv_path, random_capture_cycle)


if __name__ == "__main__":
    _main()
