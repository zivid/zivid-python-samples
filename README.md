# python-samples

[![Build Status](https://travis-ci.com/zivid/python-samples.svg?branch=master)](https://travis-ci.com/zivid/python-samples)

This repository contains additional **Python** code samples for **Zivid**.

The basic samples come with [**Zivid Python**](https://github.com/zivid/zivid-python) - the official Python package for Zivid 3D cameras.

## Samples list
- [**capture_hdr_complete_settings**](capture_hdr_complete_settings.py) - Capture an HDR frame with fully configured settings for each frame.
- [**capture_hdr_loop**](capture_hdr_loop.py) - Capture HDR frames in a loop (while actively changing some HDR settings).
- [**capture_hdr_separate_frames**](capture_hdr_separate_frames.py) - Capture several individual frames and merge them into one HDR frame.
- [**capture_save_ply**](capture_save_ply.py) - Capture a ZDF point cloud and save it to PLY file format.
- [**connect_to_serial_number_camera**](connect_to_serial_number_camera.py) - Connect to a specific Zivid camera based on its serial number.
- [**read_zdf**](read_zdf.py) - Import ZDF point cloud.
- [**read_zdf_without_zivid**](read_zdf_without_zivid.py) - Import ZDF point cloud without Zivid Software.
- [**zdf_2_csv**](zdf_2_csv.py) - Convert ZDF point cloud to CSV format.
- [**zdf_2_csv_without_zivid**](zdf_2_csv_without_zivid.py) - Convert ZDF point cloud to CSV format without Zivid Software.
- [**zdf_2_ply**](zdf_2_ply.py) - Convert ZDF point cloud to PLY file format.
- [**zdf_2_ply_without_zivid**](zdf_2_ply_without_zivid.py) - Convert ZDF point cloud to PLY file format without Zivid Software.
- [**zdf_2_txt**](zdf_2_txt.py) - Convert ZDF point cloud to TXT format.
- [**zdf_2_txt_without_zivid**](zdf_2_txt_without_zivid.py) - Convert ZDF point cloud to TXT format without Zivid Software.

## Instructions

1. [**Install Zivid Software**](https://www.zivid.com/downloads).
Note: The version tested with Zivid cameras is 1.2.0.

2. [**Install Zivid Python**](https://github.com/zivid/zivid-python).

3. Launch your Python IDE. Read our instructions on [**setting up Python**](https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/427556/Setting+up+Python).

4. Install the runtime requirements using IDE or command line:

       pip install -r requirements.txt

5. Open and run one of the samples.

## Support
If you need assistance with using Zivid cameras, visit our Knowledge Base at [https://help.zivid.com/](https://help.zivid.com/) or contact us at [customersuccess@zivid.com](mailto:customersuccess@zivid.com).

## Licence
Zivid Samples are distributed under the [BSD license](LICENSE).