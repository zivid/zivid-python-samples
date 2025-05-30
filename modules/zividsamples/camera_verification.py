import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import zivid
from zivid.experimental import calibration


@dataclass
class TemperatureAndTime:
    temperature: float
    time_stamp: datetime


@dataclass
class RandomCaptureCycle:
    min_capture_interval: timedelta = timedelta(seconds=3)
    max_capture_interval: timedelta = timedelta(seconds=6)

    def __post_init__(self) -> None:
        random.seed(datetime.now().microsecond)

    def capture_interval(self) -> timedelta:
        return timedelta(
            seconds=random.uniform(self.min_capture_interval.total_seconds(), self.max_capture_interval.total_seconds())
        )


@dataclass
class VerificationAndState:
    verification: Optional[calibration.CameraVerification]
    state: zivid.CameraState
    time: datetime
    info: zivid.CameraInfo

    def _position(self):
        return self.verification.position() if self.verification else (None, None, None)

    def distance(self):
        return self._position()[2]

    def local_dimension_trueness(self):
        return self.verification.local_dimension_trueness() if self.verification else None

    def __str__(self) -> str:
        local_dimension_trueness = self.local_dimension_trueness()
        local_dimension_trueness_str = f"{local_dimension_trueness * 100:.3f}" if local_dimension_trueness else "NA"
        return f"""\
Time: {self.time}
Pose: {'x':>4}:{self._position()[0]:>8.3f} mm{'y':>4}:{self._position()[1]:>8.3f} mm{'z':>4}:{self._position()[2]:>8.3f} mm
Estimated dimension trueness: {local_dimension_trueness_str}
Temperatures:
    {'DMD:':<9}{self.state.temperature.dmd:>6.1f}\u00b0C
    {'Lens:':<9}{self.state.temperature.lens:>6.1f}\u00b0C
    {'LED:':<9}{self.state.temperature.led:>6.1f}\u00b0C
    {'PCB:':<9}{self.state.temperature.pcb:>6.1f}\u00b0C
    {'General:':<9}{self.state.temperature.general:>6.1f}\u00b0C
"""


def capture_and_measure_from_frame(frame: zivid.Frame) -> VerificationAndState:
    detection_result = zivid.calibration.detect_calibration_board(frame)
    infield_input = calibration.InfieldCorrectionInput(detection_result)
    if not infield_input.valid():
        raise RuntimeError(
            f"Capture not valid for infield verification! Feedback: {infield_input.status_description()}"
        )
    return VerificationAndState(
        verification=calibration.verify_camera(infield_input),
        info=frame.camera_info,
        state=frame.state,
        time=frame.info.time_stamp,
    )


def capture_and_measure(camera: zivid.Camera) -> VerificationAndState:
    frame = zivid.calibration.capture_calibration_board(camera)
    return capture_and_measure_from_frame(frame)
