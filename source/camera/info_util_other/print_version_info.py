"""
This example shows how to print version information for Python, zivid-python and Zivid SDK.
"""

import platform
import zivid


def _main():
    app = zivid.Application()
    print(f"Python:       {platform.python_version()}")
    print(f"zivid-python: {zivid.__version__}")
    print(f"Zivid SDK:    {zivid.SDKVersion.full}")
    cameras = app.cameras()
    for camera in cameras:
        print(f"Camera Info:  {camera}")


if __name__ == "__main__":
    _main()
