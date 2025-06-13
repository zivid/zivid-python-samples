# Quick Capture Tutorial

Note\! This tutorial has been generated for use on Github. For original
tutorial see:
[quick\_capture\_tutorial](https://support.zivid.com/latest/getting-started/quick-capture-tutorial.html)



---

*Contents:*
[**Introduction**](#Introduction) |
[**Initialize**](#Initialize) |
[**Connect**](#Connect) |
[**Configure**](#Configure) |
[**Capture**](#Capture) |
[**Save**](#Save) |
[**Utilize**](#Utilize)

---



## Introduction

This tutorial describes the most basic way to use the Zivid SDK to
capture point clouds.

**Prerequisites**

  - Install [Zivid
    Software](https://support.zivid.com/latest//getting-started/software-installation.html).
  - For Python: install
    [zivid-python](https://github.com/zivid/zivid-python#installation)

## Initialize

Calling any of the APIs in the Zivid SDK requires initializing the Zivid
application and keeping it alive while the program runs.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L10))

``` sourceCode python
app = zivid.Application()
```

## Connect

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L13))

``` sourceCode python
camera = app.connect_camera()
```

## Configure

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture_with_settings_from_yml.py#L88))

``` sourceCode python
settings = zivid.Settings.load(settings_file)
```

## Capture

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L22-L23))

``` sourceCode python
frame = camera.capture_2d_3d(settings)
```

## Save

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L29-L31))

``` sourceCode python
data_file = "Frame.zdf"
frame.save(data_file)
.. tab-item:: Export
```

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L33-L35))

``` sourceCode python
data_file_ply = "PointCloud.ply"
frame.save(data_file_ply)
```

For other exporting options, see [Point
Cloud](https://support.zivid.com/latest//reference-articles/point-cloud-structure-and-output-formats.html)
for a list of supported formats

## Utilize

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/applications/basic/file_formats/read_iterate_zdf.py#L20-L22))

``` sourceCode python
point_cloud = frame.point_cloud()
xyz = point_cloud.copy_data("xyz")
rgba = point_cloud.copy_data("rgba_srgb")
```

-----

Tip:

1.  You can export Preset settings to YML from [Zivid
    Studio](https://support.zivid.com/latest//getting-started/studio-guide.html)

\#. You can open and view `Frame.zdf` file in [Zivid
Studio](https://support.zivid.com/latest//getting-started/studio-guide.html).
.. rubric:: Conclusion

This tutorial shows the most basic way to use the Zivid SDK to connect
to, capture, and save from the Zivid camera.

For a more in-depth tutorial check out the complete
[capture\_tutorial](https://github.com/zivid/zivid-python-samples/tree/master/source/camera/basic/capture_tutorial.md).
