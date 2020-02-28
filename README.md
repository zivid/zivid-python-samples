# python-samples

[![Build Status][ci-badge]][ci-url]

This repository contains additional **Python** code samples for **Zivid**.

The basic samples come with [**Zivid Python**](https://github.com/zivid/zivid-python) - the official Python package for Zivid 3D cameras.

## Samples list
- [**Hand-eye-calibration**](https://github.com/zivid/python-samples/tree/full-hand-eye-sample/hand-eye-calibration)
	- [**universal_robots_perform_hand_eye_calibration**](https://github.com/zivid/python-samples/blob/full-hand-eye-sample/hand-eye-calibration/universal_robots_perform_hand_eye_calibration.py) - Generate dataset and perform hand-eye calibration on generated dataset. 
	- **Dependencies:**
		- [OpenCV](https://opencv.org/) version 4.0.1 or newer.
		- [RTDE](https://www.universal-robots.com/how-tos-and-faqs/how-to/ur-how-tos/real-time-data-exchange-rtde-guide-22229/) version 1.0 or newer.
		- [Scipy](https://www.scipy.org/) version 1.4.0 or newer.
- [**capture_hdr_complete_settings**](https://github.com/zivid/python-samples/blob/master/capture_hdr_complete_settings.py) - Capture an HDR frame with fully configured settings for each frame.
- [**capture_hdr_loop**](https://github.com/zivid/python-samples/blob/master/capture_hdr_loop.py) - Capture HDR frames in a loop (while actively changing some HDR settings).
- [**capture_hdr_separate_frames**](https://github.com/zivid/python-samples/blob/master/capture_hdr_separate_frames.py) - Capture several individual frames and merge them into one HDR frame.
- [**capture_save_ply**](https://github.com/zivid/python-samples/blob/master/capture_save_ply.py) - Capture a ZDF point cloud and save it to PLY file format.
- [**connect_to_serial_number_camera**](https://github.com/zivid/python-samples/blob/master/connect_to_serial_number_camera.py) - Connect to a specific Zivid camera based on its serial number.
- [**convert_zdf**](https://github.com/zivid/python-samples/blob/master/convert_zdf.py) - Convert from ZDF to your preferred format (.ply, .csv, .txt, .png, .jpg, .bmp, .tiff).
- [**downsample**](https://github.com/zivid/python-samples/blob/master/downsample.py) - Import ZDF point cloud and downsample it.
- [**read_iterate_zdf**](https://github.com/zivid/python-samples/blob/master/read_iterate_zdf.py) - Import ZDF point cloud.
- [**read_zdf_vis_3d**](https://github.com/zivid/python-samples/blob/master/read_zdf_vis_3d.py) - Import ZDF point cloud and visualize it.
- [**utilize_eye_in_hand_calibration**](https://github.com/zivid/python-samples/blob/master/utilize_eye_in_hand_calibration.py) - Utilize the result of eye-in-hand calibration to transform (picking) point.
- [**read_zdf_without_zivid**](https://github.com/zivid/python-samples/blob/master/read_zdf_without_zivid.py) - Import ZDF point cloud without Zivid Software.
- [**zdf_2_csv_without_zivid**](https://github.com/zivid/python-samples/blob/master/zdf_2_csv_without_zivid.py) - Convert ZDF point cloud to CSV format without Zivid Software.
- [**zdf_2_ply_without_zivid**](https://github.com/zivid/python-samples/blob/master/zdf_2_ply_without_zivid.py) - Convert ZDF point cloud to PLY file format without Zivid Software.
- [**zdf_2_txt_without_zivid**](https://github.com/zivid/python-samples/blob/master/zdf_2_txt_without_zivid.py) - Convert ZDF point cloud to TXT format without Zivid Software.
- [**zdf_with_opencv**](https://github.com/zivid/python-samples/blob/master/zdf_2_opencv.py) - Import a ZDF point cloud and convert it to RGB image and Depth map in OpenCV format.

## Instructions

1. [**Install Zivid Software**](https://www.zivid.com/downloads).
Note: The version tested with Zivid cameras is 1.8.0.

2. [**Install Zivid Python**](https://github.com/zivid/zivid-python).

3. [Optional] Launch the Python IDE of your choice. Read our instructions on [**setting up Python**](https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/427556/Setting+up+Python).

4. Install the runtime requirements using IDE or command line:

       pip install -r requirements.txt

5. Open and run one of the samples.

## Support
If you need assistance with using Zivid cameras, visit our Knowledge Base at [https://help.zivid.com/](https://help.zivid.com/) or contact us at [customersuccess@zivid.com](mailto:customersuccess@zivid.com).

## Licence
Zivid Samples are distributed under the [BSD license](https://github.com/zivid/python-samples/blob/master/LICENSE).

[ci-badge]: https://img.shields.io/azure-devops/build/zivid-devops/376f5fda-ba80-4d6c-aaaa-cbcd5e0ad6c0/2/master.svg
[ci-url]: https://dev.azure.com/zivid-devops/python-samples/_build/latest?definitionId=2&branchName=master
