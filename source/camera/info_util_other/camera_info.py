"""
Print version information for Python, zivid-python and Zivid SDK, then list cameras and print camera info and state for each connected camera.

"""

import platform

import zivid


def _main() -> None:
    app = zivid.Application()
    print(f"Python:       {platform.python_version()}")
    print(f"zivid-python: {zivid.__version__}")
    print(f"Zivid SDK:    {zivid.SDKVersion.full}")
    cameras = app.cameras()
    for camera in cameras:
        print(f"Camera Info:  {camera.info}")
        print(f"Camera State: {camera.state}")


if __name__ == "__main__":
    _main()
