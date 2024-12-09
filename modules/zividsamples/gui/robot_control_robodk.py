import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import robodk
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from robodk.robolink import ITEM_TYPE_ROBOT, RUNMODE_RUN_ROBOT, Item, Robolink, TargetReachError
from robodk.robomath import Mat
from zividsamples.gui.robot_control import RobotControl, RobotTarget
from zividsamples.transformation_matrix import Distance, TransformationMatrix


class RobotControlRoboDK(RobotControl):
    rdk: Optional[Robolink]
    robot_handle: Optional[Any]
    information_update = pyqtSignal(str)
    custom_target: Item
    robodk_targets: Dict[str, Item] = {}
    target_name_mapping: Dict[str, str] = {}
    current_target: RobotTarget = RobotTarget(name="CustomTarget", pose=TransformationMatrix())
    actual_pose: Optional[RobotTarget] = None
    robot_moving: bool = False
    translation_tolerance: float = 2.0
    rotation_tolerance: float = 1e-3

    def __init__(self):
        super().__init__()
        self.robot_handle = None

    def _robodk_pose_to_transformation_matrix(self, pose: Any) -> TransformationMatrix:
        matrix = np.asarray(pose).transpose()
        return TransformationMatrix.from_matrix(matrix)

    def _map_to_existing_target(self, input_transformation_matrix: TransformationMatrix) -> RobotTarget:
        closest_target_name = "CustomTarget"
        min_distance = Distance(translation=float("inf"), rotation=float("inf"))
        for name, target in self.targets.items():
            if name == "CustomTarget":
                continue
            target_transformation_matrix = target.pose
            distance = input_transformation_matrix.distance_to(target_transformation_matrix)
            if distance.translation < (min_distance.translation + self.translation_tolerance):
                if distance.rotation < (min_distance.rotation + self.rotation_tolerance):
                    min_distance = distance
                    closest_target_name = name

        if min_distance.translation < self.translation_tolerance and min_distance.rotation < self.rotation_tolerance:
            return RobotTarget(name=closest_target_name, pose=input_transformation_matrix)
        return RobotTarget(name="CustomTarget", pose=input_transformation_matrix)

    def get_pose(self) -> RobotTarget:
        assert self.robot_handle is not None
        if self.robot_moving:
            return self.current_target
        self.retry_function_call(self.robot_handle.Joints)
        actual_pose = self.retry_function_call(self.robot_handle.Pose)
        self.retry_function_call(self.custom_target.setPose, actual_pose)
        actual_transformation_matrix = self._robodk_pose_to_transformation_matrix(actual_pose)

        self.current_target = self._map_to_existing_target(actual_transformation_matrix)

        self.actual_pose = self.current_target

        return self.current_target

    def is_home(self) -> bool:
        if self.actual_pose is not None:
            return self.actual_pose.name in ("Home", "Target_0")
        return False

    def get_custom_target(self, custom_pose: TransformationMatrix) -> RobotTarget:
        assert self.robot_handle is not None
        actual_pose = self.robot_handle.Pose()
        self.custom_target.setPose(actual_pose)
        self.current_target = self._map_to_existing_target(custom_pose)
        return self.current_target

    def get_safe_waypoint(self) -> RobotTarget:
        return self.targets["SafeWaypoint"]

    def get_target_by_id(self, target_id: int) -> RobotTarget:
        return self.targets[f"Target_{target_id}"]

    def get_number_of_regular_targets(self) -> int:
        regular_targets = [
            target_key
            for target_key in self.robodk_targets.keys()
            if target_key.startswith("Target") or target_key.startswith("HE-Pose")
        ]
        return len(regular_targets)

    def is_moving(self) -> bool:
        return self.robot_moving

    def disconnect(self):
        if self.rdk is not None:
            self.rdk.Disconnect()

    def setup_station(self):
        assert self.rdk
        active_station = self.rdk.ActiveStation()
        print(f"Currently active station: {active_station.Name()}")
        if len(self.rdk.ItemList()) > 1:
            reply = QMessageBox.question(
                None,
                "Active Station",
                f"The currently active station is:\n\t{active_station.Name()}\n\nDo you want to use this station?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                return
            reply = QMessageBox.question(
                None,
                "Save Station",
                "Do you want to save the current station before proceeding?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                station_backup_path = QFileDialog.getSaveFileName(
                    caption="Save Station",
                    directory=Path.home().joinpath("your_station_backup.rdk").resolve().as_posix(),
                    filter="RoboDK Station (*.rdk)",
                )[0]
                self.rdk.Save(station_backup_path)
            self.rdk.CloseStation()
        station_path, _ = QFileDialog.getOpenFileName(
            None, "Select Station", directory=Path.home().resolve().as_posix(), filter="RoboDK Station (*.rdk)"
        )
        self.rdk.AddFile(station_path)
        active_station = self.rdk.ActiveStation()
        print(f"Chosen station: {active_station.Name()}")

    def setup_targets(self):
        assert self.rdk
        list_items = self.rdk.ItemList()
        self.targets = {}
        robodk_items = {item.Name(): item for item in list_items}
        self.robodk_targets = {
            key: value for key, value in robodk_items.items() if key.startswith("Target") or key.startswith("HE-Pose")
        }
        if len(self.robodk_targets) == 0:
            raise RuntimeError("No targets that begins with 'Target' or 'HE-Pose' found in station.")
        for index, (robodk_item_name, robodk_target) in enumerate(self.robodk_targets.items()):
            name = f"Target_{index}"
            self.target_name_mapping[name] = robodk_item_name
            self.targets[name] = RobotTarget(
                name=name, pose=self._robodk_pose_to_transformation_matrix(robodk_target.Pose())
            )
            print(f"Added '{robodk_item_name}' as '{name}' {self.targets[name].pose.translation}")
        self.targets["Home"] = self.targets["Target_0"]
        print(f"Home set to {self.targets['Home'].pose.translation}")
        robodk_item_name = name = "SafeWaypoint"
        if name not in robodk_items:
            raise RuntimeError(f"No '{robodk_item_name}' target found in station. Cannot safely perform touch.")
        self.targets[name] = RobotTarget(
            name=name,
            pose=self._robodk_pose_to_transformation_matrix(robodk_items[robodk_item_name].Pose()),
        )
        self.robodk_targets[name] = robodk_items[robodk_item_name]
        self.target_name_mapping[name] = robodk_item_name
        print(f"Added '{robodk_item_name}' as {name} {self.targets[name].pose.translation}")
        if "CustomTarget" not in robodk_items:
            raise RuntimeError(
                "Station must include a mutable target called 'CustomTarget'. This program will only use and modify this target when moving the robot."
            )
        self.custom_target = robodk_items["CustomTarget"]

    def connect(self, ip_address: str):
        self.rdk = Robolink(args=["/NOSPLASH", "/NOSHOW", "/HIDDEN"], quit_on_close=True)
        if self.rdk is None:
            raise RuntimeError("Robolink failed to initialize")
        self.setup_station()
        self.setup_targets()
        self.robot_handle = self.rdk.ItemUserPick("", ITEM_TYPE_ROBOT)
        print(f"Connecting to robot on {ip_address}")
        if (
            self.robot_handle.ConnectSafe(
                robot_ip=ip_address,
                max_attempts=3,
                wait_connection=2,
                callback_abort=None,
            )
            != 0
        ):
            raise RuntimeError(
                "Timed out while attempting to connect. Your station is valid, but there's no connection with the physical robot."
            )
        self.rdk.setRunMode(RUNMODE_RUN_ROBOT)
        self.robot_handle.setSpeed(100)
        self.robot_handle.setSpeedJoints(100)
        self.robot_handle.setAcceleration(50)
        self.robot_handle.setAccelerationJoints(50)

    def retry_function_call(self, function_to_call, *args, **kwargs):
        max_retries = 3
        delay = 0.25
        for attempt in range(max_retries):
            try:
                return function_to_call(*args, **kwargs)
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    raise
        return None

    def move_l(self, target: RobotTarget) -> None:
        self.move(target, moveL=True)

    def move_j(self, target: RobotTarget) -> None:
        self.move(target, moveL=False)

    def move(self, target: RobotTarget, moveL: bool = False) -> None:
        if self.rdk is None or self.robot_handle is None:
            raise RuntimeError("Robot is not connected and initialized yet, cannot move.")
        print(f"Moving to {target.name}, {target.pose.translation}")
        self.current_target = target
        self.actual_pose = None
        self.target_pose_updated.emit(self.current_target)

        try:

            if target.name in self.target_name_mapping:
                self.robot_moving = True
                if moveL:
                    self.robot_handle.MoveL(self.robodk_targets[self.target_name_mapping[target.name]], blocking=False)
                else:
                    self.robot_handle.MoveJ(self.robodk_targets[self.target_name_mapping[target.name]], blocking=False)
            else:
                target_pose = Mat.fromNumpy(self.current_target.pose.as_matrix())
                try:
                    if moveL:
                        self.robot_handle.MoveL(target_pose, blocking=False)
                    else:
                        self.robot_handle.MoveJ(target_pose, blocking=False)
                except TargetReachError as ex:
                    # Get current joint positions
                    current_joints = self.robot_handle.Joints()

                    solution = self._find_joint_target(current_joints, target_pose)

                    if solution is not None:
                        # Move to the best collision-free solution
                        self.robot_moving = True
                        if moveL:
                            self.robot_handle.MoveL(solution, blocking=False)
                        else:
                            self.robot_handle.MoveJ(solution, blocking=False)
                    else:
                        raise RuntimeError(f"No collision-free solution found to target {target_pose.Pos()}") from ex

            start = datetime.now()
            start_of_interval = start
            while self.retry_function_call(self.robot_handle.Busy):  # type: ignore
                time.sleep(0.25)
                elapsed = datetime.now() - start
                interval = datetime.now() - start_of_interval
                print(f"{elapsed.total_seconds()}...")
                if interval > timedelta(seconds=5):
                    print(f"Robot still moving after {elapsed.seconds} seconds")
            elapsed = datetime.now() - start
            print(f"Robot done moving after {elapsed.total_seconds()}")
            self.robot_moving = False

        except TargetReachError as ex:
            self.robot_moving = False
            raise RuntimeError(f"Cannot move here, would collide. ({ex})") from ex

    def _find_joint_target(self, current_joints: List[float], target_pose: Mat) -> Optional[List[float]]:
        assert self.rdk is not None
        assert self.robot_handle is not None

        def are_configurations_close(config1, config2, tolerance_deg=0.1):
            # ruff: noqa: B905
            return all(abs(a - b) < tolerance_deg for a, b in zip(config1.tolist(), config2.tolist()))

        # Initialize list to store solutions
        solutions: List[Mat] = []

        # Try to find multiple solutions by slightly perturbing the target pose
        for _ in range(5):  # Adjust the range as needed
            perturbed_pose = target_pose * robodk.transl(
                random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)
            )
            solution = self.robot_handle.SolveIK(perturbed_pose)
            if solution is not None and len(solution) > 0:
                solutions.append(solution)

        # Add the original solution
        original_solution = self.robot_handle.SolveIK(target_pose)
        if original_solution is not None and len(original_solution) > 1:
            solutions.append(original_solution)

        # Remove duplicate solutions
        unique_solutions: List[Mat] = []
        for sol in solutions:
            if len(sol) > 1 and not any(
                are_configurations_close(sol, existing_sol) for existing_sol in unique_solutions
            ):
                unique_solutions.append(sol)

        best_solution = None
        min_distance = float("inf")

        for solution in unique_solutions:
            # Check if this solution is collision-free
            self.robot_handle.setJoints(solution)
            if (-180 < solution.tolist()[1] < 0) and not self.rdk.Collisions():
                # Calculate distance from current joint configuration
                distance = sum((a - b) ** 2 for a, b in zip(current_joints, solution.tolist()))  # noqa: B905
                if distance < min_distance:
                    min_distance = distance
                    best_solution = solution

        return best_solution
