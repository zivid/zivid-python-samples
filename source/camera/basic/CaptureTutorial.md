## Introduction

This tutorial describes how to use Zivid SDK to capture point clouds and 2D images.

1. [Initialize](#initialize)
2. [Connect](#connect)
   1. [Specific Camera](#connect---specific-camera)
   2. [Virtual Camera](#connect---virtual-camera)
3. [Configure](#configure)
   1. [Capture Assistant](#capture-assistant)
   2. [Manual Configuration](#manual-configuration)
      1. [Single](#single-frame)
      2. [HDR](#hdr-frame)
      3. [2D](#2d-settings)
   3. [From File](#from-file)
4. [Capture](#capture)
    1. [HDR](#capture-hdr)
    2. [2D](#capture-2d)
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

The serial number of your camera is shown in the Zivid Studio.

---

You may also list all cameras connected to the computer, and view their serial numbers through
```python
cameras = app.cameras()
for cam in cameras:
    print(f"Connecting camera: {cam.serialNumber()}")
```

### Connect - Virtual Camera

You may want to experiment with the SDK, without access to a physical camera. Minor changes are required to keep the sample working ([go to source][filecamera-url]).
```python
camera = app.create_file_camera((Path() / get_sample_data_path() / "FileCameraZividOne.zfc")
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
suggest_settings_parameters = SuggestSettingsParameters(
    max_capture_time=datetime.timedelta(milliseconds=1200),
    ambient_light_frequency=AmbientLightFrequency.none,
)
settings_list = zivid.capture_assistant.suggest_settings(
    camera, suggest_settings_parameters
)
```

These settings can be used in an [HDR capture](#capture-hdr), which we will discuss later.

As opposed to manual configuration of settings, there are only two parameters to consider with Capture Assistant.

1. **Maximum Capture Time** in number of milliseconds.
    1. Minimum capture time is 200ms. This allows only one frame to be captured.
    2. The algorithm will combine multiple frames if the budget allows.
    3. The algorithm will attempt to cover as much of the dynamic range in the scene as possible.
    4. A maximum capture time of more than 1 second will get good coverage in most scenarios.
2. **Ambient light compensation**
    1. May restrict capture assistant to exposure periods that are multiples of the ambient light period.
    2. 60Hz is found in (amongst others) Japan, Americas, Taiwan, South Korea and Philippines.
    3. 50Hz is found in most rest of the world.

### Manual configuration

We may choose to configure settings manually. For more information about what each settings does, please see [Zivid One+ Camera Settings][kb-camera_settings-url].

#### Single Frame

We can configure settings for an individual frame directly to the camera ([go to source][settings-url]).
```python
with camera.update_settings() as updater:
    updater.settings.iris = 20
    updater.settings.exposure_time = datetime.timedelta(microseconds=8333)
    updater.setting.brightness = 1
    updater.setting.gain = 1
    updater.setting.bidirectional = False
    updater.setting.filters.contrast.enabled = True
    updater.setting.filters.contrast.threshold = 5
    updater.setting.filters.gaussian.enabled = True
    updater.setting.filters.gaussian.sigma = 1.5
    updater.setting.filters.outlier.enabled = True
    updater.setting.filters.outlier.threshold = 5
    updater.setting.filters.reflection.enabled = True
    updater.setting.filters.saturated.enabled = True
    updater.setting.blue_balance = 1.081
    updater.setting.red_balance = 1.709
```

#### HDR Frame

We may also set a list of settings to be used in an [HDR capture](#capture-hdr) ([go to source][settingsHDR-url]).
```python
settings_list = [camera.settings for _ in range(3)]
settings_list[0].iris = 14
settings_list[1].iris = 21
settings_list[2].iris = 35
```

#### 2D Settings

It is possible to only capture a 2D image. This is faster than a 3D capture, and can be used . 2D settings are configured as follows ([go to source][settings2d-url]).
```python
settings_2d = zivid.Settings2D()
settings_2d.exposure_time = datetime.timedelta(microseconds=10000)
settings_2d.gain = 1
settings_2d.iris = 35
settings_2d.brightness = 1
```

### From File

Zivid Studio can store the current settings to .yml files. These can be read and applied in the API. You may find it easier to modify the settings in these (human-readable) yaml-files in your preferred editor.
```python
path_to_settings_file = Path()
camera.settings = _read_settings_from_file(path_to_settings_file/"Frame01.yml")
```
For this to work you need to implement the function for reading settings from file ([go to source][readsettings-url]).

## Capture

Now we can capture a frame. The default capture is a single 3D point cloud ([go to source][capture-url]).
```python
frame = camera.capture()
```

### Capture HDR

As was revealed in the [Capture Assistant](#capture-assistant) section, a capture may consist of multiple frames. In order to capture multiple frames, and combine them, we can do as follows ([go to source][captureHDR-url])
```python
hdr_frame = zivid.hdr.capture(camera, settings_list)
```
It is possible to [manually create](#hdr-frame) the `settings_list`, if not set via [Capture Assistant](#capture-assistant).

### Capture 2D

If we only want to capture a 2D image, which is faster than 3D, we can do so via the 2D API ([go to source][capture2d-url]).
```python
frame_2d = camera.capture_2d(settings_2d)
```

## Save

We can now save our results ([go to source][save-url]).
```python
frame.save("Result.zdf")
```
The API detects which format to use. See [Point Cloud][kb-point_cloud-url] for a list of supported formats.

## Save 2D

If we captured a 2D image, we can save it ([go to source][save2d-url]).
```python
frame_2d.image.save("Result.png")
```

## Conclusion

This tutorial shows how to use the Zivid SDK and Zivid Python to connect to, configure and capture from the Zivid camera.

[//]: ### "Recommended further reading"

[installation-instructions-url]: ../../../README.md#instructions
[start_app-url]: capture.py#L7
[connect-url]: capture.py#L8
[captureassistant-url]: capture_assistant.py#L11-L18
[settings-url]: capture.py#L10-L13
[settingsHDR-url]: capture_hdr.py#L9-L12
[kb-camera_settings-url]: https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/99713044/Zivid+One+Camera+Settings
[capture-url]: capture.py#L15
[capture2d-url]: capture_2d.py#L14
[settings2d-url]: capture_2d.py#L10-L12
[captureHDR-url]: capture_assistant.py#L20
[save-url]: capture.py#L16
[save2d-url]: capture_2d.py#L15-L16
[readsettings-url]: ../../applications/basic/capture_hdr_loop.py#L15-L34
[kb-point_cloud-url]: https://zivid.atlassian.net/wiki/spaces/ZividKB/pages/427396/Point+Cloud
[filecamera-url]: capture_from_file.py#L7
