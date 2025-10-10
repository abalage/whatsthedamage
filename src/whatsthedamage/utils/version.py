from importlib.metadata import version as pkg_version, PackageNotFoundError

def get_version() -> str:
    try:
        return pkg_version("whatsthedamage")
    except PackageNotFoundError:
        return "unknown"