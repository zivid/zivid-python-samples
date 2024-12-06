# Hand-Eye Calibration

To fully understand Hand-Eye Calibration, please see the [tutorial][Tutorial-url] in our Knowledge Base.

-----------------
The following applications create a **Hand-Eye Transformation Matrix** from data provided by a user:

[**HandEyeCalibration**][HandEyeCalibration-url]

* An application that walks through the collection of calibration poses:
   1. The user provides a robot pose in the form of a 4x4 transformation matrix (manual entry)
   2. The application captures a point cloud of the calibration object
   3. The user moves the robot to a new capture pose and enters the command to add a new pose
   4. Steps i.-iii. are repeated until 10-20 pose pairs are collected
   5. The user enter the command to perform calibration and the application returns a **Hand-Eye Transformation Matrix**

[**ZividHandEyeCalibration**][ZividHandEyeCalibration-url]

* [CLI application][CLI application-url], which takes a collection of robot pose and point cloud pairs (e.g. output of the steps i.-iii. in [HandEyeCalibration][HandEyeCalibration-url]) and returns a **Hand-Eye Transformation Matrix**. This application comes with the Windows installer and is part of the tools deb for Ubuntu.

-----------------

There are two samples that show how to perform the acquisition of the hand-eye calibration dataset.
Both samples go through the process of acquiring the robot pose and point cloud pairs and then process them to return the resulting **Hand-Eye Transform Matrix**.

[**UniversalRobotsPerformHandEyeCalibration**][URhandeyecalibration-url]

* This sample is created to work specifically with the UR5e robot.
* To follow the tutorial for this sample go to [**UR5e + Python Hand Eye Tutorial**][URHandEyeTutorial-url].

[**RoboDKHandEyeCalibration**][RobodkHandEyeCalibration-url]

The second sample uses RoboDK for robot control and can be used with any robot that the software supports.
The list of the robots that they support can be found [**here**][robodk-robot-library-url].
Poses must be added by the user to their rdk file.
To find the best capture pose practice follow the instructions provided on the Zivid knowledge base for the [hand-eye calibration process][ZividHandEyeCalibration-url].

-----------------
The following applications assume that a **Hand-Eye Transformation Matrix** has been found.

[**UtilizeHandEyeCalibration**][UtilizeHandEyeCalibration-url]:

* Shows how to transform position and rotation (pose) from the camera coordinate system to the robot coordinate system.
* Example use case - "Bin Picking":
   1. Acquire a point cloud of an object to pick with a Zivid camera.
   2. Find an optimal picking pose for the object and **transform it into the robot coordinate system**
   3. Use the transformed pose to calculate the robot path and execute the pick

[**PoseConversions**][PoseConversions-url]:

* Zivid primarily operates with a (4x4) **Transformation Matrix** (Rotation Matrix + Translation Vector). This example shows how to convert to and from:
  * AxisAngle, Rotation Vector, Roll-Pitch-Yaw, Quaternion

[**VerifyHandEyeWithVisualization**][VerifyHandEyeWithVisualization-url]:

Visually demonstrates the hand-eye calibration accuracy by overlapping transformed points clouds.

* The application asks the user for the hand-eye calibration type (manual entry).
* After loading the hand-eye dataset (point clouds and robot poses) and the hand-eye output (**transformation matrix**), the application repeats the following process for all dataset pairs:
   1. Transforms the point cloud
   2. Finds cartesian coordinates of the checkerboard centroid
   3. Creates a region of interest around the checkerboard and filters out points outside the region of interest
   4. Saves the point cloud to a PLY file
   5. Appends the point cloud to a list (overlapped point clouds)

This application ends by displaying all point clouds from the list.

[**RobodkHandEyeVerification**][RobodkHandEyeVerification-url]

Serves to verify the hand-eye calibration accuracy via a touch test.

* After loading the hand-eye configuration, the required transformation matrices, and the type of the calibration object, the application runs in the following steps:
   1. The robot moves to the Capture Pose previously defined.
   2. The user is asked to put the Zivid Calibration Object in the FOV and press Enter.
   3. The camera captures the Zivid Calibration Object and the pose of the touching point is computed and displayed to the user.
   4. When the user presses the Enter key, the robot touches the Zivid Calibration Object at a distinct point.
   5. Upon pressing the Enter key, the robot pulls back and returns to the Capture Pose.
   6. At this point, the Zivid Calibration Object can be moved to perform the Touch Test at a different location.
   7. The user is asked to input “y” on “n” to repeat or abort the touch test.

[HandEyeCalibration-url]: hand_eye_calibration.py
[UtilizeHandEyeCalibration-url]: utilize_hand_eye_calibration.py
[VerifyHandEyeWithVisualization-url]: verify_hand_eye_with_visualization.py
[ZividHandEyeCalibration-url]: https://support.zivid.com/latest/academy/applications/hand-eye/hand-eye-calibration-process.html
[Tutorial-url]: https://support.zivid.com/latest/academy/applications/hand-eye.html
[PoseConversions-url]: pose_conversions.py
[CLI application-url]: https://support.zivid.com/latest/academy/applications/hand-eye/zivid_CLI_tool_for_hand_eye_calibration.html
[URhandeyecalibration-url]: ur_hand_eye_calibration/universal_robots_perform_hand_eye_calibration.py
[URHandEyeTutorial-url]: https://support.zivid.com/en/latest/academy/applications/hand-eye/ur5-robot-+-python-generate-dataset-and-perform-hand-eye-calibration.html
[RobodkHandEyeCalibration-url]: robodk_hand_eye_calibration/robodk_hand_eye_calibration.py
[RobodkHandEyeVerification-url]: robodk_hand_eye_calibration/robodk_verify_hand_eye_calibration.py
[robodk-robot-library-url]: https://robodk.com/supported-robots