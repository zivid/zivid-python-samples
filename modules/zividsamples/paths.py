"""
Get relevant paths for Zivid Samples.

"""

import os
import sys
from pathlib import Path

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources


def get_sample_data_path() -> Path:
    """Get sample data path for your OS.

    Returns:
        Path: Sample data path

    """
    if os.name == "nt":
        path = Path(os.environ["PROGRAMDATA"]) / "Zivid"
    else:
        path = Path("/usr/share/Zivid/data")
    return path


def get_data_file_path(file_name: str) -> Path:
    if hasattr(resources, "files") and hasattr(resources, "as_file"):
        with resources.as_file(resources.files("zividsamples.data") / file_name) as data_file:
            return Path(data_file)
    else:
        with resources.path("zividsamples.data", file_name) as data_file:
            return Path(data_file)


def get_image_file_path(file_name: str) -> Path:
    if hasattr(resources, "files") and hasattr(resources, "as_file"):
        with resources.as_file(resources.files("zividsamples.images") / file_name) as icon_file:
            return Path(icon_file)
    else:
        with resources.path("zividsamples.images", file_name) as icon_file:
            return Path(icon_file)
