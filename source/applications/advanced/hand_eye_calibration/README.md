# Hand-Eye Calibration

This page provides an overview of how to **perform**, **verify**, and **use Hand–Eye Calibration** with Zivid cameras.

If you are new to Hand–Eye Calibration, start with the [Hand–Eye Calibration – Concept & Theory][HandEyeTutorial-url], explaining:

- What Hand–Eye Calibration is
- The difference between **eye-in-hand** and **eye-to-hand**
- Best practices for dataset (point clouds and robot poses) acquisition

If you already know what you’re doing and just want to run calibration or check out our Hand-Eye calibration code, continue reading.

<!-- Use "Markdown All in One plugin in VS code to automatically generate and update TOC". -->

- [Quick Start: Just Calibrate](#quick-start-just-calibrate)
- [Programmatic Hand–Eye Calibration](#programmatic-handeye-calibration)
- [Dataset Acquisition Samples](#dataset-acquisition-samples)
- [After Hand–Eye Calibration](#after-handeye-calibration)
- [Verifying Calibration Accuracy](#verifying-calibration-accuracy)
- [Summary: Which Tool Should I Use?](#summary-which-tool-should-i-use)

---

## Quick Start: Just Calibrate

If your goal is **only to compute the Hand–Eye Transformation Matrix**, use one of the tools below and follow Zivid’s [best-practice guide for capture poses][ZividHandEyeCalibration-url].

### Hand–Eye Calibration GUI (Recommended)

- Tutorial: [Hand–Eye GUI Tutorial][HandEyeCalibrationGUITutorial-url]
- Application: [HandEyeCalibration GUI][HandEyeCalibrationGUI-url]

Best choice if you:

- Want a guided, no-code workflow

---

## Programmatic Hand–Eye Calibration

The following applications produce a Hand–Eye Transformation Matrix from robot poses and calibration captures.

### Minimal Hand-Eye Calibration Code Example

- Sample: [HandEyeCalibration][HandEyeCalibration-url]
- Tutorial: [Integrating Zivid Hand-Eye Calibration][hand-eye-procedure-url]

Workflow:

1. User inputs robot pose in the form of a 4x4 transformation matrix (manual entry)
2. Camera captures the calibration object
3. User moves the robot to a new capture pose and enters the command to add a new pose
4. First three steps are repeated (typically 10–20 pose pairs)
5. User enters the command to perform calibration and the application returns a Hand-Eye Transformation Matrix

Use this if you:

- Want the simplest integration example
- Are building your own calibration pipeline

---

### Hand Eye Calibration CLI Tool

- Tutorial: [Zivid CLI Tool for Hand–Eye Calibration][CLI application-url]
- Installed with:
  - Windows Zivid installer
  - `tools` deb package on Ubuntu

Use this if you:

- Already have a dataset (robot poses + point clouds)
- Want a command-line, batch-style workflow

---

## Dataset Acquisition Samples

The samples below show how to acquire robot poses and point clouds, then compute the Hand–Eye Transformation Matrix.

### RoboDK-Based (Robot-Agnostic)

- Sample: [RoboDKHandEyeCalibration][RobodkHandEyeCalibration-url]
- Tutorial: [Any Robot + RoboDK + Python Hand–Eye Tutorial][RoboDKHandEyeTutorial-url]
- Supported robots: [RoboDK robot library][robodk-robot-library-url]

Features:

- Works with any RoboDK-supported robot
- Capture poses are manually defined in the `.rdk` file
- Fully automated robot control

---

### Universal Robots (e.g. UR5e)

- Sample: [UniversalRobotsPerformHandEyeCalibration][URhandeyecalibration-url]
- Tutorial: [UR5e + Python Hand–Eye Tutorial][URHandEyeTutorial-url]

Features:

- Designed specifically for UR robots
- Fully automated robot control

---

## After Hand–Eye Calibration

The following applications assume that a **Hand–Eye Transformation Matrix already exists**.

### Utilize Hand-Eye Calibration

- Sample: [UtilizeHandEyeCalibration][UtilizeHandEyeCalibration-url]
- Tutorial: [How To Use The Result Of Hand-Eye Calibration][UtilizeHandEyeCalibrationTutorial-url]

Demonstrates how to:

- Transform poses from camera coordinates to robot coordinates
- Use the transform in real applications (e.g., bin picking)

Example workflow:

1. Capture a point cloud with a Zivid camera
2. Find an object pick pose in camera coordinate system
3. Transform the pose into robot coordinate system
4. Plan and execute the robot motion

---

### Pose Conversions

- Sample: [PoseConversions][PoseConversions-url]
- Application: [PoseConversions GUI][PoseConversionsGUI-url]
- Theory: [Conversions Between Common Orientation Representations][PoseConversionsTheory-url]

Zivid primarily operates with a (4x4) Transformation Matrix (Rotation Matrix + Translation Vector). This example shows how to convert to and from:

- Axis–Angle
- Rotation Vector
- Roll–Pitch–Yaw
- Quaternion

Useful for integrating with robot controllers.

---

## Verifying Calibration Accuracy

### Verify Hand-Eye With Visualization

- Sample: [VerifyHandEyeWithVisualization][VerifyHandEyeWithVisualization-url]

Application validation approach:

- Loads the hand-eye dataset and output (transformation matrix)
- For each dataset pair:
  - Transforms the point cloud to common coordinate system
  - Finds the checkerboard centroid cartesian coordinates
  - Removes the points outside the the checkerboard ROI
- Overlaps transformed point clouds
- Visualizes alignment accuracy

Best for:

- Visual verification
- Detecting systematic rotation/translation errors

---

### RoboDK Touch Test Verification

- Script: [RobodkHandEyeVerification][RobodkHandEyeVerification-url]
- Tutorial: [Verify Hand-Eye Calibration Result Via Touch Test][RobodkHandEyeVerificationTutorial-url]

Verification steps:

1. Robot moves to a predefined capture pose
2. User places the calibration object in the FOV
3. Camera estimates a touch point
4. Robot physically touches the calibration object
5. User repeats the test at multiple locations

Best for:

- Physical validation
- High-accuracy requirement applications

---

## Summary: Which Tool Should I Use?

| Goal | Recommended Tool |
|------|------------------|
| Conceptual understanding | [Knowledge Base article][HandEyeTutorial-url] |
| Guided calibration | [Hand–Eye GUI][HandEyeCalibrationGUITutorial-url] |
| Minimal integration example | [HandEyeCalibration][HandEyeCalibration-url] |
| Existing dataset | [Hand–Eye GUI][HandEyeCalibrationGUITutorial-url]|
| UR robots | [Hand–Eye GUI][HandEyeCalibrationGUITutorial-url] or [UR Hand–Eye sample][URHandEyeTutorial-url] |
| Any robot | [Hand–Eye GUI][HandEyeCalibrationGUITutorial-url] or [RoboDK Hand–Eye sample][RoboDKHandEyeTutorial-url] |
| Use calibration result | [UtilizeHandEyeCalibration][UtilizeHandEyeCalibrationTutorial-url] |
| Verify visually | [Hand–Eye GUI][HandEyeCalibrationGUITutorial-url] or [VerifyHandEyeWithVisualization][VerifyHandEyeWithVisualization-url] |
| Verify physically | [Hand–Eye GUI][HandEyeCalibrationGUITutorial-url] or [RoboDK Touch Test][RobodkHandEyeVerification-url] |


[HandEyeTutorial-url]: https://support.zivid.com/latest/academy/applications/hand-eye.html

[HandEyeCalibration-url]: hand_eye_calibration.py

[HandEyeCalibrationGUI-url]: hand_eye_gui.py
[HandEyeCalibrationGUITutorial-url]: https://support.zivid.com/en/latest/academy/applications/hand-eye/hand-eye-gui.html

[UtilizeHandEyeCalibration-url]: utilize_hand_eye_calibration.py
[UtilizeHandEyeCalibrationTutorial-url]: https://support.zivid.com/en/latest/academy/applications/hand-eye/how-to-use-the-result-of-hand-eye-calibration.html

[VerifyHandEyeWithVisualization-url]: verify_hand_eye_with_visualization.py
[ZividHandEyeCalibration-url]: https://support.zivid.com/latest/academy/applications/hand-eye/hand-eye-calibration-process.html
[hand-eye-procedure-url]: https://support.zivid.com/en/latest/academy/applications/hand-eye/hand-eye-calibration-process.html#custom-integration

[PoseConversions-url]: pose_conversions.py
[PoseConversionsGUI-url]: pose_conversion_gui.py
[PoseConversionsTheory-url]: https://support.zivid.com/en/latest/reference-articles/pose-conversions.html

[CLI application-url]: https://support.zivid.com/latest/academy/applications/hand-eye/zivid_CLI_tool_for_hand_eye_calibration.html

[URhandeyecalibration-url]: ur_hand_eye_calibration/universal_robots_perform_hand_eye_calibration.py
[URHandEyeTutorial-url]: https://support.zivid.com/en/latest/academy/applications/hand-eye/ur5-robot-%2B-python-generate-dataset-and-perform-hand-eye-calibration.html

[RobodkHandEyeCalibration-url]: robodk_hand_eye_calibration/robodk_hand_eye_calibration.py
[RoboDKHandEyeTutorial-url]: https://support.zivid.com/en/latest/academy/applications/hand-eye/robodk-%2B-python-generate-dataset-and-perform-hand-eye-calibration.html

[RobodkHandEyeVerification-url]: robodk_hand_eye_calibration/robodk_verify_hand_eye_calibration.py
[RobodkHandEyeVerificationTutorial-url]: https://support.zivid.com/en/latest/academy/applications/hand-eye/hand-eye-calibration-verification-via-touch-test.html

[robodk-robot-library-url]: https://robodk.com/supported-robots
