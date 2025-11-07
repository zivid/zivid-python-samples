"""
Capture point clouds, with color, from the Zivid camera, with default settings and diagnostics enabled.

Enabling diagnostics allows collecting additional data to be saved in the ZDF file.
Send ZDF files with diagnostics enabled to the Zivid support team to allow more thorough troubleshooting.
Have in mind that enabling diagnostics increases the capture time and the RAM usage.

"""

import zivid


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings")
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    print("Enabling diagnostics")
    settings.diagnostics.enabled = True

    print("Capturing frame")
    frame = camera.capture_2d_3d(settings)
    data_file = "FrameWithDiagnostics.zdf"
    print(f"Saving frame with diagnostic data to file: {data_file}")
    frame.save(data_file)


if __name__ == "__main__":
    _main()
