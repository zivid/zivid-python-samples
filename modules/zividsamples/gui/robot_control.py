from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict

from PyQt5.QtCore import QObject, pyqtSignal
from zividsamples.gui.robot_configuration import RobotConfiguration
from zividsamples.transformation_matrix import TransformationMatrix


@dataclass
class RobotTarget:
    name: str
    pose: TransformationMatrix


class RobotControlReadOnly(QObject):
    information_update = pyqtSignal(str)

    def __init__(self, robot_configuration: RobotConfiguration) -> None:
        super().__init__()
        self.robot_configuration = robot_configuration

    @abstractmethod
    def get_pose(self) -> RobotTarget:
        raise NotImplementedError

    @abstractmethod
    def connect(self):
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        raise NotImplementedError

    def is_read_only(self) -> bool:
        return True


class RobotControl(RobotControlReadOnly):
    target_pose_updated = pyqtSignal(RobotTarget)

    def __init__(self, robot_configuration: RobotConfiguration) -> None:
        super().__init__(robot_configuration)
        self.targets: Dict[str, RobotTarget] = {}

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
    def is_moving(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def move_l(self, target: RobotTarget) -> None:
        raise NotImplementedError

    @abstractmethod
    def move_j(self, target: RobotTarget) -> None:
        raise NotImplementedError

    def is_read_only(self) -> bool:
        return False
