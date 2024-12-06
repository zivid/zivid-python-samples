# Capture Tutorial

Note\! This tutorial has been generated for use on Github. For original
tutorial see:
[capture\_tutorial](https://support.zivid.com/latest/academy/camera/capture-tutorial.html)



---

*Contents:*
[**Introduction**](#Introduction) |
[**Initialize**](#Initialize) |
[**Connect**](#Connect) |
[**Configure**](#Configure) |
[**Capture**](#Capture) |
[**Save**](#Save) |
[**Multithreading**](#Multithreading) |
[**Conclusion**](#Conclusion)

---



## Introduction

This tutorial describes how to use the Zivid SDK to capture point clouds
and 2D images.

For MATLAB see [Zivid Capture Tutorial for
MATLAB](https://github.com/zivid/zivid-matlab-samples/blob/master/source/Camera/Basic/CaptureTutorial.md).

-----

Tip:

> If you prefer watching a video, our webinar [Making 3D captures easy -
> A tour of Zivid Studio and Zivid
> SDK](https://www.zivid.com/webinars-page?wchannelid=ffpqbqc7sg&wmediaid=ce68dbjldk)
> covers the same content as the Capture Tutorial.

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
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L10))

``` sourceCode python
app = zivid.Application()
```

## Connect

Now we can connect to the camera.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L13))

``` sourceCode python
camera = app.connect_camera()
```

### Specific Camera

Sometimes multiple cameras are connected to the same computer, but it
might be necessary to work with a specific camera in the code. This can
be done by providing the serial number of the wanted camera.

``` sourceCode python
camera = app.connect_camera(serial_number="2020C0DE")
```

-----

Note:

> The serial number of your camera is shown in the Zivid Studio.

-----

You may also list all cameras connected to the computer, and view their
serial numbers through

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/info_util_other/camera_info.py#L16-L19))

``` sourceCode python
cameras = app.cameras()
for camera in cameras:
	print(f"Camera Info:  {camera.info}")
	print(f"Camera State: {camera.state}")
```

### File Camera

The file camera option allows you to experiment with the SDK without
access to a physical camera. The file cameras can be found in [Sample
Data](https://support.zivid.com/latest/api-reference/samples/sample-data.html)
where there are multiple file cameras to choose from. Each file camera
demonstrates a use case within one of the main applications of the
respective camera model. The example below shows how to create a file
camera using the Zivid 2 M70 file camera from [Sample
Data](https://support.zivid.com/latest/api-reference/samples/sample-data.html).

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_from_file_camera.py#L33))

``` sourceCode python
default=get_sample_data_path() / "FileCameraZivid2M70.zfc",
```

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_from_file_camera.py#L48))

``` sourceCode python
camera = app.create_file_camera(file_camera)
```

The acquisition settings should be initialized like shown below, but you
are free to alter the processing settings.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_from_file_camera.py#L51-L59))

``` sourceCode python
settings = zivid.Settings()
settings.acquisitions.append(zivid.Settings.Acquisition())
settings.processing.filters.smoothing.gaussian.enabled = True
settings.processing.filters.smoothing.gaussian.sigma = 1
settings.processing.filters.reflection.removal.enabled = True
settings.processing.filters.reflection.removal.mode = "global"
settings.processing.color.balance.red = 1.0
settings.processing.color.balance.green = 1.0
settings.processing.color.balance.blue = 1.0
```

You can read more about the file camera option in [File
Camera](https://support.zivid.com/latest/academy/camera/file-camera.html).

## Configure

As with all cameras there are settings that can be configured.

### Presets

The recommendation is to use
[Presets](https://support.zivid.com/latest/reference-articles/presets-settings.html)
available in Zivid Studio and as .yml files (see `load_yml_label`
below). Alternatively, you can use our Capture Assistant, or you may
configure the settings manually.

### Capture Assistant

It can be difficult to know what settings to configure. Luckily we have
the Capture Assistant. This is available in the Zivid SDK to help
configure camera settings.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_assistant.py#L17-L23))

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
Settings](https://support.zivid.com/latest/reference-articles/camera-settings.html).
Then, the next step it's [Capturing High Quality Point
Clouds](https://support.zivid.com/latest/academy/camera/capturing-high-quality-point-clouds.html)

#### Single Acquisition

We can create settings for a single acquisition capture.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L16-L17))

``` sourceCode python
settings = zivid.Settings()
settings.acquisitions.append(zivid.Settings.Acquisition())
```

#### Multi Acquisition HDR

We may also create settings to be used in a multi-acquisition HDR
capture.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr.py#L18))

``` sourceCode python
settings = zivid.Settings(acquisitions=[zivid.Settings.Acquisition(aperture=fnum) for fnum in (11.31, 5.66, 2.83)])
```

Fully configured settings are demonstrated below.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr_complete_settings.py#L99-L152))

``` sourceCode python
print("Configuring settings for capture:")
settings = zivid.Settings()
settings.engine = zivid.Settings.Engine.phase
settings.sampling.color = zivid.Settings.Sampling.Color.rgb
settings.region_of_interest.box.enabled = True
settings.region_of_interest.box.point_o = [1000, 1000, 1000]
settings.region_of_interest.box.point_a = [1000, -1000, 1000]
settings.region_of_interest.box.point_b = [-1000, 1000, 1000]
settings.region_of_interest.box.extents = [-1000, 1000]
settings.region_of_interest.depth.enabled = True
settings.region_of_interest.depth.range = [200, 2000]
filters = settings.processing.filters
filters.smoothing.gaussian.enabled = True
filters.smoothing.gaussian.sigma = 1.5
filters.noise.removal.enabled = True
filters.noise.removal.threshold = 7.0
filters.noise.suppression.enabled = True
filters.noise.repair.enabled = True
filters.outlier.removal.enabled = True
filters.outlier.removal.threshold = 5.0
filters.reflection.removal.enabled = True
filters.reflection.removal.mode = zivid.Settings.Processing.Filters.Reflection.Removal.Mode.global_
filters.cluster.removal.enabled = True
filters.cluster.removal.max_neighbor_distance = 10
filters.cluster.removal.min_area = 100
filters.experimental.contrast_distortion.correction.enabled = True
filters.experimental.contrast_distortion.correction.strength = 0.4
filters.experimental.contrast_distortion.removal.enabled = False
filters.experimental.contrast_distortion.removal.threshold = 0.5
filters.hole.repair.enabled = True
filters.hole.repair.hole_size = 0.2
filters.hole.repair.strictness = 1
resampling = settings.processing.resampling
resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2
color = settings.processing.color
color.balance.red = 1.0
color.balance.blue = 1.0
color.balance.green = 1.0
color.gamma = 1.0
settings.processing.color.experimental.mode = zivid.Settings.Processing.Color.Experimental.Mode.automatic
_set_sampling_pixel(settings, camera)
print(settings)
print("Configuring acquisition settings different for all HDR acquisitions")
exposure_values = _get_exposure_values(camera)
for aperture, gain, exposure_time, brightness in exposure_values:
	settings.acquisitions.append(
		zivid.Settings.Acquisition(
			aperture=aperture,
			exposure_time=exposure_time,
			brightness=brightness,
			gain=gain,
		)
	)
```

#### 2D Settings

It is possible to only capture a 2D image. This is faster than a 3D
capture. 2D settings are configured as follows.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_2d.py#L35-L44))

``` sourceCode python
settings_2d = zivid.Settings2D()
settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
settings_2d.acquisitions[0].exposure_time = datetime.timedelta(microseconds=20000)
settings_2d.acquisitions[0].aperture = 9.51
settings_2d.acquisitions[0].brightness = 1.80
settings_2d.acquisitions[0].gain = 2.0
settings_2d.processing.color.balance.red = 1.0
settings_2d.processing.color.balance.green = 1.0
settings_2d.processing.color.balance.blue = 1.0
settings_2d.processing.color.gamma = 1.0
```

### Load

Zivid Studio can store the current settings to .yml files. These can be
read and applied in the API. You may find it easier to modify the
settings in these (human-readable) yaml-files in your preferred editor.
Check out
[Presets](https://support.zivid.com/latest/reference-articles/presets-settings.html)
for recommended .yml files tuned for your application.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr_complete_settings.py#L164-L169))

``` sourceCode python
settings_file = "Settings.yml"
print(f"Loading settings from file: {settings_file}")
settings_from_file = zivid.Settings.load(settings_file)
```

### Save

You can also save settings to .yml file.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr_complete_settings.py#L164-L166))

``` sourceCode python
settings_file = "Settings.yml"
print(f"Saving settings to file: {settings_file}")
settings.save(settings_file)
```

-----

Caution\!:

> Zivid settings files must use .yml file extension ( not .yaml).

## Capture

Now we can capture a 3D image. Whether there is a single acquisition or
multiple acquisitions (HDR) is given by the number of `acquisitions` in
`settings`.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L20))

``` sourceCode python
with camera.capture(settings) as frame:
```

The `zivid.Frame` contains the point cloud and color image (stored on
compute device memory) and the capture and camera information. Load ^^^^

Once saved, the frame can be loaded from a ZDF file.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/file_formats/read_iterate_zdf.py#L14-L16))

``` sourceCode python
data_file = get_sample_data_path() / "Zivid3D.zdf"
print(f"Reading point cloud from file: {data_file}")
frame = zivid.Frame(data_file)
```

Saving to a ZDF file is addressed later in the tutorial.

### Capture 2D

If we only want to capture a 2D image, which is faster than 3D, we can
do so via the 2D API.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_2d.py#L47))

``` sourceCode python
with camera.capture(settings_2d) as frame_2d:
```

## Save

We can now save our results.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L21-L23))

``` sourceCode python
data_file = "Frame.zdf"
frame.save(data_file)
```

-----

Tip:

> You can open and view `Frame.zdf` file in [Zivid
> Studio](https://support.zivid.com/latest//getting-started/studio-guide.html).

### Export

The API detects which format to use. See [Point
Cloud](https://support.zivid.com/latest//reference-articles/point-cloud-structure-and-output-formats.html)
for a list of supported formats. For example, we can export the point
cloud to .ply format.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L25-L27))

``` sourceCode python
data_file_ply = "PointCloud.ply"
frame.save(data_file_ply)
```

### Save 2D

We can get 2D color image from a 3D capture.

No source available for {language\_name}2D captures also produce 2D
color images.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_2d.py#L49))

``` sourceCode python
image = frame_2d.image_rgba()
```

Then, we can save the 2D image.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_2d.py#L57-L59))

``` sourceCode python
image_file = "ImageRGB.png"
print(f"Saving 2D color image (linear RGB color space) to file: {image_file}")
image.save(image_file)
```

## Multithreading

Operations on camera objects are thread-safe, but other operations like
listing cameras and connecting to cameras should be executed in
sequence. Find out more in
[capture\_tutorial](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_tutorial.md).

## Conclusion

This tutorial shows how to use the Zivid SDK to connect to, configure,
capture, and save from the Zivid camera.
