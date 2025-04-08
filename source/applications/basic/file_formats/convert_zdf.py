"""
Convert point cloud data from a ZDF file to your preferred format
(PLY, PCD, XYZ, CSV, TXT, PNG, JPG, BMP).

Example: $ python convert_zdf.py --3d ply xyz csv --2d jpg png Zivid3D.zdf

Available formats:
    PLY, PCD, XYZ, CSV, TXT - 3D point cloud
    PNG, JPG, BMP - 2D RGB image

"""

import argparse
from pathlib import Path

import numpy as np
import zivid
from zivid.experimental.point_cloud_export import export_frame
from zivid.experimental.point_cloud_export.file_format import PCD, PLY, XYZ, ColorSpace

FORMATS_3D = ["ply", "pcd", "xyz", "csv", "txt"]
FORMATS_2D = ["jpg", "png", "bmp"]


def _options() -> argparse.Namespace:
    """Function for taking in arguments from user.

    Returns:
        Arguments from user

    """
    parser = argparse.ArgumentParser(
        description="Convert from a ZDF to your preferred format\
            \nExample:\n\t $ python convert_zdf.py --3d ply --linearRGB Zivid3D.zdf",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
    )

    parser.usage = "%(prog)s [path] [file formats] [sub-arguments]"

    # Add argument groups
    main_group = parser.add_argument_group("Main arguments")
    formats_group = parser.add_argument_group("Optional format options")
    sub_arg_group = parser.add_argument_group("Optional sub-arguments")

    # Main arguments
    main_group.add_argument("path", help="File/directory holding ZDF file(s)")
    main_group.add_argument(
        "-a", "--all", action="store_true", help="Convert to all formats (default if no formats are specified)"
    )
    main_group.add_argument("-h", "--help", action="help", help="Shows this help message")

    # Formats
    formats_group.add_argument(
        "--3d",
        dest="formats_3d",
        nargs="+",
        choices=FORMATS_3D,
        help="3D format(s) to convert to",
    )
    formats_group.add_argument(
        "--2d",
        dest="formats_2d",
        nargs="+",
        choices=FORMATS_2D,
        help="2D format(s) to convert to",
    )

    # Sub-arguments
    sub_arg_group.add_argument(
        "--linearRGB",
        dest="linear_rgb",
        action="store_true",
        help="To have colour space be Linear RGB instead of sRGB for selected format(s)",
    )
    sub_arg_group.add_argument(
        "--unordered",
        action="store_true",
        help="To have point clouds be unordered instead of ordered (PLY, PCD)",
    )

    return parser.parse_args()


def _flatten_point_cloud(point_cloud: zivid.PointCloud, linear_rgb: bool) -> np.ndarray:
    """Convert from point cloud to flattened point cloud (with numpy).

    Args:
        point_cloud: A handle to point cloud in the GPU memory
        linear_rgb: whether to save as linear RGB or sRGB for selected format(s) (default: False[sRGB])

    Returns:
        A 2D numpy array, with 8 columns and npixels rows

    """
    # Convert to numpy 3D array
    color_space = "rgba" if linear_rgb else "rgba_srgb"
    point_cloud = np.dstack(
        [point_cloud.copy_data("xyz"), point_cloud.copy_data(color_space), point_cloud.copy_data("snr")]
    )
    # Flattening the point cloud
    flattened_point_cloud = point_cloud.reshape(-1, 8)

    # Removing nans
    return flattened_point_cloud[~np.isnan(flattened_point_cloud[:, 0]), :]


def _convert_to_3d(frame: zivid.Frame, file_path: Path, file_formats: list, linear_rgb: bool, unordered: bool) -> None:
    """Convert from frame to different 3D formats.

    Args:
        frame: A frame captured by a Zivid camera
        file_path: Full path of the file(s) to be converted
        file_formats: List of formats to convert to [PLY, PCD, XYZ, CSV, TXT]
        linear_rgb: whether to save as linear RGB or sRGB for selected format(s) (default: False[sRGB])
        unordered: whether to save as unordered or ordered point cloud for PLY format (default: ordered)

    """
    for file_format in file_formats:
        file_name_w_extension = f"{file_path.parent / file_path.stem}.{file_format}"
        _3d_object = None
        if file_format == "ply":
            if not linear_rgb and not unordered:
                _3d_object = PLY(file_name_w_extension, layout=PLY.Layout.ordered, color_space=ColorSpace.srgb)
            elif linear_rgb and not unordered:
                _3d_object = PLY(file_name_w_extension, layout=PLY.Layout.ordered, color_space=ColorSpace.linear_rgb)
            elif linear_rgb and unordered:
                _3d_object = PLY(file_name_w_extension, layout=PLY.Layout.unordered, color_space=ColorSpace.linear_rgb)
            elif not linear_rgb and unordered:
                _3d_object = PLY(file_name_w_extension, layout=PLY.Layout.unordered, color_space=ColorSpace.srgb)

        elif file_format == "pcd":
            if not unordered:
                print(
                    "NOTE: If you have configured the config file for PCD, points will be ordered. \
If not they will be unordered. See https://support.zivid.com/en/latest/reference-articles/point-cloud-structure-and-output-formats.html#organized-pcd-format for more information."
                )
            if linear_rgb:
                _3d_object = PCD(file_name_w_extension, color_space=ColorSpace.linear_rgb)
            else:
                _3d_object = PCD(file_name_w_extension, color_space=ColorSpace.srgb)

        elif file_format == "xyz":
            if linear_rgb:
                _3d_object = XYZ(file_name_w_extension, color_space=ColorSpace.linear_rgb)
            else:
                _3d_object = XYZ(file_name_w_extension, color_space=ColorSpace.srgb)

        elif file_format in ("csv", "txt"):
            np.savetxt(
                file_name_w_extension, _flatten_point_cloud(frame.point_cloud(), linear_rgb), delimiter=",", fmt="%.3f"
            )

        print(f"Saving the frame to {file_name_w_extension}")
        if _3d_object:
            export_frame(frame, _3d_object)


def _convert_to_2d(frame: zivid.Frame, file_path: Path, file_formats: list, linear_rgb: bool) -> None:
    """Convert from point cloud to 2D images.

    Args:
        frame: A frame captured by a Zivid camera
        file_path: Full path of the file(s) to be converted
        file_formats: List of formats to convert to [JPG, PNG, BMP]
        linear_rgb: whether to save as linear RGB or sRGB for selected format(s) (default: False[sRGB])

    """
    for file_format in file_formats:
        file_names = [
            f"{file_path.parent / file_path.stem}.{file_format}",
            f"{file_path.parent / file_path.stem}_point_cloud_resolution.{file_format}",
        ]
        if linear_rgb:
            image_2d = frame.frame_2d().image_rgba()
            image_2d_in_point_cloud_resolution = frame.point_cloud().copy_image("rgba")
        else:
            image_2d = frame.frame_2d().image_rgba_srgb()
            image_2d_in_point_cloud_resolution = frame.point_cloud().copy_image("rgba_srgb")

        print(f"Saving the frame to {file_names[0]} and {file_names[1]}")
        image_2d.save(file_names[0])
        image_2d_in_point_cloud_resolution.save(file_names[1])


def _main() -> None:
    user_options = _options()

    path = Path(user_options.path)
    if not path.exists():
        raise ValueError(f"{user_options.path} does not exist")

    with zivid.Application():
        print(f"Reading point cloud(s) from: {user_options.path}")

        frames = []
        if path.is_dir():
            for file_path in path.glob("*.zdf"):
                frame = zivid.Frame(file_path)
                frames.append((frame, file_path))
        else:
            frame = zivid.Frame(user_options.path)
            frames.append((frame, path))

        if len(frames) == 0:
            raise ValueError(f"{user_options.path} does not contain any ZDF files")

        if user_options.all or (not user_options.formats_3d and not user_options.formats_2d):
            for frame, file_name in frames:
                user_options.formats_3d = FORMATS_3D
                user_options.formats_2d = FORMATS_2D
                _convert_to_3d(
                    frame,
                    file_name,
                    user_options.formats_3d,
                    user_options.linear_rgb,
                    user_options.unordered,
                )
                _convert_to_2d(
                    frame,
                    file_name,
                    user_options.formats_2d,
                    user_options.linear_rgb,
                )
        else:
            if user_options.formats_3d:
                for frame, file_name in frames:
                    _convert_to_3d(
                        frame,
                        file_name,
                        user_options.formats_3d,
                        user_options.linear_rgb,
                        user_options.unordered,
                    )

            if user_options.formats_2d:
                for frame, file_name in frames:
                    _convert_to_2d(
                        frame,
                        file_name,
                        user_options.formats_2d,
                        user_options.linear_rgb,
                    )


if __name__ == "__main__":
    _main()
