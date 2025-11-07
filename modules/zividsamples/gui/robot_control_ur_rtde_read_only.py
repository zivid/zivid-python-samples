import tempfile
from datetime import datetime
from time import sleep

import numpy as np
from rtde import rtde, rtde_config
from scipy.spatial.transform import Rotation
from zividsamples.gui.robot_configuration import RobotConfiguration
from zividsamples.gui.robot_control import RobotControlReadOnly, RobotTarget
from zividsamples.transformation_matrix import TransformationMatrix

UR_RTDE_RECIPE = """\
<?xml version="1.0"?>
<rtde_config>
    <recipe key="out">
        <field name="actual_TCP_pose" type="VECTOR6D"/>
    </recipe>
</rtde_config>
"""


class RobotControlURRTDEReadOnly(RobotControlReadOnly):

    def __init__(self, robot_configuration: RobotConfiguration):
        super().__init__(robot_configuration=robot_configuration)
        self.robot_handle = None

    def get_pose(self) -> RobotTarget:
        if self.robot_handle is None:
            raise RuntimeError("RTDE interface not connected.")
        try:
            for _ in range(5):
                if self.robot_handle.has_data():
                    tcp_pose = self.robot_handle.receive().actual_TCP_pose
                    return RobotTarget(
                        name="Current TCP Pose",
                        pose=TransformationMatrix(
                            translation=np.array(tcp_pose[:3]) * 1000,
                            rotation=Rotation.from_rotvec(tcp_pose[3:6], degrees=False),
                        ),
                    )
                sleep(0.01)
        except Exception as e:
            print(f"Error while receiving RTDE data: {e}")
            raise RuntimeError(f"Error while receiving RTDE data: {e}") from e
        raise RuntimeError("No RTDE data received from robot.")

    def disconnect(self):
        if self.robot_handle is not None:
            try:
                start_time = datetime.now()
                timeout = 2.0  # seconds
                while not self.robot_handle.is_connected():
                    success = self.robot_handle.send_pause()
                    if success:
                        break
                    if (datetime.now() - start_time).total_seconds() > timeout:
                        raise RuntimeError("Timeout while waiting for RTDE connection to pause.")
                    sleep(0.01)
                self.robot_handle.disconnect()
            except Exception as e:
                print(f"Error while disconnecting RTDE: {e}")
        self.robot_handle = None

    def connect(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(UR_RTDE_RECIPE.encode())
            temp_file.flush()
            configuration = rtde_config.ConfigFile(temp_file.name)
            output_names, output_types = configuration.get_recipe("out")
            self.robot_handle = rtde.RTDE(self.robot_configuration.ip_addr)
            self.robot_handle.connect()
            self.robot_handle.send_output_setup(output_names, output_types, frequency=125)
            self.robot_handle.send_start()


if __name__ == "__main__":
    robot = RobotControlURRTDEReadOnly(RobotConfiguration())
    robot.connect()
    previous_pose = TransformationMatrix()
    for _ in range(100):
        robot_target = robot.get_pose()
        distance_to_previous = robot_target.pose.distance_to(previous_pose)
        print(f"Current translation: {robot_target.pose.translation} - {distance_to_previous.translation:>10.4f} mm")
        print(
            f"Current rotation (rotvec): {robot_target.pose.rotation.as_rotvec()} - {distance_to_previous.rotation:>10.4f} rad"
        )
        sleep(0.01)
        previous_pose = robot_target.pose
