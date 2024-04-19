# Python samples

This repository contains python code samples for Zivid SDK v2.12.0. For
tested compatibility with earlier SDK versions, please check out
[accompanying
releases](https://github.com/zivid/zivid-python-samples/tree/master/../../releases).

![image](https://www.zivid.com/hubfs/softwarefiles/images/zivid-generic-github-header.png)



---

*Contents:*
[**Tutorials**](#Tutorials-list) |
[**Samples**](#Samples-list) |
[**Installation**](#Installation) |
[**Support**](#Support) |
[**License**](#License)

---



## Tutorials list

  - [quick\_capture\_tutorial](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/quick_capture_tutorial.md)
  - [capture\_tutorial](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_tutorial.md)
  - [point\_cloud\_tutorial](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/point_cloud_tutorial.md)

## Samples list

There are two main categories of samples: **Camera** and
**Applications**. The samples in the **Camera** category focus only on
how to use the camera. The samples in the **Applications** category use
the output generated by the camera, such as the 3D point cloud, a 2D
image or other data from the camera. These samples shows how the data
from the camera can be used.

  - **camera**
      - **basic**
          - [capture](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture.py) - Capture point clouds, with color, from the Zivid camera.
          - [capture\_2d](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_2d.py) - Capture 2D images from the Zivid camera.
          - [capture\_2d\_with\_settings\_from\_yml](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_2d_with_settings_from_yml.py) - Capture 2D images from the Zivid camera, with settings
            from YML file.
          - [capture\_assistant](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_assistant.py) - Use Capture Assistant to capture point clouds, with color,
            from the Zivid camera.
          - [capture\_from\_file\_camera](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_from_file_camera.py) - Capture point clouds, with color, with the Zivid file
            camera.
          - [capture\_hdr](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_hdr.py) - Capture point clouds, with color, from the Zivid camera.
          - [capture\_hdr\_complete\_settings](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_hdr_complete_settings.py) - Capture point clouds, with color, from the Zivid camera
            with fully configured settings.
          - [capture\_with\_settings\_from\_yml](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_with_settings_from_yml.py) - Capture point clouds, with color, from the Zivid camera,
            with settings from YML file.
      - **advanced**
          - [capture\_2d\_and\_3d](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/advanced/capture_2d_and_3d.py) - Capture 2D and 3D separately with the Zivid camera.
          - [capture\_hdr\_loop](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/advanced/capture_hdr_loop.py) - Cover the same dynamic range in a scene with different
            acquisition settings to optimize for quality, speed, or to
            find a compromise.
          - [capture\_hdr\_print\_normals](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/advanced/capture_hdr_print_normals.py) - Capture Zivid point clouds, compute normals and print a
            subset.
      - **info\_util\_other**
          - [camera\_info](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/info_util_other/camera_info.py) - Print version information for Python, zivid-python and
            Zivid SDK, then list cameras and print camera info and state
            for each connected camera.
          - [camera\_user\_data](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/info_util_other/camera_user_data.py) - Store user data on the Zivid camera.
          - [capture\_with\_diagnostics](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/info_util_other/capture_with_diagnostics.py) - Capture point clouds, with color, from the Zivid camera,
            with settings from YML file and diagnostics enabled.
          - [firmware\_updater](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/info_util_other/firmware_updater.py) - Update firmware on the Zivid camera.
          - [get\_camera\_intrinsics](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/info_util_other/get_camera_intrinsics.py) - Read intrinsic parameters from the Zivid camera (OpenCV
            model) or estimate them from the point cloud.
          - [warmup](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/info_util_other/warmup.py) - A basic warm-up method for a Zivid camera with specified
            time and capture cycle.
      - **maintenance**
          - [correct\_camera\_in\_field](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/maintenance/correct_camera_in_field.py) - Correct the dimension trueness of a Zivid camera.
          - [reset\_camera\_in\_field](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/maintenance/reset_camera_in_field.py) - Reset infield correction on a camera.
          - [verify\_camera\_in\_field](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/maintenance/verify_camera_in_field.py) - Check the dimension trueness of a Zivid camera.
          - [verify\_camera\_in\_field\_from\_zdf](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/maintenance/verify_camera_in_field_from_zdf.py) - Check the dimension trueness of a Zivid camera from a ZDF
            file.
  - **applications**
      - **basic**
          - **visualization**
              - [capture\_from\_file\_camera\_vis\_3d](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/basic/visualization/capture_from_file_camera_vis_3d.py) - Capture point clouds, with color, with the Zivid file
                camera.
              - [capture\_hdr\_vis\_normals](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/basic/visualization/capture_hdr_vis_normals.py) - Capture Zivid point clouds, compute normals and
                convert to color map and display.
              - [capture\_vis\_3d](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/basic/visualization/capture_vis_3d.py) - Capture point clouds, with color, from the Zivid
                camera, and visualize it.
              - [project\_image\_start\_and\_stop](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/basic/visualization/project_image_start_and_stop.py) - Start the Image Projection and Stop it.
              - [read\_and\_project\_image](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/basic/visualization/read_and_project_image.py) - Read a 2D image from file and project it using the
                camera projector.
              - [read\_zdf\_vis\_3d](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/basic/visualization/read_zdf_vis_3d.py) - Read point cloud data from a ZDF file and visualize
                it.
          - **file\_formats**
              - [convert\_zdf](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/basic/file_formats/convert_zdf.py) - Convert point cloud data from a ZDF file to your
                preferred format (PLY, CSV, TXT, PNG, JPG, BMP, TIFF).
              - [read\_iterate\_zdf](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/basic/file_formats/read_iterate_zdf.py) - Read point cloud data from a ZDF file, iterate through
                it, and extract individual points.
      - **advanced**
          - [auto\_2d\_settings](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/auto_2d_settings.py) - Automatically find 2D settings for a 2D capture by using a
            Zivid calibration board.
          - [color\_balance](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/color_balance.py) - Balance color of a 2D image by using a Zivid calibration
            board.
          - [create\_depth\_map](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/create_depth_map.py) - Read point cloud data from a ZDF file, convert it to
            OpenCV format, then extract and visualize depth map.
          - [downsample](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/downsample.py) - Downsample point cloud from a ZDF file.
          - [gamma\_correction](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/gamma_correction.py) - Capture 2D image with gamma correction.
          - [get\_checkerboard\_pose\_from\_zdf](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/get_checkerboard_pose_from_zdf.py) - Read point cloud data of a Zivid calibration board from a
            ZDF file, estimate the
          - [hand\_eye\_calibration](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/hand_eye_calibration/hand_eye_calibration.py) - Perform Hand-Eye calibration.
          - [mask\_point\_cloud](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/mask_point_cloud.py) - Read point cloud data from a ZDF file, apply a binary
            mask, and visualize it.
          - [project\_and\_find\_marker](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/project_and_find_marker.py) - Show a marker using the projector, capture a set of 2D
            images to find the marker coordinates (2D and 3D).
          - [reproject\_points](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/reproject_points.py) - Illuminate checkerboard (Zivid Calibration Board) corners
            by getting checkerboard pose
          - [roi\_box\_via\_checkerboard](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/roi_box_via_checkerboard.py) - Filter the point cloud based on a ROI box given relative
            to the Zivid Calibration Board.
          - **hand\_eye\_calibration**
              - [pose\_conversions](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/hand_eye_calibration/pose_conversions.py) - Convert to/from Transformation Matrix (Rotation Matrix
                + Translation Vector).
              - [robodk\_hand\_eye\_calibration](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/hand_eye_calibration/robodk_hand_eye_calibration/robodk_hand_eye_calibration.py) - Generate a dataset and perform hand-eye calibration
                using the Robodk interface.
              - [utilize\_hand\_eye\_calibration](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/hand_eye_calibration/utilize_hand_eye_calibration.py) - Transform single data point or entire point cloud from
                camera to robot base reference frame using Hand-Eye
                calibration
              - [verify\_hand\_eye\_with\_visualization](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/hand_eye_calibration/verify_hand_eye_with_visualization.py) - Verify hand-eye calibration by transforming all
                dataset point clouds and
              - **ur\_hand\_eye\_calibration**
                  - [universal\_robots\_perform\_hand\_eye\_calibration](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/hand_eye_calibration/ur_hand_eye_calibration/universal_robots_perform_hand_eye_calibration.py) - Script to generate a dataset and perform hand-eye
                    calibration using a Universal Robot UR5e robot.
  - **sample\_utils**
      - [calibration\_board\_utils](https://github.com/zivid/zivid-python-samples/tree/master/source/sample_utils/calibration_board_utils.py) - Utility functions for the Zivid calibration board.
      - [display](https://github.com/zivid/zivid-python-samples/tree/master/source/sample_utils/display.py) - Display relevant data for Zivid Samples.
      - [paths](https://github.com/zivid/zivid-python-samples/tree/master/source/sample_utils/paths.py) - Get relevant paths for Zivid Samples.
      - [robodk\_tools](https://github.com/zivid/zivid-python-samples/tree/master/source/sample_utils/robodk_tools.py) - Robot Control Module
      - [save\_load\_matrix](https://github.com/zivid/zivid-python-samples/tree/master/source/sample_utils/save_load_matrix.py) - try:
      - [white\_balance\_calibration](https://github.com/zivid/zivid-python-samples/tree/master/source/sample_utils/white_balance_calibration.py) - Balance color for 2D capture using white surface as reference.
  - **applications**
      - **advanced**
          - **robot\_guidance**
              - [robodk\_robot\_guidance](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/robot_guidance/robodk_robot_guidance.py) - Guide the robot to follow a path on the Zivid
                Calibration Board.
          - **verify\_hand\_eye\_calibration**
              - [robodk\_verify\_hand\_eye\_calibration](https://github.com/zivid/zivid-python-samples/tree/master/source/applications/advanced/verify_hand_eye_calibration/robodk_verify_hand_eye_calibration.py) - Perform a touch test with a robot to verify Hand-Eye
                Calibration using the RoboDK interface.

## Installation

-----

Note:

The recommended Python version for these samples is 3.7 - 3.9.

-----

1.  [Install Zivid
    Software](https://support.zivid.com/latest//getting-started/software-installation.html).

2.  [Download Zivid Sample
    Data](https://support.zivid.com/latest//api-reference/samples/sample-data.html).

3.  Install the runtime requirements using IDE or command line:
    
    ``` sourceCode bash
    pip install -r requirements.txt
    ```

4.  Add the directory source to PYTHONPATH. Navigate to the root of the
    repository and run:
    
      - PowerShell: `$env:PYTHONPATH=$env:PYTHONPATH + ";$PWD\\source"`
      - cmd: `set PYTHONPATH="$PYTHONPATH;$PWD\\source"`
      - bash: `export PYTHONPATH="$PYTHONPATH:$PWD/source"`

5.  Open and run one of the samples.

## Support

For more information about the Zivid cameras, please visit our
[Knowledge Base](https://support.zivid.com/latest). If you run into any
issues please check out
[Troubleshooting](https://support.zivid.com/latest/support/troubleshooting.html).

## License

Zivid Samples are distributed under the [BSD
license](https://github.com/zivid/zivid-python-samples/tree/master/LICENSE).
