"""
Read frame info from the Zivid camera.

The frame info consists of the version information for installed software at the time of capture,
information about the system that captured the frame, and the time stamp of the capture.

"""

import zivid


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    frame = camera.capture_2d_3d(settings)

    frame_info = frame.info

    print("The version information for installed software at the time of image capture:")
    print(frame_info.software_version)

    print("Information about the system that captured this frame:")
    print(frame_info.system_info)

    print("The time of frame capture:")
    print(frame_info.time_stamp)

    print("Acquisition time:")
    print(f"{frame_info.metrics.acquisition_time.total_seconds() * 1000:.0f} ms")

    print("Capture time:")
    print(f"{frame_info.metrics.capture_time.total_seconds() * 1000:.0f} ms")


if __name__ == "__main__":
    _main()
