"""
Connect to a Zivid camera.

Without arguments, the sample connects to the first available camera. To connect to a specific camera, provide its
serial number with --serial, its IP address with --ip, or its hostname with --hostname. To connect to all available
cameras, use --all. The sample connects with every method you provide, and fails if any of them fails.

Examples:
    python connect.py --serial 2020C0DE
    python connect.py --ip 172.28.60.5
    python connect.py --hostname zivid-2020C0DE.local
    python connect.py --serial 2020C0DE --ip 172.28.60.5
    python connect.py --all

"""

import argparse

import zivid


def _options() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--serial", type=str, help="Connect to the camera with this serial number")
    parser.add_argument("--ip", type=str, help="Connect to the camera at this IP address")
    parser.add_argument("--hostname", type=str, help="Connect to the camera at this hostname")
    parser.add_argument("--all", action="store_true", help="Connect to all available cameras")

    return parser.parse_args()


def _print_discovered_cameras(app: zivid.Application) -> None:
    print("Discovered cameras:")
    for camera in app.cameras():
        print(
            f"Serial number: {camera.info.serial_number}, "
            f"IP address: {camera.state.network.ipv4.address}, "
            f"hostname: {camera.state.network.hostname}"
        )


def _connect_to_first_available_camera(app: zivid.Application) -> None:
    print("Connecting to the first available camera")
    camera = app.connect_camera()
    camera.disconnect()


def _connect_by_serial_number(app: zivid.Application, serial_number: str) -> None:
    print(f"Connecting to the camera with serial number {serial_number}")
    camera = app.connect_camera(serial_number=serial_number)
    camera.disconnect()


def _connect_by_ip_address(app: zivid.Application, ip_address: str) -> None:
    print(f"Connecting to the camera at IP address {ip_address}")
    camera = app.connect_camera(address=zivid.CameraAddress(ip_address))
    camera.disconnect()


def _connect_by_hostname(app: zivid.Application, hostname: str) -> None:
    print(f"Connecting to the camera at hostname {hostname}")
    # The default hostname format is "zivid-<serial-number>"; connect to it with the ".local" suffix.
    # The hostname is set through the network configuration, see the network_configuration sample.
    camera = app.connect_camera(address=zivid.CameraAddress(hostname))
    camera.disconnect()


def _connect_to_all_available_cameras(app: zivid.Application) -> None:
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


def _main() -> None:
    user_options = _options()

    app = zivid.Application()

    _print_discovered_cameras(app)

    no_method_given = (
        user_options.serial is None
        and user_options.ip is None
        and user_options.hostname is None
        and not user_options.all
    )
    if no_method_given:
        _connect_to_first_available_camera(app)
    if user_options.serial is not None:
        _connect_by_serial_number(app, user_options.serial)
    if user_options.ip is not None:
        _connect_by_ip_address(app, user_options.ip)
    if user_options.hostname is not None:
        _connect_by_hostname(app, user_options.hostname)
    if user_options.all:
        _connect_to_all_available_cameras(app)


if __name__ == "__main__":
    _main()
