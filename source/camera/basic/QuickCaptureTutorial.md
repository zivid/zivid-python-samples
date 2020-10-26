## Introduction

This tutorial shows how few API calls are required to capture a point cloud with Zivid SDK.

1. [Connect](#connect)
2. [Capture](#capture)
3. [Save](#save)

### Prerequisites

You should have installed Zivid SDK and Python samples. For more details see [Instructions][installation-instructions-url].

Before calling any of the APIs in the Zivid SDK, we have to start up the Zivid Application. This is done through a simple instantiation of the application ([go to source][start_app-url]).
```python
app = zivid.Application()
```

## Connect

First we have to connect to the camera ([go to source][connect-url]).
```python
camera = app.connect_camera()
```

## Configure

Then we have to create settings ([go to source][settings-url]).
```python
settings = zivid.Settings()
settings.acquisitions.append(zivid.Settings.Acquisition())
```

## Capture

Now we can capture a frame. The default capture is a single 3D point cloud ([go to source][capture-url]).
```python
frame = camera.capture(settings)
```

## Save

We can now save our results. By default the 3D point cloud is saved in Zivid format `.zdf` ([go to source][save-url]).
```python
frame.save("Frame.zdf")
```

## Conclusion

This tutorial showed how few API calls are required to capture a point cloud with Zivid SDK.

### Recommended further reading

[The complete Capture Tutorial](CaptureTutorial.md)

[installation-instructions-url]: ../../../README.md#instructions
[start_app-url]: capture.py#L10
[connect-url]: capture.py#L13
[settings-url]: capture.py#L16-L17
[capture-url]: capture.py#L24
[save-url]: capture.py#L27
