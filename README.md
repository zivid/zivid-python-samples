# python-samples

[![Build Status][ci-badge]][ci-url]

This repository contains **Python** code samples for **Zivid**.

## Samples list

There are two main categories of samples: **camera** and **applications**. The samples in the **camera** category focus only on how to use the camera. The samples in the **applications** category demonstrate practical use of the output data from the camera, such as 3D point clouds or 2D images.

- **camera**
  - **basic** ([quick tutorial][QuickCaptureTutorial-url] / [complete tutorial][CompleteCaptureTutorial-url])
    - [**capture**][capture-url] - Capture point clouds, with color, from the Zivid camera.
    - [**capture_2d**][capture_2d-url] - Capture 2D images from the Zivid camera.
    - [**capture_assistant**][capture_assistant-url] - Use Capture Assistant to capture point clouds, with color, from the Zivid camera.
    - [**capture_from_file**][capture_from_file-url] - Capture point clouds, with color, from the Zivid file camera.
    - [**capture_with_settings_from_yml**][capture_with_settings_from_yml-url] -  Capture point clouds, with color, from the Zivid camera, with settings from YML file.
    - [**capture_hdr**][capture_hdr-url] - Capture HDR point clouds, with color, from the Zivid camera.
    - [**capture_hdr_complete_settings**][capture_hdr_complete_settings-url] - Capture point clouds, with color, from the Zivid camera with fully configured settings.
  - **advanced**
    - [**capture_hdr_loop**][capture_hdr_loop-url] - Cover the same dynamic range in a scene with different acquisition settings to optimize for quality, speed, or to find a compromise.
  - **info_util_other**
    - [**print_version_info**][print_version_info-url] - Print version info about connected Zivid cameras and the installed Zivid SDK.

- **applications**
  - **basic**
    - **visualization**
      - [**read_zdf_vis_3d**][read_zdf_vis_3d-url] - Read point cloud data from a ZDF file and visualize it.
        - **Dependencies:**
          - [pptk](https://github.com/heremaps/pptk) version 0.1.0 or newer
          - [numpy](https://numpy.org/) version 1.19.2 or newer
          - [matplotlib](https://matplotlib.org/) version 3.3.2 or newer
    - **file_formats**
      - [**convert_zdf**][convert_zdf-url] - Convert point cloud data from a ZDF file to your preferred format (.ply, .csv, .txt, .png, .jpg, .bmp, .tiff).
        - **Dependencies:**
          - [numpy](https://numpy.org/) version 1.19.2 or newer
          - [OpenCV](https://opencv.org/) version 4.0.1 or newer.
      - [**read_iterate_zdf**][read_iterate_zdf-url] - Read point cloud data from a ZDF file, iterate through it, and extract individual points.
  - **advanced**
    - [**hand_eye_calibration**][hand_eye_calibration-url]
      - [**calibrate_eye_to_hand**][calibrate_eye_to_hand-url] - Perform Eye-to-Hand calibration.
        - **Dependencies:**
          - [numpy](https://numpy.org/) version 1.19.2 or newer
      - [**utilize_eye_in_hand_calibration**][utilize_eye_in_hand_calibration-url] - Transform a single data point or entire point cloud from the camera frame to the robot base frame using the Eye-in-Hand calibration matrix.
        - **Dependencies:**
          - [numpy](https://numpy.org/) version 1.19.2 or newer
          - [OpenCV](https://opencv.org/) version 4.0.1 or newer.
      - [**pose_conversions**][pose_conversions-url] - Convert to/from Transformation Matrix (Rotation Matrix + Translation Vector).
        - **Dependencies:**
          - [numpy](https://numpy.org/) version 1.19.2 or newer
          - [OpenCV](https://opencv.org/) version 4.0.1 or newer.
          - [Scipy](https://www.scipy.org/) version 1.4.0 or newer.
      - **universal_robots_hand_eye_calibration**
        - [**universal_robots_perform_hand_eye_calibration**][ur_perform_hand_eye_calibration-url] - Generate dataset and perform Hand-Eye calibration on the generated dataset.
          - **Dependencies:**
            - [numpy](https://numpy.org/) version 1.19.2 or newer
            - [OpenCV](https://opencv.org/) version 4.0.1 or newer.
            - [RTDE][rtde_guide-url] version 1.0 or newer.
            - [Scipy](https://www.scipy.org/) version 1.4.0 or newer.
    - [**downsample**][downsample-url]  - Downsample point cloud from a ZDF file.
      - **Dependencies:**
        - [numpy](https://numpy.org/) version 1.19.2 or newer
        - [pptk](https://github.com/heremaps/pptk) version 0.1.0 or newer
    - [**create_depth_map**][create_depth_map-url] - Read point cloud data from a ZDF file, convert it to OpenCV format, then extract and visualize depth map.
      - **Dependencies:**
        - [numpy](https://numpy.org/) version 1.19.2 or newer
        - [OpenCV](https://opencv.org/) version 4.0.1 or newer
    - [**mask_point_cloud**][mask_point_cloud-url] - Read point cloud data from a ZDF file, apply a binary mask, and visualize it.
      - **Dependencies:**
        - [numpy](https://numpy.org/) version 1.19.2 or newer
        - [matplotlib](https://matplotlib.org/) version 3.3.2 or newer
        - [pptk](https://github.com/heremaps/pptk) version 0.1.0 or newer
    - [**gamma_correction**][gamma_correction-url] - Modify gamma of 2D image.
      - **Dependencies:**
        - [numpy](https://numpy.org/) version 1.19.2 or newer
        - [OpenCV](https://opencv.org/) version 4.0.1 or newer
    - [**color_balance**][color_balance-url] - Balance color of 2D image.
      - **Dependencies:**
        - [numpy](https://numpy.org/) version 1.19.2 or newer
        - [matplotlib](https://matplotlib.org/) version 3.3.2 or newer

## Instructions

1. [**Install Zivid Software**](https://www.zivid.com/downloads).
Note: The samples require Zivid SDK v2 (minor version 2.1 or newer).

2. [**Install Zivid Python**](https://github.com/zivid/zivid-python).
Note: The recommended Python version for these samples is 3.7.

3. [**Download Zivid Sample Data**](https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/450363393/Sample+Data).

4. [Optional] Launch the Python IDE of your choice. Read our instructions on [**setting up Python**](https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/427556/Setting+up+Python).

5. Install the runtime requirements using IDE or command line:

       pip install -r requirements.txt

6. Add the directory `source` to PYTHONPATH. Navigate to the root of the repository and run:

    - PowerShell: `$env:PYTHONPATH=$env:PYTHONPATH + ";$PWD\source"`
    - cmd: `set PYTHONPATH="$PYTHONPATH;$PWD\source"`
    - bash: `export PYTHONPATH="$PYTHONPATH:$PWD/source"`

7. Open and run one of the samples.

## Support
If you need assistance with using Zivid cameras, visit our Knowledge Base at [https://help.zivid.com/](https://help.zivid.com/) or contact us at [customersuccess@zivid.com](mailto:customersuccess@zivid.com).

## Licence
Zivid Samples are distributed under the [BSD license](source/LICENSE).

[ci-badge]: https://img.shields.io/azure-devops/build/zivid-devops/701a6042-3865-4412-9f7f-78b846c1a406/3
[ci-url]: https://dev.azure.com/zivid-devops/python-samples/_build/latest?definitionId=3&branchName=master
[QuickCaptureTutorial-url]: source/camera/basic/QuickCaptureTutorial.md
[CompleteCaptureTutorial-url]: source/camera/basic/CaptureTutorial.md
[capture-url]: source/camera/basic/capture.py
[capture_2d-url]: source/camera/basic/capture_2d.py
[capture_assistant-url]: source/camera/basic/capture_assistant.py
[capture_from_file-url]: source/camera/basic/capture_from_file.py
[capture_with_settings_from_yml-url]: source/camera/basic/capture_with_settings_from_yml.py
[capture_hdr-url]: source/camera/basic/capture_hdr.py
[capture_hdr_complete_settings-url]: source/camera/basic/capture_hdr_complete_settings.py
[print_version_info-url]: source/camera/info_util_other/print_version_info.py
[capture_hdr_loop-url]: source/camera/advanced/capture_hdr_loop.py
[capture_hdr_separate_frames-url]: source/applications/basic/capture_hdr_separate_frames.py
[read_zdf_vis_3d-url]: source/applications/basic/visualization/read_zdf_vis_3d.py
[convert_zdf-url]: source/applications/basic/file_formats/convert_zdf.py
[read_iterate_zdf-url]: source/applications/basic/file_formats/read_iterate_zdf.py
[hand_eye_calibration-url]: source/applications/advanced/hand_eye_calibration
[calibrate_eye_to_hand-url]: source/applications/advanced/hand_eye_calibration/calibrate_eye_to_hand.py
[utilize_eye_in_hand_calibration-url]: source/applications/advanced/hand_eye_calibration/utilize_eye_in_hand_calibration.py
[pose_conversions-url]: source/applications/advanced/hand_eye_calibration/pose_conversions.py
[ur_perform_hand_eye_calibration-url]: source/applications/advanced/hand_eye_calibration/ur_hand_eye_calibration/universal_robots_perform_hand_eye_calibration.py
[rtde_guide-url]: https://www.universal-robots.com/how-tos-and-faqs/how-to/ur-how-tos/real-time-data-exchange-rtde-guide-22229/
[downsample-url]: source/applications/advanced/downsample.py
[create_depth_map-url]: source/applications/advanced/create_depth_map.py
[gamma_correction-url]: source/applications/advanced/gamma_correction.py
[color_balance-url]: source/applications/advanced/color_balance.py
[mask_point_cloud-url]: source/applications/advanced/mask_point_cloud.py
