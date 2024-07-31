"""
Automatically set the IP addresses of any number of cameras to be in the same subnet as the provided IP address of the network interface.
"""

import argparse
import ipaddress

import zivid


def _options() -> argparse.Namespace:
    """Function to read user arguments.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface-ipv4", required=True, help="IP address of the PC network interface")
    parser.add_argument("--subnet-mask", required=False, default="255.255.255.0", help="Network subnet mask")

    return parser.parse_args()


def _assert_user_input(ip_address: str, subnet_mask: str) -> None:
    """Validates the IP address and the subnet mask.

    Args:
        ip_address: IP address
        subnet_mask: Subnet mask

    """
    zivid.NetworkConfiguration.IPV4(address=ip_address, subnet_mask=subnet_mask)


def _main() -> None:
    try:

        user_input = _options()
        _assert_user_input(user_input.interface_ipv4, user_input.subnet_mask)
        user_ip_address = ipaddress.ip_address(user_input.interface_ipv4)

        # defines the last octet of the ip address of the first Zivid camera. Eg.: x.x.x.2
        next_ip_address_last_octet = 2
        new_ip_address = ipaddress.IPv4Address(user_ip_address.packed[:-1] + bytes([next_ip_address_last_octet]))

        app = zivid.Application()
        cameras = app.cameras()

        if len(cameras) == 0:
            raise RuntimeError("No cameras connected")

        for camera in cameras:

            if new_ip_address == user_ip_address:
                new_ip_address = new_ip_address + 1

            new_config = zivid.NetworkConfiguration(
                ipv4=zivid.NetworkConfiguration.IPV4(
                    mode=zivid.NetworkConfiguration.IPV4.Mode.manual,
                    address=str(new_ip_address),
                    subnet_mask=user_input.subnet_mask,
                )
            )

            new_ip_address = new_ip_address + 1

            print(f"Applying network configuration to camera {camera.info.serial_number}")
            camera.apply_network_configuration(new_config)
            print(f"New {camera.network_configuration}\n")

    except RuntimeError as ex:
        print(ex)


if __name__ == "__main__":
    _main()
