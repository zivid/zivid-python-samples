"""
Print Python, zivid-python and Zivid SDK versions, then list each connected camera with info and state.

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
        print(camera.info)
        print(camera.state)

    for camera in cameras:
        temperature = camera.state.temperature
        print("Temperatures:")
        print(f"  DMD:     {temperature.dmd} °C")
        print(f"  LED:     {temperature.led} °C")
        print(f"  Lens:    {temperature.lens} °C")
        print(f"  PCB:     {temperature.pcb} °C")
        print(f"  General: {temperature.general} °C")


if __name__ == "__main__":
    _main()
