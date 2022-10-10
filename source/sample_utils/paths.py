"""
Get relevant paths for Zivid Samples.

"""

import os
from pathlib import Path


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
