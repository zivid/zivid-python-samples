"""
Capture a frame with diagnostics enabled and create a file camera from it.

A file camera is a virtual camera that replays captures offline using the raw sensor data
stored in the original frame. This allows you to develop and test without a physical camera.

The workflow:
1. Capture a frame with diagnostics enabled
2. Save the diagnostics frame as a .zdf file
3. Disconnect from the camera (no longer needed)
4. Load the .zdf frame and create a file camera from it
5. Adjust processing settings and capture from the file camera
6. Save the resulting frame

For more information about file cameras, check out this tutorial:
https://support.zivid.com/en/latest/camera/academy/camera/file-camera.html

"""

import zivid


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Creating default settings")
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )
    print("Enabling diagnostics")
    settings.diagnostics.enabled = True

    print("Capturing frame with diagnostics")
    frame_with_diagnostics = camera.capture_2d_3d(settings)

    frame_with_diagnostics_file = "FrameWithDiagnostics.zdf"
    print(f"Saving diagnostics frame to: {frame_with_diagnostics_file}")
    frame_with_diagnostics.save(frame_with_diagnostics_file)

    print("Disconnecting from camera")
    camera.disconnect()

    print(f"Loading ZDF with diagnostics enabled from: {frame_with_diagnostics_file}")
    loaded_frame_with_diagnostics = zivid.Frame(frame_with_diagnostics_file)

    print("Creating file camera from frame")
    file_camera = app.create_file_camera(loaded_frame_with_diagnostics)

    print(f"File camera info: {file_camera.info}")

    print("Configuring settings")
    settings_from_frame = loaded_frame_with_diagnostics.settings
    settings_from_frame.diagnostics.enabled = False
    settings_from_frame.processing.filters.smoothing.gaussian.enabled = True
    settings_from_frame.processing.filters.smoothing.gaussian.sigma = 1.5
    settings_from_frame.processing.filters.reflection.removal.enabled = True
    settings_from_frame.processing.filters.reflection.removal.mode = (
        zivid.Settings.Processing.Filters.Reflection.Removal.Mode.global_
    )

    print("Capturing from file camera")
    file_camera_frame = file_camera.capture_2d_3d(settings_from_frame)

    file_camera_frame_file = "FrameFromFileCameraWithNoDiagnostics.zdf"
    print(f"Saving file camera frame to: {file_camera_frame_file}")
    file_camera_frame.save(file_camera_frame_file)


if __name__ == "__main__":
    _main()
