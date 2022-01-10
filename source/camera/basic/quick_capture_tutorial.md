# Quick Capture Tutorial



---

*Contents:*
1. [Introduction](#Introduction)
2. [Initialize](#Initialize)
3. [Connect](#Connect)
4. [Configure](#Configure)
5. [Capture](#Capture)
6. [Save](#Save)

---

## Introduction

This tutorial describes the most basic way to use the Zivid SDK to
capture point clouds.

For MATLAB see [Zivid Quick Capture Tutorial for
MATLAB](https://github.com/zivid/zivid-matlab-samples/blob/master/source/Camera/Basic/QuickCaptureTutorial.md)

**Prerequisites**

  - Install [Zivid
    Software](https://support.zivid.com/latest//getting-started/software-installation.html).
  - For Python: install
    [zivid-python](https://github.com/zivid/zivid-python#installation)

## Initialize

Calling any of the APIs in the Zivid SDK requires initializing the Zivid
application and keeping it alive while the program runs.

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L11))

``` sourceCode python
app = zivid.Application()
```

## Connect

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L15))

``` sourceCode python
camera = app.connect_camera()
```

## Configure

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

## Capture

([go to
source](https://github.com/zivid/zivid-python-samples/tree/master//source/camera/basic/capture.py#L29))

``` sourceCode python
with camera.capture(settings) as frame:
```

## Save

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

**Conclusion**

This tutorial shows the most basic way to use the Zivid SDK to connect
to, capture, and save from the Zivid camera.

For a more in-depth tutorial check out the complete
[capture\_tutorial](https://github.com/zivid/zivid-python-samples/tree/master/Camera/Basic/capture_tutorial).
