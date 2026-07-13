"""
Automatically configure the IP addresses of connected cameras to match the network of the user's PC.

Usage:
- By default, the program applies the new configuration directly to the cameras.
- Use the [--display-only] argument to simulate the configuration and display the
  proposed IP addresses without making actual changes. Note: camera-side Ethernet
  link speed will also be skipped, as it requires connecting to the camera.

For more information on network configuration, check out this tutorial:
https://support.zivid.com/en/latest/camera/getting-started/software-installation/zivid-two-network-configuration.html

"""

import argparse
import ipaddress
from typing import Dict, List, Tuple

import zivid


def get_users_local_interface(camera: zivid.Camera) -> zivid.CameraState.Network.LocalInterface:
    local_interfaces = camera.state.network.local_interfaces

    if len(local_interfaces) == 0:
        raise RuntimeError(f"No user local interface detected from the camera {camera.info.serial_number}")

    if len(local_interfaces) > 1:
        raise RuntimeError(
            f"More than one local interface detected from the camera {camera.info.serial_number}. "
            "Please, reorganize your network."
        )

    return local_interfaces[0]


def print_host_side_ethernet_link_speed(camera: zivid.Camera) -> None:
    # Reading the host-side (local interface) Ethernet link speed does not require a connection to the camera.
    local_interface_link_speed = get_users_local_interface(camera).ethernet.link_speed

    print(f"Camera {camera.info.serial_number}: local interface Ethernet link speed={local_interface_link_speed}")


def print_camera_side_ethernet_link_speed(camera: zivid.Camera) -> None:
    # Reading the camera-side Ethernet link speed requires being connected to the camera.
    camera.connect()
    try:
        camera_link_speed = camera.state.network.ethernet.link_speed
    finally:
        camera.disconnect()

    print(f"Camera {camera.info.serial_number}: camera Ethernet link speed={camera_link_speed}")


def get_users_local_interface_network_configuration(camera: zivid.Camera) -> Tuple[str, str]:
    """Get the IP address and subnet mask of the user's local network interface connected to the specified camera.

    Args:
        camera: A Zivid camera

    Raises:
        RuntimeError: If no local interface is detected for the camera.
        RuntimeError: If multiple local interfaces are detected for the camera.
        RuntimeError: If no subnet is detected for the local interface detected.
        RuntimeError: If multiple subnets are found for a single interface detected for the camera.

    Returns:
        A tuple containing the IP address and subnet mask.

    """
    local_interface = get_users_local_interface(camera)

    if len(local_interface.ipv4.subnets) == 0:
        raise RuntimeError(f"No valid subnets found for camera {camera.info.serial_number}")

    if len(local_interface.ipv4.subnets) > 1:
        raise RuntimeError(
            f"More than one ip address found for the local interface from the camera {camera.info.serial_number}"
        )

    subnet = local_interface.ipv4.subnets[0]
    return subnet.address, subnet.mask


def _main() -> None:
    try:
        parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
        parser.add_argument(
            "--display-only",
            action="store_true",
            help="Only display the new network configurations of the camera(s) without applying changes",
        )

        args = parser.parse_args()

        app = zivid.Application()
        cameras = app.cameras()

        if len(cameras) == 0:
            raise RuntimeError("No cameras connected")

        local_interface_ip_to_cameras: Dict[str, List[zivid.Camera]] = {}

        for camera in cameras:

            try:

                local_interface_ip_address, local_interface_subnet_mask = (
                    get_users_local_interface_network_configuration(camera)
                )
                local_interface_ip_object = ipaddress.ip_address(local_interface_ip_address)

                next_ip_address_last_octet = local_interface_ip_object.packed[-1]

                # Identifying the last octet of the new ip address for the current camera
                if local_interface_ip_address not in local_interface_ip_to_cameras:
                    local_interface_ip_to_cameras[local_interface_ip_address] = []
                    next_ip_address_last_octet += 1
                else:
                    next_ip_address_last_octet += len(local_interface_ip_to_cameras[local_interface_ip_address]) + 1

                local_interface_ip_to_cameras[local_interface_ip_address].append(camera)

                new_camera_ip_address = ipaddress.IPv4Address(
                    local_interface_ip_object.packed[:-1] + bytes([next_ip_address_last_octet])
                )

                new_config = zivid.NetworkConfiguration(
                    ipv4=zivid.NetworkConfiguration.IPV4(
                        mode=zivid.NetworkConfiguration.IPV4.Mode.manual,
                        address=str(new_camera_ip_address),
                        subnet_mask=local_interface_subnet_mask,
                    )
                )

                if args.display_only:
                    print(
                        f"Current camera serial number: {camera.info.serial_number}\n"
                        f"Current camera {camera.network_configuration}"
                        f"Current local interface detected: {local_interface_ip_address}\n"
                        f"Simulated new camera address ip: {new_camera_ip_address}\n\n"
                    )
                else:
                    print(
                        f"Applying new network configuration to camera with serial number: {camera.info.serial_number}\n"
                        f"Current local interface detected: {local_interface_ip_address}"
                    )
                    camera.apply_network_configuration(new_config)
                    print(f"New {camera.network_configuration}\n")

            except RuntimeError as ex:
                print(f"Error when configuring camera: {camera.info.serial_number}. Exception: {ex}")

        for camera in cameras:

            try:
                print_host_side_ethernet_link_speed(camera)
                if not args.display_only:
                    print_camera_side_ethernet_link_speed(camera)

            except RuntimeError as ex:
                print(
                    f"Error when reading Ethernet link speed for camera: {camera.info.serial_number}. Exception: {ex}"
                )

    except RuntimeError as ex:
        print(ex)


if __name__ == "__main__":
    _main()
