from pathlib import Path

import yaml


def read_configuration(config_name):
    """Load a YAML config searching common locations.

    Search order:
    1. Current working directory
    2. Package configs directory (../configs)
    3. utils directory (alongside this file)
    """

    candidates = [
        Path.cwd() / config_name,
        Path(__file__).resolve().parent.parent / "configs" / config_name,
        Path(__file__).resolve().parent / config_name,
    ]

    for candidate in candidates:
        if candidate.is_file():
            try:
                with open(candidate, "r", encoding="utf-8") as config_file:
                    return yaml.safe_load(config_file) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing YAML in {candidate}: {e}")
            except OSError as e:
                raise OSError(f"Error reading {candidate}: {e}")

    raise FileNotFoundError(
        f"{config_name} file not found in {[str(path) for path in candidates]}"
    )
