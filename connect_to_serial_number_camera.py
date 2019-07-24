"""
Connect to a specific Zivid camera based on its serial number.
"""

import zivid


def _main():
    app = zivid.Application()

    print("Connecting to the camera")
    serial_number = "12345678"
    camera = app.connect_camera(serial_number)

    print(
        f"Connected to the camera with the following serial number: {camera.serial_number}"
    )


if __name__ == "__main__":
    _main()
