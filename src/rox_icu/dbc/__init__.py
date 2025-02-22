from importlib import resources
from pathlib import Path


def get_dbc() -> Path:
    """get path to dbc file"""

    return Path(resources.files("rox_icu.dbc").joinpath("rox_icu.dbc"))  # type: ignore
