from zividsamples.gui.robot_control import RobotTarget
from zividsamples.gui.rotation_format_configuration import RotationInformation
from zividsamples.gui.tab_content_widget import TabContentWidget


class TabWidgetWithRobotSupport(TabContentWidget):

    def on_actual_pose_updated(self, robot_target: RobotTarget):
        """
        Override in subclasses to handle robot pose update.
        :param robot_target: Actual robot pose now.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def rotation_format_update(self, rotation_information: RotationInformation):
        """
        Override in subclasses to handle rotation information updates.
        This is called when user updates rotation format.
        """
        raise NotImplementedError("Subclasses should implement this method.")
