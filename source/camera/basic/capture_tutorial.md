# Capture Tutorial



---

*Contents:*
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
6. [Conclusion](#Conclusion)

---
## Introduction

This tutorial describes how to use the Zivid SDK to capture point clouds
and 2D images.

For MATLAB see [Zivid Capture Tutorial for
MATLAB](https://github.com/zivid/zivid-matlab-samples/blob/master/source/Camera/Basic/CaptureTutorial.md).

**Prerequisites**

  - Install [Zivid
    Software](https://support.zivid.com/latest//getting-started/software-installation.html).
  - For Python: install
    [zivid-python](https://github.com/zivid/zivid-python#installation)

## Initialize

Calling any of the APIs in the Zivid SDK requires initializing the Zivid
application and keeping it alive while the program runs.

-----

Note:

`Zivid::Application` must be kept alive while operating the Zivid
Camera. This is essentially the Zivid driver.

-----

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L11))

``` sourceCode python
app = zivid.Application()
```

## Connect

Now we can connect to the camera.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L15))

``` sourceCode python
camera = app.connect_camera()
```

### Connect - Specific Camera

Sometimes multiple cameras are connected to the same computer, but it
might be necessary to work with a specific camera in the code. This can
be done by providing the serial number of the wanted camera.

``` sourceCode python
camera = app.connect_camera(serial_number="2020C0DE")
```

-----

Note:

The serial number of your camera is shown in the Zivid Studio.

-----

You may also list all cameras connected to the computer, and view their
serial numbers through

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/info_util_other/print_version_info.py#L15-L17))

``` sourceCode python
cameras = app.cameras()
for camera in cameras:
	print(f"Camera Info:  {camera}")
```

### Connect - File Camera

You may want to experiment with the SDK, without access to a physical
camera. Minor changes are required to keep the sample working.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_from_file_camera.py#L18-L22))

``` sourceCode python
file_camera = Path() / get_sample_data_path() / "FileCameraZividOne.zfc"
camera = app.create_file_camera(file_camera)
```

-----

Note:

The quality of the point cloud you get from FileCameraZividOne.zfc is
not representative of the Zivid 3D cameras.

-----

## Configure

As with all cameras there are settings that can be configured. These may
be set manually, or you use our Capture Assistant.

### Capture Assistant

It can be difficult to know what settings to configure. Luckily we have
the Capture Assistant. This is available in the Zivid SDK to help
configure camera settings.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_assistant.py#L16-L22))

``` sourceCode python
suggest_settings_parameters = zivid.capture_assistant.SuggestSettingsParameters(
	max_capture_time=datetime.timedelta(milliseconds=1200),
	ambient_light_frequency=zivid.capture_assistant.SuggestSettingsParameters.AmbientLightFrequency.none,
)
print(f"Running Capture Assistant with parameters: {suggest_settings_parameters}")
settings = zivid.capture_assistant.suggest_settings(camera, suggest_settings_parameters)
```

There are only two parameters to configure with Capture Assistant:

1.  **Maximum Capture Time** in number of milliseconds.
    1.  Minimum capture time is 200 ms. This allows only one
        acquisition.
    2.  The algorithm will combine multiple acquisitions if the budget
        allows.
    3.  The algorithm will attempt to cover as much of the dynamic range
        in the scene as possible.
    4.  A maximum capture time of more than 1 second will get good
        coverage in most scenarios.
2.  **Ambient light compensation**
    1.  May restrict capture assistant to exposure periods that are
        multiples of the ambient light period.
    2.  60Hz is found in Japan, Americas, Taiwan, South Korea and
        Philippines.
    3.  50Hz is common in the rest of the world.

### Manual configuration

Another option is to configure settings manually. For more information
about what each settings does, please see [Camera
Settings](https://support.zivid.com/latest/rst/reference-articles/camera-settings.html).
Note that Zivid Two has a set of [standard
settings](https://support.zivid.com/latest//reference-articles/standard-acquisition-settings-zivid-two.html).

#### Single Acquisition

We can create settings for a single capture.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L19-L25))

``` sourceCode python
settings = zivid.Settings()
settings.experimental.engine = "phase"
settings.acquisitions.append(zivid.Settings.Acquisition())
settings.acquisitions[0].aperture = 5.66
settings.acquisitions[0].exposure_time = datetime.timedelta(microseconds=6500)
settings.processing.filters.outlier.removal.enabled = True
settings.processing.filters.outlier.removal.threshold = 5.0
```

#### Multi Acquisition HDR

We may also create settings to be used in an HDR capture.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr.py#L17))

``` sourceCode python
settings = zivid.Settings(acquisitions=[zivid.Settings.Acquisition(aperture=fnum) for fnum in (11.31, 5.66, 2.83)])
```

#### 2D Settings

It is possible to only capture a 2D image. This is faster than a 3D
capture. 2D settings are configured as follows.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_2d.py#L18-L27))

``` sourceCode python
settings_2d = zivid.Settings2D()
settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
settings_2d.acquisitions[0].exposure_time = datetime.timedelta(microseconds=30000)
settings_2d.acquisitions[0].aperture = 11.31
settings_2d.acquisitions[0].brightness = 1.80
settings_2d.acquisitions[0].gain = 2.0
settings_2d.processing.color.balance.red = 1.0
settings_2d.processing.color.balance.green = 1.0
settings_2d.processing.color.balance.blue = 1.0
settings_2d.processing.color.gamma = 1.0
```

### From File

Zivid Studio can store the current settings to .yml files. These can be
read and applied in the API. You may find it easier to modify the
settings in these (human-readable) yaml-files in your preferred editor.

``` sourceCode python
from sample_utils.paths import get_sample_data_path
from sample_utils.settings_from_file import get_settings_from_yaml
settings = get_settings_from_yaml("Settings.yml")
```

-----

Caution\!:

Zivid settings files must use .yml file extension ( not .yaml).

## Capture

Now we can capture a 3D image. Whether there is a single acquisition or
multiple acquisitions (HDR) is given by the number of `acquisitions` in
`settings`.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L29))

``` sourceCode python
with camera.capture(settings) as frame:
```

### Capture2D

If we only want to capture a 2D image, which is faster than 3D, we can
do so via the 2D API.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_2d.py#L31))

``` sourceCode python
with camera.capture(settings_2d) as frame_2d:
```

-----

Caution\!:

  - Zivid One+ camera has a time penalty when changing the capture mode
    (2D and 3D) if the 2D capture settings use brightness \> 0.  
    You can read more about it in [2D and 3D switching
    limitation](https://support.zivid.com/latest//support/2d-3d-switching-limitation.html).

## Save

We can now save our results.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L31-L34))

``` sourceCode python
data_file = "Frame.zdf"
frame.save(data_file)
```

The API detects which format to use. See [Point
Cloud](https://support.zivid.com/latest//reference-articles/point-cloud-structure-and-output-formats.html)
for a list of supported formats.

-----

Tip:

You can open and view `Frame.zdf` file in [Zivid
Studio](https://support.zivid.com/latest//getting-started/studio-guide.html).

### Save 2D

If we capture a 2D image, we can save it.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_2d.py#L34-L45))

``` sourceCode python
image = frame_2d.image_rgba()
image_file = "Image.png"
print(f"Saving image to file: {image_file}")
image.save(image_file)
```

## Conclusion

This tutorial shows how to use the Zivid SDK to connect to, configure,
capture, and save from the Zivid camera.
