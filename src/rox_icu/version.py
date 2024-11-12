from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("rox_icu")
except PackageNotFoundError:  # pragma: no cover
    # Package is not installed, and therefore, version is unknown.
    __version__ = "0.0.0+unknown"
