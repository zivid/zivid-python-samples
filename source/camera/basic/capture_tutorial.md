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
[**Capture**](#Capture-2D3D) |
[**Save**](#Save) |
[**Multithreading**](#Multithreading) |
[**Conclusion**](#Conclusion)

---



## Introduction

This tutorial describes how to use the Zivid SDK to capture point clouds
and 2D images.

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
default=get_sample_data_path() / "FileCameraZivid2PlusMR60.zfc",
```

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_from_file_camera.py#L48))

``` sourceCode python
camera = app.create_file_camera(file_camera)
```

The acquisition settings should be initialized like shown below, but you
are free to alter the processing settings.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_from_file_camera.py#L51-L64))

``` sourceCode python
settings = zivid.Settings()
settings.acquisitions.append(zivid.Settings.Acquisition())
settings.processing.filters.smoothing.gaussian.enabled = True
settings.processing.filters.smoothing.gaussian.sigma = 1
settings.processing.filters.reflection.removal.enabled = True
settings.processing.filters.reflection.removal.mode = "global"
settings_2d = zivid.Settings2D()
settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
settings_2d.processing.color.balance.blue = 1.0
settings_2d.processing.color.balance.green = 1.0
settings_2d.processing.color.balance.red = 1.0

settings.color = settings_2d
```

You can read more about the file camera option in [File
Camera](https://support.zivid.com/latest/academy/camera/file-camera.html).

## Configure

As with all cameras there are settings that can be configured.

### Presets

The recommendation is to use
[Presets](https://support.zivid.com/latest/reference-articles/presets-settings.html)
available in Zivid Studio and as .yml files (see below). Presets are
designed to work well for most cases right away, making them a great
starting point. If needed, you can easily fine-tune the settings for
better results. You can edit the YAML files in any text editor or code
the settings manually.

### Load

You can export camera settings to .yml files from Zivid Studio. These
can be loaded and applied in the API.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr_complete_settings.py#L195-L200))

``` sourceCode python
settings_file = "Settings.yml"
print(f"Loading settings from file: {settings_file}")
settings_from_file = zivid.Settings.load(settings_file)
```

### Save

You can also save settings to .yml file.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr_complete_settings.py#L195-L197))

``` sourceCode python
settings_file = "Settings.yml"
print(f"Saving settings to file: {settings_file}")
settings.save(settings_file)
```

### Manual configuration

Another option is to configure settings manually. For more information
about what each settings does, please see [Camera
Settings](https://support.zivid.com/latest/reference-articles/camera-settings.html).
Then, the next step it's [Capturing High Quality Point
Clouds](https://support.zivid.com/latest/academy/camera/capturing-high-quality-point-clouds.html)

#### Single 2D and 3D Acquisition - Default settings

We can create settings for a single acquisition capture.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L16-L19))

``` sourceCode python
settings = zivid.Settings(
	acquisitions=[zivid.Settings.Acquisition()],
	color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
)
```

#### Multi Acquisition HDR

We may also create settings to be used in a multi-acquisition HDR
capture.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/advanced/capture_hdr_print_normals.py#L42))

``` sourceCode python
settings = zivid.Settings(acquisitions=[zivid.Settings.Acquisition(aperture=fnum) for fnum in (5.66, 4.00, 2.83)])
```

Fully configured settings are demonstrated below.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_hdr_complete_settings.py#L99-L183))

``` sourceCode python
print("Configuring settings for capture:")
settings_2d = zivid.Settings2D()
settings_2d.sampling.color = zivid.Settings2D.Sampling.Color.rgb
settings_2d.sampling.pixel = zivid.Settings2D.Sampling.Pixel.all

settings_2d.processing.color.balance.red = 1.0
settings_2d.processing.color.balance.blue = 1.0
settings_2d.processing.color.balance.green = 1.0
settings_2d.processing.color.gamma = 1.0

settings_2d.processing.color.experimental.mode = zivid.Settings2D.Processing.Color.Experimental.Mode.automatic

settings = zivid.Settings()
settings.engine = zivid.Settings.Engine.phase

settings.region_of_interest.box.enabled = True
settings.region_of_interest.box.point_o = [1000, 1000, 1000]
settings.region_of_interest.box.point_a = [1000, -1000, 1000]
settings.region_of_interest.box.point_b = [-1000, 1000, 1000]
settings.region_of_interest.box.extents = [-1000, 1000]

settings.region_of_interest.depth.enabled = True
settings.region_of_interest.depth.range = [200, 2000]

settings.processing.filters.cluster.removal.enabled = True
settings.processing.filters.cluster.removal.max_neighbor_distance = 10
settings.processing.filters.cluster.removal.min_area = 100

settings.processing.filters.hole.repair.enabled = True
settings.processing.filters.hole.repair.hole_size = 0.2
settings.processing.filters.hole.repair.strictness = 1

settings.processing.filters.noise.removal.enabled = True
settings.processing.filters.noise.removal.threshold = 7.0

settings.processing.filters.noise.suppression.enabled = True
settings.processing.filters.noise.repair.enabled = True

settings.processing.filters.outlier.removal.enabled = True
settings.processing.filters.outlier.removal.threshold = 5.0

settings.processing.filters.reflection.removal.enabled = True
settings.processing.filters.reflection.removal.mode = (
	zivid.Settings.Processing.Filters.Reflection.Removal.Mode.global_
)

settings.processing.filters.smoothing.gaussian.enabled = True
settings.processing.filters.smoothing.gaussian.sigma = 1.5

settings.processing.filters.experimental.contrast_distortion.correction.enabled = True
settings.processing.filters.experimental.contrast_distortion.correction.strength = 0.4

settings.processing.filters.experimental.contrast_distortion.removal.enabled = False
settings.processing.filters.experimental.contrast_distortion.removal.threshold = 0.5

settings.processing.resampling.mode = zivid.Settings.Processing.Resampling.Mode.upsample2x2

settings.diagnostics.enabled = False

settings.color = settings_2d

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

settings_2d.acquisitions.append(
	zivid.Settings2D.Acquisition(
		aperture=2.83,
		exposure_time=timedelta(microseconds=10000),
		brightness=1.8,
		gain=1.0,
	)
)
```

## Capture 2D3D

Now we can capture a 2D and 3D image (point cloud with color). Whether
there is a single acquisition or multiple acquisitions (HDR) is given by
the number of `acquisitions` in `settings`.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L22-L23))

``` sourceCode python
frame = camera.capture_2d_3d(settings)
```

The `zivid.Frame` contains the point cloud, the color image, the
capture, and the camera information (all of which are stored on the
compute device memory). Capture 3D ^^^^^^^^^^

If we only want to capture 3D, the points cloud without color, we can do
so via the `capture3D` API.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_with_settings_from_yml.py#L122))

``` sourceCode python
frame_3d = camera.capture_3d(settings)
```

### Capture 2D

If we only want to capture a 2D image, which is faster than 3D, we can
do so via the `capture2D` API.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_with_settings_from_yml.py#L91))

``` sourceCode python
frame_2d = camera.capture_2d(settings)
```

## Save

We can now save our results.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L29-L31))

``` sourceCode python
data_file = "Frame.zdf"
frame.save(data_file)
```

-----

Tip:

> You can open and view `Frame.zdf` file in [Zivid
> Studio](https://support.zivid.com/latest//getting-started/studio-guide.html).

### Export

In the next code example, the point cloud is exported to the .ply
format. For other exporting options, see [Point
Cloud](https://support.zivid.com/latest//reference-articles/point-cloud-structure-and-output-formats.html)
for a list of supported formats.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L33-L35))

``` sourceCode python
data_file_ply = "PointCloud.ply"
frame.save(data_file_ply)
```

### Load

Once saved, the frame can be loaded from a ZDF file.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/file_formats/read_iterate_zdf.py#L14-L17))

``` sourceCode python
data_file = get_sample_data_path() / "Zivid3D.zdf"
print(f"Reading point cloud from file: {data_file}")
frame = zivid.Frame(data_file)
```

### Save 2D

From a `capture2D()` you get a `Frame2D`. There are two color spaces
available for 2D images: linear RGB and sRGB. The `imageRGBA()` will
return an image in the linear RGB color space. If you append `_SRGB` to
the function name then the returned image will be in the sRGB color
space

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_with_settings_from_yml.py#L96))

``` sourceCode python
image_rgba = frame_2d.image_rgba()
.. tab-item:: sRGB
```

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_with_settings_from_yml.py#L107))

``` sourceCode python
image_srgb = frame_2d.image_rgba_srgb()
```

Then, we can save the 2D image in linear RGB or sRGB color space.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_with_settings_from_yml.py#L97-L99))

``` sourceCode python
image_file = "ImageRGBA_linear.png"
print(f"Saving 2D color image (sRGB color space) to file: {image_file}")
image_rgba.save(image_file)
.. tab-item:: sRGB
```

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_with_settings_from_yml.py#L108-L110))

``` sourceCode python
image_file = "ImageRGBA_sRGB.png"
print(f"Saving 2D color image (sRGB color space) to file: {image_file}")
image_srgb.save(image_file)
```

We can get 2D color image directly from the point cloud. This image will
have the same resolution as the point cloud and it will be in the sRGB
color space.

([go to source]())

``` sourceCode python
point_cloud = frame.point_cloud()
image_2d_in_point_cloud_resolution = point_cloud.copy_image("bgra_srgb")
```

We can get the 2D color image from `Frame2D`, which is part of the
`Frame` object, obtained from `capture2D3D()`. This image will have the
resolution given by the 2D settings inside the 2D3D settings.

([go to source]())

``` sourceCode python
image_2d = frame.frame_2d().image_bgra_srgb()
```

## Multithreading

Operations on camera objects are thread-safe, but other operations like
listing cameras and connecting to cameras should be executed in
sequence. Find out more in
[capture\_tutorial](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_tutorial.md).

## Conclusion

This tutorial shows how to use the Zivid SDK to connect to, configure,
capture, and save from the Zivid camera.
