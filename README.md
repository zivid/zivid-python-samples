# python-samples

This repository contains **Python** code samples for **Zivid**.

[![Build Status][ci-badge]][ci-url]
![Zivid Image][header-image]

---

*Contents:*
[**Samples**](#Samples-list) |
[**Instructions**](#Instructions) |
[**Support**](#Support) |
[**Licence**](#Licence)

---

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
    - [**capture_hdr_print_normals**][capture_hdr_print_normals-url] - Capture Zivid point clouds, compute normals and print a subset.
  - **info_util_other**
    - [**print_version_info**][print_version_info-url] - Print version info about connected Zivid cameras and the installed Zivid SDK.
    - [**warm up**][warm_up_sample_url] - Short example of a basic way to warm up the camera with specified time and capture cycle.

- **applications**
  - **basic**
    - **visualization**
      - [**capture_hdr_vis_normals**][capture_hdr_vis_normals-url] - Capture Zivid point clouds, compute normals and convert to color map and display.
      - [**read_zdf_vis_3d**][read_zdf_vis_3d-url] - Read point cloud data from a ZDF file and visualize it.
        - **Dependencies:**
          - [Open3D][open-3d-url] version 0.12.0 or newer
          - [numpy][numpy-url] version 1.19.2 or newer
          - [matplotlib][matplotlib-url] version 3.3.2 or newer
    - **file_formats**
      - [**convert_zdf**][convert_zdf-url] - Convert point cloud data from a ZDF file to your preferred format (.ply, .csv, .txt, .png, .jpg, .bmp, .tiff).
        - **Dependencies:**
          - [numpy][numpy-url] version 1.19.2 or newer
          - [OpenCV][openCV-url] version 4.0.1 or newer.
      - [**read_iterate_zdf**][read_iterate_zdf-url] - Read point cloud data from a ZDF file, iterate through it, and extract individual points.
  - **advanced**
    - [**hand_eye_calibration**][hand_eye_calibration-url]
      - [**calibrate_hand_eye**][calibrate_hand_eye-url] - Perform Hand-Eye calibration.
        - **Dependencies:**
          - [numpy][numpy-url] version 1.19.2 or newer
      - [**utilize_eye_in_hand_calibration**][utilize_eye_in_hand_calibration-url] - Transform a single data point or entire point cloud from the camera frame to the robot base frame using the Eye-in-Hand calibration matrix.
        - **Dependencies:**
          - [numpy][numpy-url] version 1.19.2 or newer
          - [OpenCV][openCV-url] version 4.0.1 or newer.
      - [**pose_conversions**][pose_conversions-url] - Convert to/from Transformation Matrix (Rotation Matrix + Translation Vector).
        - **Dependencies:**
          - [numpy][numpy-url] version 1.19.2 or newer
          - [OpenCV][openCV-url] version 4.0.1 or newer.
          - [Scipy][scipy-url][scipy-url] version 1.4.0 or newer.
      - **universal_robots_hand_eye_calibration**
        - [**universal_robots_perform_hand_eye_calibration**][ur_perform_hand_eye_calibration-url] - Generate dataset and perform Hand-Eye calibration on the generated dataset.
          - **Dependencies:**
            - [numpy][numpy-url] version 1.19.2 or newer
            - [OpenCV][openCV-url] version 4.0.1 or newer.
            - [RTDE][rtde_guide-url] version 1.0 or newer.
            - [Scipy][scipy-url] version 1.4.0 or newer.
    - [**downsample**][downsample-url]  - Downsample point cloud from a ZDF file.
      - **Dependencies:**
        - [numpy][numpy-url] version 1.19.2 or newer
        - [Open3D][open-3d-url] version 0.12.0 or newer
    - [**create_depth_map**][create_depth_map-url] - Read point cloud data from a ZDF file, convert it to OpenCV format, then extract and visualize depth map.
      - **Dependencies:**
        - [numpy][numpy-url] version 1.19.2 or newer
        - [OpenCV][openCV-url] version 4.0.1 or newer
    - [**mask_point_cloud**][mask_point_cloud-url] - Read point cloud data from a ZDF file, apply a binary mask, and visualize it.
      - **Dependencies:**
        - [numpy][numpy-url] version 1.19.2 or newer
        - [matplotlib][matplotlib-url] version 3.3.2 or newer
        - [Open3D][open-3d-url] version 0.12.0 or newer
    - [**gamma_correction**][gamma_correction-url] - Capture 2D image with gamma correction.
      - **Dependencies:**
        - [numpy][numpy-url] version 1.19.2 or newer
        - [OpenCV][openCV-url] version 4.0.1 or newer
    - [**color_balance**][color_balance-url] - Balance color of 2D image.
      - **Dependencies:**
        - [numpy][numpy-url] version 1.19.2 or newer
        - [matplotlib][matplotlib-url] version 3.3.2 or newer

## Instructions

1. [**Install Zivid Software**][zivid-software-installation-url].
Note: The samples require Zivid SDK v2 (minor version 2.2 or newer).

2. [**Install Zivid Python**][install-zivid-python-url].
Note: The recommended Python version for these samples is 3.7.

3. [**Download Zivid Sample Data**][zivid-sample-data-url].

4. [Optional] Launch the Python IDE of your choice. Read our instructions on [**setting up Python**](https://support.zivid.com/latest/academy/samples/python/setting-up-python.html).

5. Install the runtime requirements using IDE or command line:

       pip install -r requirements.txt

6. Add the directory `source` to PYTHONPATH. Navigate to the root of the repository and run:

    - PowerShell: `$env:PYTHONPATH=$env:PYTHONPATH + ";$PWD\source"`
    - cmd: `set PYTHONPATH="$PYTHONPATH;$PWD\source"`
    - bash: `export PYTHONPATH="$PYTHONPATH:$PWD/source"`

7. Open and run one of the samples.

## Support
If you need assistance with using Zivid cameras, visit our [**Knowledge Base**][knowledge-base-url] or contact us at [customersuccess@zivid.com](mailto:customersuccess@zivid.com).

## Licence
Zivid Samples are distributed under the [BSD license](LICENSE).

[ci-badge]: https://img.shields.io/github/workflow/status/zivid/zivid-python-samples/Main%20CI%20workflow/master
[ci-url]: https://github.com/zivid/zivid-python-samples/actions?query=workflow%3A%22Main+CI+workflow%22+branch%3Amaster
[header-image]: https://www.zivid.com/hubfs/softwarefiles/images/zivid-generic-github-header.png

[QuickCaptureTutorial-url]: source/camera/basic/QuickCaptureTutorial.md
[CompleteCaptureTutorial-url]: source/camera/basic/CaptureTutorial.md
[capture-url]: source/camera/basic/capture.py
[capture_2d-url]: source/camera/basic/capture_2d.py
[capture_assistant-url]: source/camera/basic/capture_assistant.py
[capture_from_file-url]: source/camera/basic/capture_from_file.py
[capture_with_settings_from_yml-url]: source/camera/basic/capture_with_settings_from_yml.py
[capture_hdr-url]: source/camera/basic/capture_hdr.py
[capture_hdr_complete_settings-url]: source/camera/basic/capture_hdr_complete_settings.py
[capture_hdr_loop-url]: source/camera/advanced/capture_hdr_loop.py
[capture_hdr_print_normals-url]: source/camera/advanced/capture_hdr_print_normals.py
[print_version_info-url]: source/camera/info_util_other/print_version_info.py
[warm_up_sample_url]: source/camera/info_util_other/warm-up-sample.py

[capture_hdr_vis_normals-url]: source/applications/basic/visualization/capture_hdr_vis_normals.py
[read_zdf_vis_3d-url]: source/applications/basic/visualization/read_zdf_vis_3d.py
[convert_zdf-url]: source/applications/basic/file_formats/convert_zdf.py
[read_iterate_zdf-url]: source/applications/basic/file_formats/read_iterate_zdf.py
[hand_eye_calibration-url]: source/applications/advanced/hand_eye_calibration
[calibrate_hand_eye-url]: source/applications/advanced/hand_eye_calibration/calibrate_hand_eye.py
[utilize_eye_in_hand_calibration-url]: source/applications/advanced/hand_eye_calibration/utilize_eye_in_hand_calibration.py
[pose_conversions-url]: source/applications/advanced/hand_eye_calibration/pose_conversions.py
[ur_perform_hand_eye_calibration-url]: source/applications/advanced/hand_eye_calibration/ur_hand_eye_calibration/universal_robots_perform_hand_eye_calibration.py
[rtde_guide-url]: https://www.universal-robots.com/how-tos-and-faqs/how-to/ur-how-tos/real-time-data-exchange-rtde-guide-22229/
[downsample-url]: source/applications/advanced/downsample.py
[create_depth_map-url]: source/applications/advanced/create_depth_map.py
[mask_point_cloud-url]: source/applications/advanced/mask_point_cloud.py
[gamma_correction-url]: source/applications/advanced/gamma_correction.py
[color_balance-url]: source/applications/advanced/color_balance.py

[open-3d-url]: http://www.open3d.org/
[numpy-url]: https://numpy.org/
[matplotlib-url]: https://matplotlib.org/
[openCV-url]: https://opencv.org/
[scipy-url]: https://www.scipy.org/

[knowledge-base-url]: https://support.zivid.com/
[zivid-software-installation-url]: https://support.zivid.com/latest/academy/getting-started/zivid-software-installation.html
[zivid-sample-data-url]: https://support.zivid.com/latest/academy/samples/sample-data.html

[install-zivid-python-url]: https://github.com/zivid/zivid-python
