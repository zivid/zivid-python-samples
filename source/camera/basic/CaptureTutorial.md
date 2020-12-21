## Introduction

This tutorial describes how to use Zivid SDK to capture point clouds and 2D images.

1. [Initialize](#initialize)
2. [Connect](#connect)
   1. [Specific Camera](#connect---specific-camera)
   2. [File Camera](#connect---file-camera)
3. [Configure](#configure)
   1. [Capture Assistant](#capture-assistant)
   2. [Manual Configuration](#manual-configuration)
      1. [Single](#single-frame)
      2. [HDR](#hdr-frame)
      3. [2D](#2d-settings)
   3. [From File](#from-file)
4. [Capture](#capture)
    1. [2D](#capture-2d)
5. [Save](#save)
    1. [2D](#save-2d)

### Prerequisites

You should have installed Zivid SDK, Zivid Python, and Python samples. For more details see [Instructions][installation-instructions-url].

## Initialize

Before calling any of the APIs in the Zivid SDK, we have to start up the Zivid Application. This is done through a simple instantiation of the application ([go to source][start_app-url]).
```python
app = zivid.Application()
```

## Connect

Now we can connect to the camera ([go to source][connect-url]).
```python
camera = app.connect_camera()
```

### Connect - Specific Camera

Sometime multiple cameras are connected to the same computer. It might then be necessary to work with a specific camera in the code. This can be done by providing the serial number of the wanted camera.
```python
camera = app.connect_camera(serial_number="2020C0DE")
```

---
**Note** 

The serial number of your camera is shown in Zivid Studio.

---

You may also list all cameras connected to the computer, and view their serial numbers through
```python
cameras = app.cameras()
for cam in cameras:
    print(f"Connecting camera: {cam.serialNumber()}")
```

### Connect - File Camera

You may want to experiment with the SDK, without access to a physical camera. Minor changes are required to keep the sample working ([go to source][filecamera-url]).
```python
camera_file = Path() / get_sample_data_path() / "FileCameraZividOne.zfc"
camera = app.create_file_camera(camera_file)
```

---
**Note**

The quality of the point cloud you get from *FileCameraZividOne.zfc* is not representative of the Zivid One+.

---

## Configure

As with all cameras there are settings that can be configured. These may be set manually, or you use our Capture Assistant.

### Capture Assistant

It can be difficult to know what settings to configure. Luckily we have the Capture Assistant. This is available in the Zivid SDK to help configure camera settings ([go to source][captureassistant-url]).
```python
suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
    max_capture_time=datetime.timedelta(milliseconds=1200),
    ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
)
settings = zivid.capture_assistant.suggest_settings(
    camera, suggest_settings_parameters
)
```

There are only two parameters to configure with Capture Assistant:

1. **Maximum Capture Time** in number of milliseconds.
    1. Minimum capture time is 200 ms. This allows only one acquisition.
    2. The algorithm will combine multiple acquisitions if the budget allows.
    3. The algorithm will attempt to cover as much of the dynamic range in the scene as possible.
    4. A maximum capture time of more than 1 second will get good coverage in most scenarios.
2. **Ambient light compensation**
    1. May restrict capture assistant to exposure periods that are multiples of the ambient light period.
    2. 60Hz is found in (amongst others) Japan, Americas, Taiwan, South Korea and Philippines.
    3. 50Hz is common in the rest of the world.

### Manual configuration

We may choose to configure settings manually. For more information about what each settings does, please see [Zivid One+ Camera Settings][kb-camera_settings-url].

#### Single Acquisition

We can create settings for a single capture ([go to source][settings-url]).
```python
settings = zivid.Settings()
settings.acquisitions.append(zivid.Settings.Acquisition())
settings.acquisitions[0].aperture = 5.66
settings.acquisitions[0].exposure_time = datetime.timedelta(microseconds=8333)
settings.processing.filters.outlier.removal.enabled = True
settings.processing.filters.outlier.removal.threshold = 5.0
```

#### Multi Acquisition HDR

We may also create settings to be used in an HDR capture ([go to source][settings-hdr-url]).
```python
settings = zivid.Settings(acquisitions=[zivid.Settings.Acquisition(aperture=fnum) for fnum in (11.31, 5.66, 2.83)])
```

#### 2D Settings

It is possible to only capture a 2D image. This is faster than a 3D capture. 2D settings are configured as follows ([go to source][settings2d-url]).
```python
settings_2d = zivid.Settings2D()
settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
settings_2d.acquisitions[0].exposure_time = datetime.timedelta(microseconds=10000)
settings_2d.acquisitions[0].aperture = 2.83
settings_2d.acquisitions[0].gain = 1.0
settings_2d.acquisitions[0].brightness = 1.0
settings_2d.processing.color.balance.red = 1.0
settings_2d.processing.color.balance.green = 1.0
settings_2d.processing.color.balance.blue = 1.0
settings_2d.processing.color.gamma = 1.0
```

### From File

Zivid Studio can store the current settings to .yml files. These can be read and applied in the API. You may find it easier to modify the settings in these (human-readable) yaml-files in your preferred editor ([go to source][settings_from_file-url]).
```python
from sample_utils.paths import get_sample_data_path
from sample_utils.settings_from_file import get_settings_from_yaml
settings = get_settings_from_yaml("Settings.yml")
```

## Capture

Now we can capture a 3D image. Whether there is a single acquisition or multiple acquisitions (HDR) is given by the number of `acquisitions` in `settings` ([go to source][capture-url]).
```python
frame = camera.capture(settings)
```

### Capture 2D

If we only want to capture a 2D image, which is faster than 3D, we can do so via the 2D API ([go to source][capture2d-url]).
```python
frame_2d = camera.capture(settings_2d)
```

## Save

We can now save our results ([go to source][save-url]).
```python
frame.save("Frame.zdf")
```
The API detects which format to use. See [Point Cloud][kb-point_cloud-url] for a list of supported formats.

### Save 2D

If we captured a 2D image, we can save it ([go to source][save2d-url]).
```python
frame_2d.image_rgba().save("Image.png")
```

## Conclusion

This tutorial shows how to use the Zivid SDK and Zivid Python to connect to, configure, capture and save from the Zivid camera.

[//]: ### "Recommended further reading"

[installation-instructions-url]: ../../../README.md#instructions
[start_app-url]: capture.py#L10
[connect-url]: capture.py#L13
[captureassistant-url]: capture_assistant.py#L15-L21
[settings-url]: capture.py#L16-L21
[settings-hdr-url]: capture_hdr.py#L17
[kb-camera_settings-url]: https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/450265335/Settings
[capture-url]: capture.py#L24
[capture2d-url]: capture_2d.py#L28
[settings2d-url]: capture_2d.py#L16-L25
[save-url]: capture.py#L25-L27
[save2d-url]: capture_2d.py#L38-L40
[settings_from_file-url]: capture_with_settings_from_yml.py#L20-L22
[kb-point_cloud-url]: https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/520061383/Point+Cloud
[filecamera-url]: capture_from_file.py#L18
