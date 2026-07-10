from zividsamples.gui.robot.robot_control import RobotTarget
from zividsamples.gui.widgets.tab_content_widget import TabContentWidget
from zividsamples.gui.wizard.rotation_format_configuration import RotationInformation


class TabWidgetWithRobotSupport(TabContentWidget):

    def on_actual_pose_updated(self, robot_target: RobotTarget) -> None:
        """
        Override in subclasses to handle robot pose update.

        Args:
            robot_target: Actual robot pose now.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def rotation_format_update(self, rotation_information: RotationInformation) -> None:
        """
        Override in subclasses to handle rotation information updates.

        This is called when user updates rotation format.

        Args:
            rotation_information: Rotation format selected by the user.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method.")
