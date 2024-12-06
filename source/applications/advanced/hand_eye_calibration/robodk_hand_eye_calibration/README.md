# Hand-Eye Calibration with RoboDK

Hand-eye calibration is a necessity for any picking scenario that involves a camera and a robot.
This sample robodk_hand_eye_calibration.py offers an easy and adaptable method to perform hand-eye
calibration with a variety of robots that are supported in RoboDK.
The sample robodk_verify_hand_eye_calibration.py serves to verify hand-eye calibration accuracy via
a touch test.

For more on Hand-Eye Calibration, please see the [tutorial](https://support.zivid.com/latest/academy/applications/hand-eye.html) in our Knowledge Base.

If you need help with the samples, visit our Knowledge Base:

* [Any Robot + RoboDK + Python: Generate Dataset and Perform Hand-Eye Calibration](https://support.zivid.com/en/latest/academy/applications/hand-eye/robodk-%2B-python-generate-dataset-and-perform-hand-eye-calibration.html).

* [Any Robot + RoboDK + Python: Verify Hand-Eye Calibration Result Via Touch Test](https://support.zivid.com/en/latest/academy/applications/hand-eye/hand-eye-calibration-verification-via-touch-test.html).

The samples are made and modeled with a Universal Robots UR5e robot.
It is a requirement that you make your own poses that suit your environment.
If you have a different robot from a UR5e you will need to load in the corresponding robot to your rdk file.

## Installation

1. [Install Zivid Software](https://support.zivid.com/latest//getting-started/software-installation.html)

2. [Install Zivid Python](https://github.com/zivid/zivid-python).
Note: The recommended Python version for these samples is 3.8.

3. [Install RoboDK](https://robodk.com/download)

4. [Install RoboDK python](https://pypi.org/project/robodk/)
