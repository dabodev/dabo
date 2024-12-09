import tomllib as toml
from pathlib import Path


def get_version():
    # pyproject.toml is in the directory above this file
    pyproj_file = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproj_file, "rb") as ff:
        config = toml.load(ff)
    return config.get("project", {}).get("version", "0.0.0")


if __name__ == "__main__":
    print(get_version())
