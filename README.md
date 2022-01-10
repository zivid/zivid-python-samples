# Python samples

This repository contains C++ code samples for Zivid SDK v2.7.0. For
tested compatibility with earlier SDK versions, please check out
[accompanying
releases](https://github.com/zivid/zivid-python-samples/tree/master/../../releases).

![image](https://www.zivid.com/hubfs/softwarefiles/images/zivid-generic-github-header.png)



---

*Contents:*
[**Samples**](#Samples-list) |
[**Installation**](#Installation) |
[**Support**](#Support) |
[**License**](#License)

---
## Samples list

There are two main categories of samples: **Camera** and
**Applications**. The samples in the **Camera** category focus only on
how to use the camera. The samples in the **Applications** category use
the output generated by the camera, such as the 3D point cloud, a 2D
image or other data from the camera. These samples shows how the data
from the camera can be used.

[QuickCaptureTutorial-url]: source/camera/basic/quick_capture_tutorial.md
[CompleteCaptureTutorial-url]: source/camera/basic/capture_tutorial.md

  - **camera**
      - **basic** ([quick tutorial](source/camera/basic/quick_capture_tutorial.md) / [complete tutorial](source/camera/basic/capture_tutorial.md))
          - [capture\_hdr\_complete\_settings](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr_complete_settings.py) - Capture point clouds, with color, from the Zivid camera
            with fully configured settings.
          - [capture\_assistant](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_assistant.py) - Use Capture Assistant to capture point clouds, with color,
            from the Zivid camera.
          - [capture\_from\_file\_camera](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_from_file_camera.py) - Capture point clouds, with color, from the Zivid file
            camera.
          - [capture\_hdr](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr.py) - Capture point clouds, with color, from the Zivid camera.
          - [capture\_2d](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_2d.py) - Capture 2D images from the Zivid camera.
          - [capture\_with\_settings\_from\_yml](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_with_settings_from_yml.py) - Capture point clouds, with color, from the Zivid camera,
            with settings from YML file.
          - [capture](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py) - Capture point clouds, with color, from the Zivid camera.
      - **advanced**
          - [capture\_hdr\_print\_normals](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/advanced/capture_hdr_print_normals.py) - Capture Zivid point clouds, compute normals and print a
            subset.
          - [capture\_hdr\_loop](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/advanced/capture_hdr_loop.py) - Cover the same dynamic range in a scene with different
            acquisition settings to optimize for quality, speed, or to
            find a compromise.
      - **info\_util\_other**
          - [warmup](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/info_util_other/warmup.py) - A basic warm-up method for a Zivid camera with specified
            time and capture cycle.
          - [capture\_with\_diagnostics](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/info_util_other/capture_with_diagnostics.py) - Capture point clouds, with color, from the Zivid camera,
            with settings from YML file and diagnostics enabled.
          - [print\_version\_info](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/info_util_other/print_version_info.py) - Print version information for Python, zivid-python and
            Zivid SDK, then list cameras and print camera info for each
            connected camera.
  - **applications**
      - **basic**
          - **visualization**
              - [capture\_hdr\_vis\_normals](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/visualization/capture_hdr_vis_normals.py) - Capture Zivid point clouds, compute normals and
                convert to color map and display.
              - [read\_zdf\_vis\_3d](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/visualization/read_zdf_vis_3d.py) - Read point cloud data from a ZDF file and visualize
                it.
          - **file\_formats**
              - [read\_iterate\_zdf](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/file_formats/read_iterate_zdf.py) - Read point cloud data from a ZDF file, iterate through
                it, and extract individual points.
              - [convert\_zdf](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/file_formats/convert_zdf.py) - Convert point cloud data from a ZDF file to your
                preferred format (.ply, .csv, .txt, .png, .jpg, .bmp,
                .tiff).
      - **advanced**
          - [create\_depth\_map](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/create_depth_map.py) - Read point cloud data from a ZDF file, convert it to
            OpenCV format, then extract and visualize depth map.
          - [downsample](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/downsample.py) - Downsample point cloud from a ZDF file.
          - [mask\_point\_cloud](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/mask_point_cloud.py) - Read point cloud data from a ZDF file, apply a binary
            mask, and visualize it.
          - [hand\_eye\_calibration](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/hand_eye_calibration/hand_eye_calibration.py) - Perform Hand-Eye calibration.
          - [gamma\_correction](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/gamma_correction.py) - Capture 2D image with gamma correction.
          - [color\_balance](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/color_balance.py) - Balance color of 2D image.
          - **hand\_eye\_calibration**
              - [pose\_conversions](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/hand_eye_calibration/pose_conversions.py) - Convert to/from Transformation Matrix (Rotation Matrix
                + Translation Vector).
              - [utilize\_hand\_eye\_calibration](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/hand_eye_calibration/utilize_hand_eye_calibration.py) - Transform a single data point or entire point cloud
                from the camera frame to the robot base frame using the
                Hand-Eye calibration matrix.
              - **ur\_hand\_eye\_calibration**
                  - [universal\_robots\_perform\_hand\_eye\_calibration](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/advanced/hand_eye_calibration/ur_hand_eye_calibration/universal_robots_perform_hand_eye_calibration.py) - Script to generate a dataset and perform hand-eye
                    calibration using a Universal Robot UR5e robot.
  - **sample\_utils**
      - [paths](https://github.com/zivid/zivid-python-samples/tree/master//source/sample_utils/paths.py) - Get relevant paths for Zivid Samples.
      - [display](https://github.com/zivid/zivid-python-samples/tree/master//source/sample_utils/display.py) - Display relevant data for Zivid Samples.

## Installation

1.  [Install Zivid
    Software](https://support.zivid.com/latest//getting-started/software-installation.html)

2.  [Install Zivid Python](https://github.com/zivid/zivid-python). Note:
    The recommended Python version for these samples is 3.8.

3.  [Download Zivid Sample
    Data](https://support.zivid.com/latest//api-reference/samples/sample-data.html)

4.  \[Optional\] Launch the Python IDE of your choice. Read our
    instructions on [setting up
    Python](https://support.zivid.com/latest//api-reference/samples/python/setting-up-python.html).

5.  Install the runtime requirements using IDE or command line:
    
    ``` sourceCode 
    pip install -r requirements.txt
    ```

6.  Add the directory source to PYTHONPATH. Navigate to the root of the
    repository and run:

>   - PowerShell: `$env:PYTHONPATH=$env:PYTHONPATH + ";$PWD\source"`
>   - cmd: `set PYTHONPATH="$PYTHONPATH;$PWD\source"`
>   - bash: `export PYTHONPATH="$PYTHONPATH:$PWD/source"`

7.  Open and run one of the samples.

## Support

For more information about the Zivid cameras, please visit our
[Knowledge Base](https://support.zivid.com/latest). If you run into any
issues please check out
[Troubleshooting](https://support.zivid.com/latest/rst/support/troubleshooting.html).

## License

Zivid Samples are distributed under the [BSD
license](https://github.com/zivid/zivid-python-samples/tree/master/LICENSE).
