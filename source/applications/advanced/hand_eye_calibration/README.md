# Hand Eye Calibration

To fully understand Hand-Eye Calibration, please see the [tutorial][Tutorial-url] in our Knowledge Base.

-----------------
The following applications create a **Transformation Matrix** from data provided by a user

[**HandEyeCalibration**][HandEyeCalibration-url]

* Application which walks through the collection of calibration poses
   1. Provide robot pose to application (manual entry)
   2. Application takes an image of the calibration object, and calculates pose
   3. Move robot to new position, enter command to Add Pose
   4. Repeat i.-iii. until 10-20 pose pairs are collected
   5. Enter command to perform calibration and return a **Transformation Matrix**

[**ZividHandEyeCalibration**][ZividHandEyeCalibration-url]

* [CLI application][CLI application-url] which takes a collection of pose pairs (e.g. output of steps 1-3 in [HandEyeCalibration][HandEyeCalibration-url]) and returns a **Transformation Matrix**. This application comes with the Windows installer and is part of the tools deb for Ubuntu.

-----------------

There are two samples that show how to perform acquisition of the hand-eye calibration dataset in this repository.
Both samples go through the process of acquiring the pose and point cloud pairs and then process them to return the resulting hand-eye **Transform Matrix**.

[**UniversalRobotsPerformHandEyeCalibration**][URhandeyecalibration-url]

* This sample is created to work specifically with the UR5e robot.
* To follow the tutorial for this sample go to [**UR5e + Python Hand Eye Tutorial**][URHandEyeTutorial-url].

[**RoboDKHandEyeCalibration**][RobodkHandEyeCalibration-url]

The second sample uses RoboDK for robot control and can be used with any robot that the software supports.
The list for the robots that they support can be found [**here**][robodk-robot-library-url].
Poses must be added by the user to their personal rdk file.    
To find best pose practice follow the instructions provided on the Zivid knowledge base for the [hand-eye calibration process][ZividHandEyeCalibration-url].

-----------------
The following applications assume that a **Transformation Matrix** has been found

[**UtilizeHandEyeCalibration**][UtilizeHandEyeCalibration-url]:

* Shows how to transform position and rotation (pose) in Camera co-ordinate system to Robot co-ordinate system.
* Example use case - "Bin Picking":
   1. Acquire point cloud of objects to pick with Zivid camera
   2. Find optimal picking pose for object and **transform to robot co-ordinate system**
   3. Use transformed pose to calculate robot path and execute pick

[**PoseConversions**][PoseConversions-url]:

* Zivid primarily operate with a (4x4) **Transformation Matrix** (Rotation Matrix + Translation Vector). This example shows how to use Eigen to convert to and from:
  * AxisAngle, Rotation Vector, Roll-Pitch-Yaw, Quaternion

[**VerifyHandEyeWithVisualization**][VerifyHandEyeWithVisualization-url]:

Visually demonstrates the hand-eye calibration accuracy by overlapping transformed points clouds.

* The application asks the user for the hand-eye calibration type (manual entry).
* After loading the hand-eye dataset (point clouds and robot poses) and the hand-eye output (**transformation matrix**), the application repeats the following process for all data pairs:
   1. Transforms the point cloud
   2. Finds cartesian coordinates of the checkerboard centroid
   3. Creates a region of interest around the checkerboard and filters out points outside the region of interest
   4. Saves the point cloud to a PLY file
   5. Appends the point cloud to a list (overlapped point clouds)

This application ends by displaying all point clouds from the list.

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
[robodk-robot-library-url]: https://robodk.com/supported-robots