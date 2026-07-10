"""
Capture a 2D+3D frame and a 2D frame from the Zivid camera with diagnostics enabled.

Enabling diagnostics allows collecting additional data to be saved in the ZDF file.
Send ZDF files with diagnostics enabled to the Zivid support team to allow more thorough troubleshooting.
The 2D frame ZDF (Frame2DWithDiagnostics.zdf) must be loaded using the Frame2D API.
Have in mind that enabling diagnostics increases the capture time and the RAM usage.

For more information on diagnostics, check out this article:
https://support.zivid.com/en/latest/reference-articles/settings/diagnostics.html

"""

import zivid


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings for 2D+3D capture")
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    print("Enabling diagnostics")
    settings.diagnostics.enabled = True

    print("Capturing 2D+3D frame")
    frame = camera.capture_2d_3d(settings)
    data_file = "FrameWithDiagnostics.zdf"
    print(f"Saving frame with diagnostic data to file: {data_file}")
    frame.save(data_file)

    print("Configuring settings for 2D capture")
    settings_2d = zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()])

    print("Enabling 2D diagnostics")
    settings_2d.diagnostics.enabled = True

    print("Capturing 2D frame")
    frame_2d = camera.capture_2d(settings_2d)
    data_file_2d = "Frame2DWithDiagnostics.zdf"
    print(f"Saving 2D frame with diagnostic data to file: {data_file_2d}")
    frame_2d.save(data_file_2d)


if __name__ == "__main__":
    _main()
