"""
Uses Zivid API to change the IP address of the Zivid camera.
"""

import zivid


def _confirm(message: str) -> bool:
    while True:
        answer = input(f"{message} [Y/n]: ")
        if answer.lower() == "y" or answer.lower() == "yes":
            return True
        if answer.lower() == "n" or answer.lower() == "no":
            return False
        print("Invalid input. Please enter 'Y' or 'n'.")


def _main() -> None:
    app = zivid.Application()
    cameras = app.cameras()

    if len(cameras) == 0:
        raise RuntimeError("Failed to connect to camera. No cameras found.")

    camera = cameras[0]

    original_config = camera.network_configuration

    print(f"Current network configuration of camera {camera.info.serial_number}:")
    print(f"{original_config}\n")

    mode = zivid.NetworkConfiguration.IPV4.Mode.manual
    address = original_config.ipv4.address
    subnet_mask = original_config.ipv4.subnet_mask

    if _confirm("Do you want to use DHCP?"):
        mode = zivid.NetworkConfiguration.IPV4.Mode.dhcp
    else:

        input_address = input(f"Enter IPv4 Address [{original_config.ipv4.address}]: ")
        if input_address:
            address = input_address
        else:
            address = original_config.ipv4.address

        input_subnet_mask = input(f"Enter new Subnet mask [{original_config.ipv4.subnet_mask}]: ")
        if input_subnet_mask:
            subnet_mask = input_subnet_mask
        else:
            subnet_mask = original_config.ipv4.subnet_mask

    new_config = zivid.NetworkConfiguration(
        ipv4=zivid.NetworkConfiguration.IPV4(
            mode=mode,
            address=address,
            subnet_mask=subnet_mask,
        )
    )

    print("\nNew network configuration:")
    print(new_config)
    if not _confirm(f"Do you want to apply the new network configuration to camera {camera.info.serial_number}?"):
        return

    print("Applying network configuration...")
    camera.apply_network_configuration(new_config)

    print(f"Updated network configuration of camera {camera.info.serial_number}:")
    print(f"{camera.network_configuration}\n")

    print(f"Camera status is '{camera.state.status}'")


if __name__ == "__main__":
    _main()
