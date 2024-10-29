from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict

from PyQt5.QtCore import QObject, pyqtSignal
from zividsamples.transformation_matrix import TransformationMatrix


@dataclass
class RobotTarget:
    name: str
    pose: TransformationMatrix


class RobotControl(QObject):
    information_update = pyqtSignal(str)
    target_pose_updated = pyqtSignal(RobotTarget)
    targets: Dict[str, RobotTarget]

    def __init__(self) -> None:
        super().__init__()
        self.targets = {}

    @abstractmethod
    def get_pose(self) -> RobotTarget:
        raise NotImplementedError

    @abstractmethod
    def get_custom_target(self, custom_pose: TransformationMatrix) -> RobotTarget:
        raise NotImplementedError

    @abstractmethod
    def get_safe_waypoint(self) -> RobotTarget:
        raise NotImplementedError

    @abstractmethod
    def get_target_by_id(self, target_id: int) -> RobotTarget:
        raise NotImplementedError

    @abstractmethod
    def get_number_of_regular_targets(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def is_home(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def connect(self, ip_address: str):
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        raise NotImplementedError

    @abstractmethod
    def is_moving(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def move_l(self, target: RobotTarget) -> None:
        raise NotImplementedError

    @abstractmethod
    def move_j(self, target: RobotTarget) -> None:
        raise NotImplementedError
