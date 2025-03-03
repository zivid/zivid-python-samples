import queue
import threading
import time
from typing import Callable, List, Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from zividsamples.gui.robot_control import RobotControl, RobotTarget
from zividsamples.gui.robot_control_robodk import RobotControlRoboDK
from zividsamples.transformation_matrix import TransformationMatrix


class RobotControlWidget(QWidget):
    ip: str = "172.28.60.23"
    robot_control: RobotControl
    connected: bool = False
    robot_connected = pyqtSignal(bool)
    auto_run_toggled = pyqtSignal()
    target_pose_updated = pyqtSignal(RobotTarget)
    actual_pose_updated = pyqtSignal(RobotTarget)
    get_user_pose: Callable[[], TransformationMatrix]
    current_robot_target: Optional[RobotTarget] = None
    touch_target: Optional[TransformationMatrix] = None
    target_counter: int = 0
    robot_move_thread_done = pyqtSignal()
    result_queue: Optional[queue.Queue] = None
    activeButton: Optional[QPushButton] = None

    def __init__(
        self,
        get_user_pose: Callable[[], TransformationMatrix],
        parent=None,
    ):
        super().__init__(parent)

        self.get_user_pose = get_user_pose

        self.robot_control = RobotControlRoboDK()

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

    def create_widgets(self):

        self.ip_input = QLineEdit()
        self.ip_input.setText(self.ip)

        self.robot_control_group_box = QGroupBox("Robot")
        self.btn_connect_robot = QPushButton("Connect")
        self.btn_connect_robot.setCheckable(True)
        self.btn_connect_robot.setObjectName("ConnectToRobot")
        self.btn_move_to_next_target = QPushButton("Move to next target")
        self.btn_move_to_next_target.setCheckable(True)
        self.btn_move_to_next_target.setObjectName("MoveToNextTarget")
        self.btn_move_to_next_target.setToolTip(
            "Move to the next target in the list. If the last target is reached, the first target will be selected."
        )
        self.btn_move_home = QPushButton("Home")
        self.btn_move_home.setCheckable(True)
        self.btn_move_home.setObjectName("MoveHome")
        self.btn_move_home.setToolTip("Move to the home position. This is also the first target in the list")
        self.btn_move_to_current_target = QPushButton("Move to 'Robot Pose'")
        self.btn_move_to_current_target.setToolTip(
            "Use this if you have manually modified the Robot Pose field and want to move to that pose."
        )
        self.btn_move_to_current_target.setCheckable(True)
        self.btn_move_to_current_target.setObjectName("MoveToCurrentTarget")
        self.btn_move_to_current_target.setVisible(False)
        self.btn_move_to_touch_target = QPushButton("Touch")
        self.btn_move_to_touch_target.setCheckable(True)
        self.btn_move_to_touch_target.setObjectName("MoveToTouchTarget")
        self.btn_move_to_touch_target.setVisible(False)
        self.btn_auto_run = QPushButton("Auto Run")
        self.btn_auto_run.setObjectName("AutoRun")
        self.btn_auto_run.setCheckable(True)
        self.btn_auto_run.setVisible(False)

        self.buttons_which_depend_on_connection_status = {
            self.btn_move_to_next_target: True,
            self.btn_move_home: True,
            self.btn_move_to_current_target: True,
            self.btn_auto_run: True,
            self.btn_move_to_touch_target: True,
        }

        for button, status in self.buttons_which_depend_on_connection_status.items():
            button.setDisabled(status)

    def setup_layout(self):
        ip_form = QFormLayout()
        ip_form.addRow("Robot IP", self.ip_input)

        group_box_layout = QVBoxLayout()
        group_box_layout.addLayout(ip_form)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.btn_connect_robot)
        buttons_layout.addWidget(self.btn_move_to_next_target)
        buttons_layout.addWidget(self.btn_move_home)
        buttons_layout.addWidget(self.btn_move_to_current_target)
        buttons_layout.addWidget(self.btn_auto_run)
        buttons_layout.addWidget(self.btn_move_to_touch_target)
        group_box_layout.addLayout(buttons_layout)
        self.robot_control_group_box.setLayout(group_box_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.robot_control_group_box)
        self.setLayout(layout)

    def connect_signals(self):
        self.btn_connect_robot.clicked.connect(self.on_connect_to_robot)
        self.btn_move_to_next_target.clicked.connect(self.on_move_to_next_target)
        self.btn_move_home.clicked.connect(self.on_move_home)
        self.btn_move_to_current_target.clicked.connect(self.on_move_to_current_target)
        self.btn_auto_run.clicked.connect(self.on_auto_run_toggled)
        self.btn_move_to_touch_target.clicked.connect(self.on_move_to_touch_target)
        self.robot_control.target_pose_updated.connect(self.target_pose_updated.emit)
        self.robot_move_thread_done.connect(self.on_robot_done_moving)

    def enable_disable_buttons(self, auto_run: bool, touch: bool):
        self.buttons_which_depend_on_connection_status[self.btn_auto_run] = auto_run
        self.btn_auto_run.setEnabled(auto_run and self.connected)
        self.buttons_which_depend_on_connection_status[self.btn_move_to_touch_target] = touch
        self.btn_move_to_touch_target.setEnabled(touch and self.connected)
        for button, status in self.buttons_which_depend_on_connection_status.items():
            button.setEnabled(status)

    def show_buttons(self, auto_run: bool, touch: bool):
        self.btn_auto_run.setVisible(auto_run)
        self.btn_move_to_touch_target.setVisible(touch)

    def set_auto_run_active(self, auto_run_active: bool):
        self.btn_auto_run.setChecked(auto_run_active)
        for button, status in self.buttons_which_depend_on_connection_status.items():
            if button != self.btn_auto_run:
                button.setEnabled((not auto_run_active) and status and self.connected)
        if self.btn_auto_run.isChecked():
            self.btn_auto_run.setStyleSheet("background-color: yellow;")
            self.btn_auto_run.setText("Stop")
        else:
            self.btn_auto_run.setStyleSheet("")
            self.btn_auto_run.setText("Auto Run")

    def on_auto_run_toggled(self):
        self.auto_run_toggled.emit()

    def toggle_unsafe_move(self, allow_unsafe_move: bool):
        self.btn_move_to_current_target.setVisible(allow_unsafe_move)

    def robot_is_moving(self):
        return self.robot_control.is_moving()

    def robot_is_home(self):
        return self.robot_control.is_home()

    def on_robot_done_moving(self):
        if self.result_queue is None:
            raise RuntimeError("result_queue is not initialized")
        if self.activeButton is None:
            raise RuntimeError("activeButton is not initialized")
        result = self.result_queue.get()
        print(f"Robot finished a non-blocking move, button: {self.activeButton.objectName()}")
        self.activeButton.setChecked(False)
        self.activeButton.setStyleSheet("")
        self.on_get_pose()
        if not result:
            print("Failed to `move_to_current_target()`")

    def on_get_pose(self):
        try:
            actual_pose = self.robot_control.get_pose()
            if actual_pose:
                if actual_pose.name == "Home":
                    self.btn_move_home.setStyleSheet("background-color: green;")
                self.actual_pose_updated.emit(actual_pose)
        except Exception as ex:
            QMessageBox.warning(self, "Robot Control", f"Lost connection: {ex}")
            self.btn_connect_robot.setChecked(False)
            self.btn_connect_robot.setStyleSheet("")
            self.btn_connect_robot.setText("Connect")
            self.robot_connected.emit(False)

    def disconnect(self):
        print("Disconnecting")
        self.btn_connect_robot.setChecked(False)
        self.btn_connect_robot.setStyleSheet("")
        self.btn_connect_robot.setText("Connect")
        for button in self.buttons_which_depend_on_connection_status:
            button.setDisabled(True)
        self.connected = False
        self.robot_connected.emit(False)

    def on_connect_to_robot(self):
        if self.connected:
            self.robot_control.disconnect()
            self.disconnect()
        else:
            self.btn_connect_robot.setChecked(True)
            self.btn_connect_robot.setStyleSheet("background-color: yellow;")
            self.btn_connect_robot.setText("Connecting...")
            QApplication.processEvents()
            try:
                self.robot_control.connect(self.ip)
                self.btn_connect_robot.setStyleSheet("background-color: green;")
                self.btn_connect_robot.setText("Disconnect")
                self.on_get_pose()
                for button, status in self.buttons_which_depend_on_connection_status.items():
                    button.setEnabled(status)
                self.connected = True
                self.robot_connected.emit(True)
            except Exception as ex:
                print(f"Failed to connect: {ex}")
                QMessageBox.warning(self, "Robot Control", f"Failed to connect: {ex}")
                self.disconnect()

    def move_robot_in_separate_thread(self, emit_signal_when_done: bool = False, moveL: bool = False) -> None:
        assert self.result_queue is not None
        if self.current_robot_target is None:
            QMessageBox.warning(None, "Robot Control", "No target set")
            self.result_queue.put(False)
            return
        try:
            print(f"{emit_signal_when_done=}")
            if moveL:
                self.robot_control.move_l(self.current_robot_target)
            else:
                self.robot_control.move_j(self.current_robot_target)
            self.result_queue.put(True)
        except Exception as ex:
            print(f"Warning: {ex}")
            QMessageBox.warning(None, "Robot Control", str(ex))
            self.result_queue.put(False)
        if emit_signal_when_done:
            self.robot_move_thread_done.emit()
        elif self.activeButton is not None:
            print(f"Robot finished a blocking move, button: {self.activeButton.objectName()}")

    def move_to_current_target(self, blocking: bool = True, moveL: bool = False) -> bool:
        if self.activeButton is None:
            raise RuntimeError("activeButton is not initialized")
        self.activeButton.setChecked(True)
        self.activeButton.setStyleSheet("background-color: yellow;")
        QApplication.processEvents()
        self.result_queue = queue.Queue()
        emit_signal_when_done = not blocking
        move_thread = threading.Thread(target=self.move_robot_in_separate_thread, args=(emit_signal_when_done, moveL))
        move_thread.start()
        if not blocking:
            return True
        while move_thread.is_alive():
            time.sleep(0.1)
            print("-", end="", flush=True)
            QApplication.processEvents()
        result = self.result_queue.get()
        self.activeButton.setChecked(False)
        self.activeButton.setStyleSheet("")
        self.on_get_pose()
        if not result:
            print("Failed to `move_to_current_target()`")
        return result

    def on_move_home(self):
        self.target_counter = 0
        self.current_robot_target = self.robot_control.get_target_by_id(self.target_counter)
        self.activeButton = self.btn_move_home
        if self.move_to_current_target():
            self.btn_move_home.setStyleSheet("background-color: green;")

    def on_move_to_next_target(self, blocking: bool = True):
        self.target_counter += 1
        if self.target_counter == self.robot_control.get_number_of_regular_targets():
            self.target_counter = 0
        if self.target_counter == 0:
            self.btn_move_home.setStyleSheet("background-color: green;")
        else:
            self.btn_move_home.setStyleSheet("")
        self.current_robot_target = self.robot_control.get_target_by_id(self.target_counter)
        self.activeButton = self.btn_move_to_next_target
        self.move_to_current_target(blocking)

    def on_move_to_touch_target(self):
        if self.touch_target is None:
            QMessageBox.warning(self, "Robot Control", "Aruco target not acquired")
            return
        self.btn_move_home.setStyleSheet("")
        self.current_robot_target = self.robot_control.get_safe_waypoint()
        if self.current_robot_target is None:
            QMessageBox.critical(self, "Robot Control", "No safe waypoint found. Cannot safely perform touch.")
            self.on_get_pose()
            return
        self.activeButton = self.btn_move_to_touch_target
        self.move_to_current_target()
        approach_target_in_tool_frame = TransformationMatrix()
        approach_target_in_tool_frame.translation[2] = -200
        approach_target_in_base_frame = self.touch_target * approach_target_in_tool_frame
        self.current_robot_target = self.robot_control.get_custom_target(approach_target_in_base_frame)
        self.move_to_current_target()
        self.current_robot_target = self.robot_control.get_custom_target(self.touch_target)
        self.move_to_current_target(moveL=True)
        time.sleep(4)
        self.current_robot_target = self.robot_control.get_custom_target(approach_target_in_base_frame)
        self.move_to_current_target(moveL=True)
        self.current_robot_target = self.robot_control.get_safe_waypoint()
        self.move_to_current_target()

    def on_move_to_current_target(self):
        self.current_robot_target = self.robot_control.get_custom_target(self.get_user_pose())
        self.activeButton = self.btn_move_to_current_target
        self.move_to_current_target()
        self.btn_move_home.setStyleSheet("")

    def set_touch_target(self, touch_target: TransformationMatrix):
        self.touch_target = touch_target
        self.btn_move_to_touch_target.setEnabled(True)

    def get_tab_widgets_in_order(self) -> List[QWidget]:
        all_widgets = [
            self.btn_connect_robot,
            self.btn_move_to_next_target,
            self.btn_move_home,
            self.btn_auto_run,
            self.btn_move_to_touch_target,
        ]
        return [widget for widget in all_widgets if widget.isVisible()]
