"""
Store user data on the Zivid camera.
"""

import argparse

import zivid


def _args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", help="Select mode")
    subparsers.add_parser(
        "read",
        help="read",
    )
    subparsers.add_parser(
        "clear",
        help="clear",
    )
    parser_write = subparsers.add_parser(
        "write",
        help="write",
    )
    parser_write.add_argument(
        "user-data",
        type=str,
        help="User data to be stored on the Zivid camera",
    )
    return parser.parse_args()


def _check_user_data_support(camera):
    max_data_size = camera.info.user_data.max_size_bytes
    if max_data_size == 0:
        raise Exception("This camera does not support user data")


def _write(camera: zivid.Camera, string: str):
    camera.write_user_data(str.encode(string))


def _clear(camera: zivid.Camera):
    _write(camera, "")


def _read(camera: zivid.Camera):
    data = camera.user_data
    return data.decode()


def _main():
    try:

        args = _args()
        mode = args.mode

        app = zivid.Application()

        print("Connecting to camera")
        camera = app.connect_camera()
        _check_user_data_support(camera)

        if mode == "read":
            print("Reading user data from camera")
            print(f"Done. User data: '{_read(camera)}'")

        if mode == "write":
            print(f"Writing '{args.user_data}' to the camera")
            _write(camera, args.user_data)
            print("Done. Note! Camera must be rebooted to allow another write operation")

        if mode == "clear":
            print("Clearing user data from camera")
            _clear(camera)
            print("Done. Note! Camera must be rebooted to allow another clear operation")

    except ValueError as ex:
        print(f"Error: {ex}")


if __name__ == "__main__":
    _main()
