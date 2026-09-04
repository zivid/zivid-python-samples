"""
Connect to a Zivid camera using the different available methods.

Replace the IP address, serial number and hostname in the code with the ones of your camera,
or provide them with --serial, --ip and --hostname.

"""

import argparse

import zivid


def _options() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--serial", required=False, type=str, default="2020C0DE", help="Serial number of the camera")
    parser.add_argument("--ip", required=False, type=str, default="172.28.60.5", help="IP address of the camera")
    parser.add_argument(
        "--hostname", required=False, type=str, default="zivid-2020C0DE.local", help="Hostname of the camera"
    )

    return parser.parse_args()


def _print_discovered_cameras(app: zivid.Application) -> None:
    print("Discovered cameras:")
    for camera in app.cameras():
        print(f"Serial number: {camera.info.serial_number}, IP address: {camera.state.network.ipv4.address}")


def _main() -> None:
    user_options = _options()

    app = zivid.Application()

    _print_discovered_cameras(app)

    print("Connecting to the first available camera")
    camera = app.connect_camera()
    camera.disconnect()

    print(f"Connecting to the camera with serial number {user_options.serial}")
    camera = app.connect_camera(serial_number=user_options.serial)
    camera.disconnect()

    print(f"Connecting to the camera at IP address {user_options.ip}")
    camera = app.connect_camera(address=zivid.CameraAddress(user_options.ip))
    camera.disconnect()

    print(f"Connecting to the camera at hostname {user_options.hostname}")
    # The default hostname format is "zivid-<serial-number>.local".
    # The hostname cannot be read or set through the SDK.
    camera = app.connect_camera(address=zivid.CameraAddress(user_options.hostname))
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
