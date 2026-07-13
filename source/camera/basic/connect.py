"""
Connect to a Zivid camera using the different available methods.

Replace the IP address and serial number in the code with the ones of your camera.

"""

import zivid


def _print_discovered_cameras(app: zivid.Application) -> None:
    print("Discovered cameras:")
    for camera in app.cameras():
        print(f"Serial number: {camera.info.serial_number}, IP address: {camera.state.network.ipv4.address}")


def _main() -> None:
    app = zivid.Application()

    _print_discovered_cameras(app)

    print(
        "The serial number, IP address and hostname below are placeholders. Replace them with the ones of your camera."
    )

    print("Connecting to the first available camera")
    camera = app.connect_camera()
    camera.disconnect()

    print("Connecting to the camera with a specific serial number")
    camera = app.connect_camera(serial_number="2020C0DE")
    camera.disconnect()

    print("Connecting to the camera at a specific IP address")
    camera = app.connect_camera(address=zivid.CameraAddress("172.28.60.5"))
    camera.disconnect()

    print("Connecting to the camera at a specific hostname")
    # The default hostname format is "zivid-<serial-number>.local".
    # The hostname cannot be read or set through the SDK.
    camera = app.connect_camera(address=zivid.CameraAddress("zivid-2020C0DE.local"))
    camera.disconnect()

    print("Connecting to all available cameras")
    connected_cameras = []
    for camera in app.cameras():
        if camera.state.status == zivid.CameraState.Status.available:
            print(f"Connecting to camera: {camera.info.serial_number}")
            camera.connect()
            connected_cameras.append(camera)
        else:
            print(f"Camera {camera.info.serial_number} is not available. Camera status: {camera.state.status}")
    for camera in connected_cameras:
        camera.disconnect()


if __name__ == "__main__":
    _main()
