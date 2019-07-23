"""
Connect to a specific Zivid camera based on its serial number.
"""

import zivid


def _main():
    app = zivid.Application()

    print("Connecting to the camera")
    camera = app.connect_camera("122026014961")

    print(
        "Connected to the camera with the following serial number: ",
        camera.serial_number,
    )


if __name__ == "__main__":
    _main()
